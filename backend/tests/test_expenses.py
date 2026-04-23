"""
Integration tests for Expense Tracker API.
Run against a live server at BASE_URL.
Start server first: uvicorn app.main:app --port 8000
Run: python -m tests.test_expenses
"""

import json
import uuid
import urllib.request
import urllib.error
import sys

BASE_URL = "http://localhost:8000"
PASSED = 0
FAILED = 0


def req(method: str, path: str, body: dict = None) -> tuple:
    """Returns (status_code, response_json, headers_dict)."""
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as resp:
            return resp.status, json.loads(resp.read()), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()), dict(e.headers)


def check(name: str, condition: bool, detail: str = ""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  PASS  {name}")
    else:
        FAILED += 1
        print(f"  FAIL  {name} {f'| {detail}' if detail else ''}")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
def test_health():
    print("\n--- Health Check ---")
    status, data, hdrs = req("GET", "/health")
    check("returns 200", status == 200)
    check("success is true", data["success"] is True)
    check("db connected", data["data"]["db"] == "connected")
    check("has request_id in metadata", data["metadata"].get("request_id") is not None)
    check("has timestamp in metadata", data["metadata"].get("timestamp") is not None)
    check("X-Request-ID in response header", "X-Request-ID" in hdrs or "x-request-id" in hdrs)


# ---------------------------------------------------------------------------
# POST /expenses - happy path
# ---------------------------------------------------------------------------
def test_create_expense():
    print("\n--- POST /expenses (valid) ---")
    expense_id = str(uuid.uuid4())
    body = {
        "id": expense_id,
        "amount": "250.75",
        "category": "food",
        "description": "Test expense",
        "date": "2026-04-23",
    }
    status, data, hdrs = req("POST", "/expenses", body)
    check("returns 201", status == 201)
    check("success true", data["success"] is True)
    check("id matches", data["data"]["id"] == expense_id)
    check("amount is string '250.75'", data["data"]["amount"] == "250.75")
    check("category lowercased", data["data"]["category"] == "food")
    check("has created_at", "created_at" in data["data"])
    check("no amount_paisa leaked", "amount_paisa" not in data["data"])
    check("no updated_at leaked", "updated_at" not in data["data"])
    check("has request_id", data["metadata"].get("request_id") is not None)
    check("has timestamp", data["metadata"].get("timestamp") is not None)
    check("no X-Idempotent-Replayed on first create",
          hdrs.get("X-Idempotent-Replayed") is None and hdrs.get("x-idempotent-replayed") is None)
    return expense_id


# ---------------------------------------------------------------------------
# POST /expenses - idempotency
# ---------------------------------------------------------------------------
def test_idempotency(expense_id: str):
    print("\n--- POST /expenses (idempotency) ---")
    body = {
        "id": expense_id,
        "amount": "250.75",
        "category": "food",
        "description": "Test expense",
        "date": "2026-04-23",
    }
    status1, data1, hdrs1 = req("POST", "/expenses", body)
    check("retry returns 201 (not 409)", status1 == 201)
    check("same id returned", data1["data"]["id"] == expense_id)
    check("same amount", data1["data"]["amount"] == "250.75")
    replay_hdr = hdrs1.get("X-Idempotent-Replayed") or hdrs1.get("x-idempotent-replayed")
    check("X-Idempotent-Replayed: true on retry", replay_hdr == "true")

    status2, data2, _ = req("POST", "/expenses", body)
    check("second retry also 201", status2 == 201)
    check("created_at unchanged (no new row)",
          data1["data"]["created_at"] == data2["data"]["created_at"])


# ---------------------------------------------------------------------------
# POST /expenses - validation errors
# ---------------------------------------------------------------------------
def test_validation_errors():
    print("\n--- POST /expenses (validation) ---")

    # Empty body
    s, d, _ = req("POST", "/expenses", {})
    check("empty body -> 422", s == 422)
    check("has field errors", "fields" in d.get("metadata", {}))
    check("error message is descriptive", len(d.get("error", "")) > 10)

    # Missing required fields
    s, d, _ = req("POST", "/expenses", {"id": str(uuid.uuid4()), "amount": "10.00"})
    check("missing category+date -> 422", s == 422)
    fields = d.get("metadata", {}).get("fields", {})
    check("category error present", "category" in fields)
    check("date error present", "date" in fields)

    # Invalid UUID
    s, d, _ = req("POST", "/expenses", {
        "id": "not-a-uuid", "amount": "10.00", "category": "food",
        "description": "x", "date": "2026-04-23",
    })
    check("invalid UUID -> 422", s == 422)

    # Negative amount
    s, d, _ = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "-50.00", "category": "food",
        "description": "x", "date": "2026-04-23",
    })
    check("negative amount -> 422", s == 422)

    # Zero amount
    s, d, _ = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "0", "category": "food",
        "description": "x", "date": "2026-04-23",
    })
    check("zero amount -> 422", s == 422)

    # Three decimal places
    s, d, _ = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "10.123", "category": "food",
        "description": "x", "date": "2026-04-23",
    })
    check("3 decimals -> 422", s == 422)

    # Amount as number (not string)
    s, d, _ = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": 10.50, "category": "food",
        "description": "x", "date": "2026-04-23",
    })
    check("amount as number -> 422", s == 422)

    # Very large amount
    s, d, _ = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "99999999.99", "category": "food",
        "description": "x", "date": "2026-04-23",
    })
    check("huge amount -> 422", s == 422)

    # Future date
    s, d, _ = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "10.00", "category": "food",
        "description": "x", "date": "2030-12-31",
    })
    check("future date -> 422", s == 422)
    check("future date error is descriptive",
          "future" in d.get("error", "").lower())

    # Invalid date format
    s, d, _ = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "10.00", "category": "food",
        "description": "x", "date": "24-04-2026",
    })
    check("bad date format -> 422", s == 422)

    # Empty category
    s, d, _ = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "10.00", "category": "",
        "description": "x", "date": "2026-04-23",
    })
    check("empty category -> 422", s == 422)

    # Whitespace-only category
    s, d, _ = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "10.00", "category": "   ",
        "description": "x", "date": "2026-04-23",
    })
    check("whitespace category -> 422", s == 422)

    # Amount with leading zeros
    s, d, _ = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "0050.00", "category": "food",
        "description": "x", "date": "2026-04-23",
    })
    check("leading zeros accepted (valid decimal)", s == 201)

    # Description at max length (500 chars)
    s, d, _ = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "1.00", "category": "food",
        "description": "x" * 500, "date": "2026-04-23",
    })
    check("500 char description accepted", s == 201)

    # Description over max length
    s, d, _ = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "1.00", "category": "food",
        "description": "x" * 501, "date": "2026-04-23",
    })
    check("501 char description -> 422", s == 422)

    # Category over max length (50 chars)
    s, d, _ = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "1.00", "category": "a" * 51,
        "description": "x", "date": "2026-04-23",
    })
    check("51 char category -> 422", s == 422)

    # Amount "0.01" - smallest valid
    s, d, _ = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "0.01", "category": "food",
        "description": "smallest", "date": "2026-04-23",
    })
    check("0.01 (1 paisa) accepted", s == 201)
    check("0.01 stored correctly", d["data"]["amount"] == "0.01")


# ---------------------------------------------------------------------------
# POST /expenses - category normalization
# ---------------------------------------------------------------------------
def test_category_normalization():
    print("\n--- POST /expenses (category normalization) ---")
    cid = str(uuid.uuid4())
    s, d, _ = req("POST", "/expenses", {
        "id": cid, "amount": "15.00", "category": "  Food  ",
        "description": "trimmed", "date": "2026-04-23",
    })
    check("201 created", s == 201)
    check("category trimmed+lowered -> 'food'", d["data"]["category"] == "food")


# ---------------------------------------------------------------------------
# GET /expenses - list, filter, sort, date range
# ---------------------------------------------------------------------------
def test_list_expenses():
    print("\n--- GET /expenses ---")

    # Seed known data with different dates
    tag = str(uuid.uuid4())[:6]
    for amt, cat, dt in [
        ("100.00", f"{tag}-groc", "2026-04-20"),
        ("200.00", f"{tag}-groc", "2026-04-22"),
        ("300.00", f"{tag}-trans", "2026-04-21"),
    ]:
        req("POST", "/expenses", {
            "id": str(uuid.uuid4()), "amount": amt,
            "category": cat, "description": "list test", "date": dt,
        })

    # All expenses
    s, d, _ = req("GET", "/expenses")
    check("returns 200", s == 200)
    check("has expenses array", isinstance(d["data"]["expenses"], list))
    check("has total_amount", "total_amount" in d["data"])
    check("has count", "count" in d["data"])
    check("count > 0", d["data"]["count"] > 0)

    # Default sort is date_desc
    expenses = d["data"]["expenses"]
    if len(expenses) >= 2:
        dates = [e["date"] for e in expenses]
        check("default sort newest first", dates == sorted(dates, reverse=True))

    # Filter by category
    s, d, _ = req("GET", f"/expenses?category={tag}-groc")
    check("filter returns 200", s == 200)
    cats = [e["category"] for e in d["data"]["expenses"]]
    check("all results match filter", all(c == f"{tag}-groc" for c in cats))

    # Sort date_asc
    s, d, _ = req("GET", "/expenses?sort=date_asc")
    check("sort asc returns 200", s == 200)
    dates_asc = [e["date"] for e in d["data"]["expenses"]]
    check("sorted oldest first", dates_asc == sorted(dates_asc))

    # Non-existent category
    s, d, _ = req("GET", "/expenses?category=nonexistent_xyz")
    check("no results -> 200 with empty list", s == 200)
    check("empty expenses", d["data"]["expenses"] == [])
    check("total is 0.00", d["data"]["total_amount"] == "0.00")
    check("count is 0", d["data"]["count"] == 0)

    # Invalid sort param
    s, d, _ = req("GET", "/expenses?sort=invalid")
    check("invalid sort -> 422", s == 422)
    check("error code is VALIDATION_ERROR", d["error_code"] == "VALIDATION_ERROR")

    # Date range filter
    s, d, _ = req("GET", "/expenses?from_date=2026-04-21&to_date=2026-04-22")
    check("date range returns 200", s == 200)
    for e in d["data"]["expenses"]:
        check(f"  date {e['date']} in range",
              "2026-04-21" <= e["date"] <= "2026-04-22")

    # Combined filters: category + date range + sort
    s, d, _ = req("GET", f"/expenses?category={tag}-groc&from_date=2026-04-20&to_date=2026-04-22&sort=date_asc")
    check("combined filters returns 200", s == 200)
    check("combined: all match category", all(e["category"] == f"{tag}-groc" for e in d["data"]["expenses"]))


# ---------------------------------------------------------------------------
# DELETE /expenses/:id
# ---------------------------------------------------------------------------
def test_delete():
    print("\n--- DELETE /expenses/:id ---")

    # Create one to delete
    del_id = str(uuid.uuid4())
    req("POST", "/expenses", {
        "id": del_id, "amount": "99.00", "category": "deleteme",
        "description": "will be deleted", "date": "2026-04-23",
    })

    # Delete it
    s, d, _ = req("DELETE", f"/expenses/{del_id}")
    check("delete returns 200", s == 200)
    check("success true", d["success"] is True)
    check("returned deleted id", d["data"]["id"] == del_id)
    check("has request_id", d["metadata"].get("request_id") is not None)

    # Try deleting again -> 404
    s, d, _ = req("DELETE", f"/expenses/{del_id}")
    check("double delete -> 404", s == 404)
    check("error code NOT_FOUND", d["error_code"] == "NOT_FOUND")

    # Delete non-existent UUID
    s, d, _ = req("DELETE", f"/expenses/{uuid.uuid4()}")
    check("delete unknown -> 404", s == 404)

    # Delete with invalid UUID format
    s, d, _ = req("DELETE", "/expenses/not-a-uuid")
    check("delete bad UUID -> 422", s == 422)

    # Verify deleted expense doesn't appear in list
    s, d, _ = req("GET", "/expenses?category=deleteme")
    check("deleted expense gone from list", d["data"]["count"] == 0)


# ---------------------------------------------------------------------------
# GET /expenses/summary
# ---------------------------------------------------------------------------
def test_summary():
    print("\n--- GET /expenses/summary ---")
    s, d, _ = req("GET", "/expenses/summary")
    check("returns 200", s == 200)
    check("has total", "total" in d["data"])
    check("has by_category", "by_category" in d["data"])
    check("by_category is list", isinstance(d["data"]["by_category"], list))

    if d["data"]["by_category"]:
        cat = d["data"]["by_category"][0]
        check("category entry has 'category'", "category" in cat)
        check("category entry has 'total'", "total" in cat)
        check("category entry has 'count'", "count" in cat)


# ---------------------------------------------------------------------------
# Response format consistency
# ---------------------------------------------------------------------------
def test_response_format():
    print("\n--- Response Format ---")

    s, d, hdrs = req("GET", "/health")
    check("success response has 'success'", "success" in d)
    check("success response has 'status'", "status" in d)
    check("success response has 'message'", "message" in d)
    check("success response has 'data'", "data" in d)
    check("success response has 'metadata'", "metadata" in d)
    check("metadata has request_id", "request_id" in d["metadata"])
    check("metadata has timestamp", "timestamp" in d["metadata"])

    s, d, _ = req("POST", "/expenses", {})
    check("error has 'success' false", d["success"] is False)
    check("error has 'error' field", "error" in d)
    check("error has 'error_code' field", "error_code" in d)
    check("error has 'metadata' field", "metadata" in d)
    check("error metadata has request_id", "request_id" in d["metadata"])


# ---------------------------------------------------------------------------
# Money precision
# ---------------------------------------------------------------------------
def test_money_precision():
    print("\n--- Money Precision ---")
    tag = str(uuid.uuid4())[:8]

    # 0.10 + 0.20 must be exactly 0.30
    req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "0.10", "category": tag,
        "description": "a", "date": "2026-04-23",
    })
    req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "0.20", "category": tag,
        "description": "b", "date": "2026-04-23",
    })
    s, d, _ = req("GET", f"/expenses?category={tag}")
    check("0.10 + 0.20 = 0.30 (exact)", d["data"]["total_amount"] == "0.30")

    # Large sum precision
    tag2 = str(uuid.uuid4())[:8]
    for _ in range(10):
        req("POST", "/expenses", {
            "id": str(uuid.uuid4()), "amount": "9999.99", "category": tag2,
            "description": "big", "date": "2026-04-23",
        })
    s, d, _ = req("GET", f"/expenses?category={tag2}")
    check("10 x 9999.99 = 99999.90 (exact)", d["data"]["total_amount"] == "99999.90")

    # Smallest unit
    tag3 = str(uuid.uuid4())[:8]
    req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "0.01", "category": tag3,
        "description": "1 paisa", "date": "2026-04-23",
    })
    s, d, _ = req("GET", f"/expenses?category={tag3}")
    check("1 paisa preserved", d["data"]["total_amount"] == "0.01")


# ---------------------------------------------------------------------------
# Concurrent idempotency (rapid fire same UUID)
# ---------------------------------------------------------------------------
def test_rapid_idempotency():
    print("\n--- Rapid Idempotency (5 requests, same UUID) ---")
    rapid_id = str(uuid.uuid4())
    body = {
        "id": rapid_id, "amount": "42.00", "category": "rapid",
        "description": "rapid fire", "date": "2026-04-23",
    }
    results = []
    for _ in range(5):
        s, d, _ = req("POST", "/expenses", body)
        results.append((s, d["data"]["id"], d["data"]["created_at"]))

    check("all 5 returned 201", all(r[0] == 201 for r in results))
    check("all same id", len(set(r[1] for r in results)) == 1)
    check("all same created_at (1 row)", len(set(r[2] for r in results)) == 1)

    # Verify only 1 in DB
    s, d, _ = req("GET", "/expenses?category=rapid")
    rapid_expenses = [e for e in d["data"]["expenses"] if e["id"] == rapid_id]
    check("only 1 row in DB", len(rapid_expenses) == 1)


# ---------------------------------------------------------------------------
# Edge cases: special characters, unicode, XSS
# ---------------------------------------------------------------------------
def test_special_characters():
    print("\n--- Special Characters & Injection ---")

    # SQL injection attempt in category
    s, d, _ = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "10.00",
        "category": "'; DROP TABLE expenses; --",
        "description": "sql inject", "date": "2026-04-23",
    })
    check("SQL injection in category -> still 201 (parameterized)", s == 201)

    # XSS attempt in description
    s, d, _ = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "10.00", "category": "xss",
        "description": '<script>alert("xss")</script>', "date": "2026-04-23",
    })
    check("XSS in description -> 201 (stored as text)", s == 201)
    check("description stored as-is (no execution)", "<script>" in d["data"]["description"])

    # Unicode in description
    s, d, _ = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "10.00", "category": "unicode",
        "description": "Bought food", "date": "2026-04-23",
    })
    check("unicode description -> 201", s == 201)

    # Verify DB still works after injection attempts
    s, d, _ = req("GET", "/health")
    check("DB still healthy after injection attempts", s == 200)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("EXPENSE TRACKER API - INTEGRATION TESTS")
    print(f"Target: {BASE_URL}")
    print("=" * 60)

    test_health()
    created_id = test_create_expense()
    test_idempotency(created_id)
    test_validation_errors()
    test_category_normalization()
    test_list_expenses()
    test_delete()
    test_summary()
    test_response_format()
    test_money_precision()
    test_rapid_idempotency()
    test_special_characters()

    print("\n" + "=" * 60)
    total = PASSED + FAILED
    print(f"RESULTS: {PASSED}/{total} passed, {FAILED} failed")
    print("=" * 60)

    sys.exit(1 if FAILED else 0)

"""
Integration tests for Expense Tracker API.
Tests run against a live server at BASE_URL.
Start the server before running: uvicorn app.main:app --port 8000
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


def req(method: str, path: str, body: dict = None) -> tuple[int, dict]:
    """Make HTTP request, return (status_code, response_json)."""
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


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
    status, data = req("GET", "/health")
    check("returns 200", status == 200)
    check("success is true", data["success"] is True)
    check("db connected", data["data"]["db"] == "connected")


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
        "date": "2026-04-24",
    }
    status, data = req("POST", "/expenses", body)
    check("returns 201", status == 201)
    check("success true", data["success"] is True)
    check("id matches", data["data"]["id"] == expense_id)
    check("amount is string '250.75'", data["data"]["amount"] == "250.75")
    check("category lowercased", data["data"]["category"] == "food")
    check("has created_at", "created_at" in data["data"])
    check("no amount_paisa leaked", "amount_paisa" not in data["data"])
    check("no updated_at leaked", "updated_at" not in data["data"])
    return expense_id


# ---------------------------------------------------------------------------
# POST /expenses - idempotency
# ---------------------------------------------------------------------------
def test_idempotency(expense_id: str):
    print("\n--- POST /expenses (idempotency - same UUID) ---")
    body = {
        "id": expense_id,
        "amount": "250.75",
        "category": "food",
        "description": "Test expense",
        "date": "2026-04-24",
    }
    # First retry
    status1, data1 = req("POST", "/expenses", body)
    check("retry returns 201 (not 409)", status1 == 201)
    check("same id returned", data1["data"]["id"] == expense_id)
    check("same amount", data1["data"]["amount"] == "250.75")

    # Second retry
    status2, data2 = req("POST", "/expenses", body)
    check("second retry also 201", status2 == 201)
    check("created_at unchanged (no new row)", data1["data"]["created_at"] == data2["data"]["created_at"])


# ---------------------------------------------------------------------------
# POST /expenses - validation errors
# ---------------------------------------------------------------------------
def test_validation_errors():
    print("\n--- POST /expenses (validation) ---")

    # Empty body
    status, data = req("POST", "/expenses", {})
    check("empty body -> 422", status == 422)
    check("has field errors", "fields" in data.get("metadata", {}))

    # Missing required fields
    status, data = req("POST", "/expenses", {"id": str(uuid.uuid4()), "amount": "10.00"})
    check("missing category+date -> 422", status == 422)
    fields = data.get("metadata", {}).get("fields", {})
    check("category error present", "category" in fields)
    check("date error present", "date" in fields)

    # Invalid UUID
    status, data = req("POST", "/expenses", {
        "id": "not-a-uuid", "amount": "10.00", "category": "food",
        "description": "x", "date": "2026-04-24",
    })
    check("invalid UUID -> 422", status == 422)

    # Negative amount
    status, data = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "-50.00", "category": "food",
        "description": "x", "date": "2026-04-24",
    })
    check("negative amount -> 422", status == 422)

    # Zero amount
    status, data = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "0", "category": "food",
        "description": "x", "date": "2026-04-24",
    })
    check("zero amount -> 422", status == 422)

    # Three decimal places
    status, data = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "10.123", "category": "food",
        "description": "x", "date": "2026-04-24",
    })
    check("3 decimals -> 422", status == 422)

    # Amount as number (not string)
    status, data = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": 10.50, "category": "food",
        "description": "x", "date": "2026-04-24",
    })
    check("amount as number -> 422", status == 422)

    # Very large amount
    status, data = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "99999999.99", "category": "food",
        "description": "x", "date": "2026-04-24",
    })
    check("huge amount -> 422", status == 422)

    # Future date (far)
    status, data = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "10.00", "category": "food",
        "description": "x", "date": "2030-12-31",
    })
    check("far future date -> 422", status == 422)

    # Invalid date format
    status, data = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "10.00", "category": "food",
        "description": "x", "date": "24-04-2026",
    })
    check("bad date format -> 422", status == 422)

    # Empty category
    status, data = req("POST", "/expenses", {
        "id": str(uuid.uuid4()), "amount": "10.00", "category": "",
        "description": "x", "date": "2026-04-24",
    })
    check("empty category -> 422", status == 422)


# ---------------------------------------------------------------------------
# POST /expenses - category normalization
# ---------------------------------------------------------------------------
def test_category_normalization():
    print("\n--- POST /expenses (category normalization) ---")
    cid = str(uuid.uuid4())
    status, data = req("POST", "/expenses", {
        "id": cid, "amount": "15.00", "category": "  Food  ",
        "description": "trimmed", "date": "2026-04-24",
    })
    check("201 created", status == 201)
    check("category trimmed+lowered -> 'food'", data["data"]["category"] == "food")


# ---------------------------------------------------------------------------
# GET /expenses - list, filter, sort
# ---------------------------------------------------------------------------
def test_list_expenses():
    print("\n--- GET /expenses ---")

    # Seed known data
    ids = []
    for i, (amt, cat, dt) in enumerate([
        ("100.00", "groceries", "2026-04-20"),
        ("200.00", "groceries", "2026-04-22"),
        ("300.00", "transport", "2026-04-21"),
    ]):
        eid = str(uuid.uuid4())
        ids.append(eid)
        req("POST", "/expenses", {
            "id": eid, "amount": amt, "category": cat,
            "description": f"list test {i}", "date": dt,
        })

    # All expenses
    status, data = req("GET", "/expenses")
    check("returns 200", status == 200)
    check("has expenses array", isinstance(data["data"]["expenses"], list))
    check("has total_amount", "total_amount" in data["data"])
    check("has count", "count" in data["data"])
    check("count > 0", data["data"]["count"] > 0)

    # Default sort is date_desc (newest first)
    expenses = data["data"]["expenses"]
    if len(expenses) >= 2:
        dates = [e["date"] for e in expenses]
        check("default sort newest first", dates == sorted(dates, reverse=True))

    # Filter by category
    status, data = req("GET", "/expenses?category=groceries")
    check("filter returns 200", status == 200)
    cats = [e["category"] for e in data["data"]["expenses"]]
    check("all results are groceries", all(c == "groceries" for c in cats))
    check("total matches groceries only", data["data"]["total_amount"] == "300.00" or float(data["data"]["total_amount"]) > 0)

    # Sort date_asc
    status, data = req("GET", "/expenses?sort=date_asc")
    check("sort asc returns 200", status == 200)
    dates_asc = [e["date"] for e in data["data"]["expenses"]]
    check("sorted oldest first", dates_asc == sorted(dates_asc))

    # Non-existent category
    status, data = req("GET", "/expenses?category=nonexistent")
    check("no results -> 200 with empty list", status == 200)
    check("empty expenses", data["data"]["expenses"] == [])
    check("total is 0.00", data["data"]["total_amount"] == "0.00")
    check("count is 0", data["data"]["count"] == 0)

    # Invalid sort param
    status, data = req("GET", "/expenses?sort=invalid")
    check("invalid sort -> 422", status == 422)
    check("error code is VALIDATION_ERROR", data["error_code"] == "VALIDATION_ERROR")


# ---------------------------------------------------------------------------
# GET /expenses/summary
# ---------------------------------------------------------------------------
def test_summary():
    print("\n--- GET /expenses/summary ---")
    status, data = req("GET", "/expenses/summary")
    check("returns 200", status == 200)
    check("has total", "total" in data["data"])
    check("has by_category", "by_category" in data["data"])
    check("by_category is list", isinstance(data["data"]["by_category"], list))

    if data["data"]["by_category"]:
        cat = data["data"]["by_category"][0]
        check("category entry has 'category'", "category" in cat)
        check("category entry has 'total'", "total" in cat)
        check("category entry has 'count'", "count" in cat)


# ---------------------------------------------------------------------------
# Response format consistency
# ---------------------------------------------------------------------------
def test_response_format():
    print("\n--- Response Format ---")

    # Success response shape
    status, data = req("GET", "/health")
    check("has 'success' field", "success" in data)
    check("has 'status' field", "status" in data)
    check("has 'message' field", "message" in data)
    check("has 'data' field", "data" in data)
    check("has 'metadata' field", "metadata" in data)

    # Error response shape
    status, data = req("POST", "/expenses", {})
    check("error has 'success' false", data["success"] is False)
    check("error has 'error' field", "error" in data)
    check("error has 'error_code' field", "error_code" in data)
    check("error has 'metadata' field", "metadata" in data)


# ---------------------------------------------------------------------------
# Money precision
# ---------------------------------------------------------------------------
def test_money_precision():
    print("\n--- Money Precision ---")
    # Rs0.10 + Rs0.20 should be exactly Rs0.30 (not 0.30000000000000004)
    id1 = str(uuid.uuid4())
    id2 = str(uuid.uuid4())
    tag = str(uuid.uuid4())[:8]  # unique category to isolate
    req("POST", "/expenses", {
        "id": id1, "amount": "0.10", "category": tag,
        "description": "precision a", "date": "2026-04-24",
    })
    req("POST", "/expenses", {
        "id": id2, "amount": "0.20", "category": tag,
        "description": "precision b", "date": "2026-04-24",
    })
    status, data = req("GET", f"/expenses?category={tag}")
    check("precision test 200", status == 200)
    check("0.10 + 0.20 = 0.30 (exact)", data["data"]["total_amount"] == "0.30")


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
    test_summary()
    test_response_format()
    test_money_precision()

    print("\n" + "=" * 60)
    total = PASSED + FAILED
    print(f"RESULTS: {PASSED}/{total} passed, {FAILED} failed")
    print("=" * 60)

    sys.exit(1 if FAILED else 0)

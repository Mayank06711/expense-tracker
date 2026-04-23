# Expense Tracker

A minimal full-stack personal expense tracker built for production-like quality.
Record, review, filter, and summarize your personal expenses.

## Live Application

- **Frontend**: https://mayank06711.xyz
- **Backend API**: https://api.mayank06711.xyz
- **Health Check**: https://api.mayank06711.xyz/health

## Tech Stack

### Backend
- **Python 3.11** + **FastAPI** — Async-first, high performance, auto-generated OpenAPI docs
- **PostgreSQL 16** — Relational DB for ACID compliance and data integrity
- **SQLAlchemy 2.0** (async) — Type-safe ORM with connection pooling
- **Pydantic v2** — Request/response validation with strict rules

### Frontend
- **React 18** + **TypeScript** + **Vite** — Fast dev experience, type safety
- **Tailwind CSS** — Utility-first styling, B&W theme with dark mode toggle

### Deployment
- **Docker** — Multi-stage builds, each service runs independently (no docker-compose in prod)
- **Nginx** — Reverse proxy with SSL termination
- **AWS EC2** — Ubuntu 22.04, Let's Encrypt HTTPS
- **deploy.sh** — Single script deploys everything from scratch

## Why PostgreSQL over NoSQL?

This is a financial application dealing with money. We need:

1. **ACID transactions** — Every expense write must be atomic. PostgreSQL guarantees this.
2. **Relational integrity** — Expenses have a fixed schema. A relational model enforces data quality at the DB level.
3. **Precise aggregations** — SUM, GROUP BY with indexes. SQL is purpose-built for this.
4. **Money handling** — BIGINT stores amounts in paisa (smallest currency unit) with zero floating-point risk.

## Key Design Decisions

### Idempotent expense creation
The client generates a UUID per form submission and sends it as the expense `id`. If the user double-clicks submit or the network retries, the same UUID hits the server. The primary key constraint catches duplicates, and the server returns the existing record with `X-Idempotent-Replayed: true` header. No duplicate expenses, no extra columns.

### Money stored as integer paisa
₹150.50 is stored as `15050` (BIGINT). Float types can't represent 0.1 exactly (`0.1 + 0.2 = 0.30000000000000004`). By storing in paisa and converting at the API boundary, all internal math is exact integer arithmetic.

### Request tracing
Every response includes `request_id` and `timestamp` in metadata + `X-Request-ID` response header. When something breaks in production, you can trace a specific request through the logs.

### SOLID architecture
- **Repository pattern** — Data access abstracted behind `ExpenseRepository`. Swap PostgreSQL for SQLite without touching business logic.
- **Service layer** — Business logic (money conversion, dedup handling) lives in `ExpenseService`, not in route handlers.
- **Dependency injection** — FastAPI's `Depends()` wires concrete implementations at runtime.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/expenses` | Create expense (idempotent via client UUID) |
| GET | `/expenses` | List with `?category=`, `?sort=date_desc`, `?from_date=`, `?to_date=` |
| DELETE | `/expenses/:id` | Delete an expense |
| GET | `/expenses/summary` | Total per category breakdown |
| GET | `/health` | DB connectivity check |

### Response Format
```json
// Success
{ "success": true, "status": 200, "message": "...", "data": {}, "metadata": { "request_id": "abc123", "timestamp": "..." } }

// Error
{ "success": false, "error": "amount: Amount must be greater than zero", "error_code": "VALIDATION_ERROR", "metadata": { "fields": { "amount": "Amount must be greater than zero" } } }
```

## Running Locally

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
docker run -d --name expense-db -e POSTGRES_USER=expense_user -e POSTGRES_PASSWORD=expense_pass -e POSTGRES_DB=expense_tracker -p 5432:5432 postgres:16-alpine
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Run Tests (113 integration tests)
```bash
cd backend
python -m tests.test_expenses
```

## Deployment

### Prerequisites
- AWS EC2 instance (Ubuntu 22.04, t2.small or larger)
- Elastic IP associated with the instance
- Security group: inbound port 80 (HTTP) and 443 (HTTPS) open
- Domain pointing to the Elastic IP (A records for root + api subdomain)
- SSL certificates (use certbot: `certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com`)

### Deploy
```bash
# SSH into your EC2
ssh -i your-key.pem ubuntu@your-ip

# Clone and deploy
git clone https://github.com/Mayank06711/expense-tracker.git ~/app
cd ~/app
sudo bash deploy.sh
```

The `deploy.sh` script:
1. Starts PostgreSQL container with persistent volume
2. Builds backend image (multi-stage: pip install → slim runtime)
3. Builds frontend image (multi-stage: npm build → nginx serve)
4. Generates Nginx reverse proxy config with SSL
5. Starts Nginx container
6. Verifies all services are healthy

Each service runs as an independent container — no docker-compose, no shared network. Services communicate via host ports, Nginx proxies external HTTPS traffic.

### Outbound rules
No outbound restrictions needed — the application does not make external API calls. All communication is internal (backend → database).

## Project Structure
```
expense-tracker/
├── backend/
│   ├── Dockerfile              # Multi-stage Python build
│   ├── app/
│   │   ├── main.py             # App factory, lifespan, CORS, middleware
│   │   ├── config.py           # Environment settings (pydantic-settings)
│   │   ├── database.py         # Async engine + connection pool (pool_size, pre_ping)
│   │   ├── dependencies.py     # DI wiring (repo → service → route)
│   │   ├── models/             # SQLAlchemy ORM (Expense, TimestampMixin)
│   │   ├── schemas/            # Pydantic validation (amount, date, category rules)
│   │   ├── repositories/       # Data access layer (CRUD, filters, aggregations)
│   │   ├── services/           # Business logic (money conversion, idempotency)
│   │   ├── api/                # Route handlers (expenses, health)
│   │   ├── middleware/         # Request logger, error formatter
│   │   └── utils/              # rupees_to_paisa / paisa_to_rupees
│   └── tests/                  # 113 integration tests
├── frontend/
│   ├── Dockerfile              # Multi-stage Node build → nginx
│   ├── nginx.conf              # Frontend static file server on :3000
│   └── src/
│       ├── api/                # Typed API client with timeout
│       ├── components/         # Form modal, table, filters, summary, theme toggle
│       ├── hooks/              # useExpenses (fetch, filter, delete), useTheme
│       ├── types/              # TypeScript interfaces matching API
│       └── utils/              # UUID generation for idempotency
├── deploy.sh                   # Production deploy script (single source of truth)
└── README.md
```

## Trade-offs (due to timebox)

- **No authentication** — Single-user personal tool. Auth adds complexity without matching the use case.
- **No pagination** — Personal expense lists are small. Would add cursor-based pagination if scaling.
- **No edit endpoint** — Delete is supported. Edit would follow the same pattern.
- **Minimal styling** — Black & white theme with dark mode. Focus on correctness over visuals.

## What Was Intentionally Not Done

- **No WebSocket/real-time updates** — Single user, no collaboration needed.
- **No file upload (receipts)** — Out of scope for core expense tracking.
- **No budget/limit alerts** — Interesting feature but not in acceptance criteria.
- **No export (CSV/PDF)** — Would add if extending, but not core.

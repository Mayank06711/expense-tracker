# Expense Tracker

A minimal full-stack personal expense tracker built for production-like quality.
Record, review, filter, and summarize your personal expenses.

## Tech Stack

### Backend
- **Python 3.11** + **FastAPI** — Async-first, high performance, auto-generated OpenAPI docs
- **PostgreSQL** — Relational DB for ACID compliance and data integrity
- **SQLAlchemy 2.0** (async) — Type-safe ORM with connection pooling
- **Pydantic v2** — Request/response validation

### Frontend
- **React 18** + **TypeScript** + **Vite** — Fast dev experience, type safety
- **Tailwind CSS** — Utility-first styling, minimal custom CSS

### Deployment
- **Docker Compose** — Consistent environments across dev and prod
- **Nginx** — Reverse proxy with SSL termination
- **AWS EC2** — Hosted with HTTPS via Let's Encrypt

## Why PostgreSQL over NoSQL?

This is a financial application dealing with money. We need:

1. **ACID transactions** — Every expense write must be atomic. No partial writes, no phantom reads. PostgreSQL guarantees this. Document stores like MongoDB have weaker consistency by default.

2. **Relational integrity** — Expenses have a fixed, well-defined schema (amount, category, date). This isn't a flexible-schema problem. A relational model enforces data quality at the DB level.

3. **Precise aggregations** — SUM, GROUP BY, filtering with indexes. SQL is purpose-built for this. Running aggregation pipelines in Mongo for what's a simple `SELECT SUM(amount) WHERE category = 'food'` is unnecessary complexity.

4. **Money handling** — PostgreSQL's BIGINT stores amounts in paisa (smallest currency unit) with zero floating-point risk. Integer arithmetic is exact.

## Key Design Decisions

### Idempotent expense creation
The client generates a UUID per form submission and sends it as the expense `id`. If the user double-clicks submit or the network retries, the same UUID hits the server. The primary key constraint catches duplicates, and the server returns the existing record. No duplicate expenses, no extra idempotency columns.

### Money stored as integer paisa
₹150.50 is stored as `15050` (BIGINT). Float types can't represent 0.1 exactly (`0.1 + 0.2 = 0.30000000000000004`). By storing in paisa and converting at the API boundary, all internal math is exact integer arithmetic.

### SOLID architecture
- **Repository pattern** — Data access is abstracted behind `ExpenseRepository`. Swap PostgreSQL for SQLite without touching business logic.
- **Service layer** — Business logic (money conversion, dedup handling) lives in `ExpenseService`, not in route handlers.
- **Dependency injection** — FastAPI's `Depends()` wires concrete implementations at runtime. Services depend on abstractions, not concrete DB code.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/expenses` | Create an expense (idempotent via client UUID) |
| GET | `/expenses` | List expenses with optional `?category=` filter and `?sort=date_desc` |
| GET | `/expenses/summary` | Total per category breakdown |
| GET | `/health` | DB connectivity check |

## Running Locally

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Start PostgreSQL (Docker)
docker run -d --name expense-db -e POSTGRES_USER=expense_user -e POSTGRES_PASSWORD=expense_pass -e POSTGRES_DB=expense_tracker -p 5433:5432 postgres:16-alpine
# Run server
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Project Structure
```
expense-tracker/
├── backend/
│   ├── app/
│   │   ├── main.py              # App factory, lifespan, CORS
│   │   ├── config.py            # Environment settings
│   │   ├── database.py          # Async engine + connection pool
│   │   ├── dependencies.py      # DI wiring
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic validation
│   │   ├── repositories/        # Data access layer
│   │   ├── services/            # Business logic
│   │   ├── api/                 # Route handlers
│   │   ├── middleware/          # Error formatting
│   │   └── utils/               # Money conversion helpers
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                 # API client with timeout
│   │   ├── components/          # React components
│   │   ├── hooks/               # Custom hooks
│   │   ├── types/               # TypeScript interfaces
│   │   └── utils/               # UUID generation
│   └── package.json
└── docker-compose.yml
```

## Trade-offs (due to timebox)

- **No authentication** — Single-user personal tool. Auth would add complexity without matching the use case.
- **No pagination** — Personal expense lists are small. Would add if scaling to thousands of records.
- **No edit/delete** — Not in acceptance criteria. The data model supports it; just no endpoints yet.
- **Minimal styling** — Black & white theme. Focus was on correctness and data handling, not visual design.

## Live Application

- **Frontend**: https://mayank06711.xyz
- **Backend API**: https://api.mayank06711.xyz

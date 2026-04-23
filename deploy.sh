#!/bin/bash
set -e

# Production deploy script — each service runs as independent container
# Nginx reverse proxy is pre-configured on the host (EC2)

APP_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Expense Tracker Deploy ==="

# 1. Database
if ! docker ps --format '{{.Names}}' | grep -q '^expense-db$'; then
    echo "Starting PostgreSQL..."
    docker run -d \
        --name expense-db \
        --restart unless-stopped \
        -e POSTGRES_USER=expense_user \
        -e POSTGRES_PASSWORD=expense_pass \
        -e POSTGRES_DB=expense_tracker \
        -p 127.0.0.1:5432:5432 \
        -v expense_pgdata:/var/lib/postgresql/data \
        postgres:16-alpine
    echo "Waiting for DB to be ready..."
    sleep 5
else
    echo "PostgreSQL already running"
fi

# 2. Backend
echo "Building backend..."
docker build -t expense-backend "$APP_DIR/backend"

echo "Starting backend..."
docker rm -f expense-backend 2>/dev/null || true
docker run -d \
    --name expense-backend \
    --restart unless-stopped \
    -e DATABASE_URL=postgresql+asyncpg://expense_user:expense_pass@host.docker.internal:5432/expense_tracker \
    -e APP_ENV=production \
    -e ALLOWED_ORIGINS=https://mayank06711.xyz,https://www.mayank06711.xyz \
    -p 127.0.0.1:8000:8000 \
    expense-backend

# 3. Frontend
echo "Building frontend..."
docker build -t expense-frontend \
    --build-arg VITE_API_URL=https://api.mayank06711.xyz \
    "$APP_DIR/frontend"

echo "Starting frontend..."
docker rm -f expense-frontend 2>/dev/null || true
docker run -d \
    --name expense-frontend \
    --restart unless-stopped \
    -p 127.0.0.1:3000:3000 \
    expense-frontend

echo ""
echo "=== Deploy complete ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "Frontend: http://localhost:3000 (proxied via Nginx -> https://mayank06711.xyz)"
echo "Backend:  http://localhost:8000 (proxied via Nginx -> https://api.mayank06711.xyz)"

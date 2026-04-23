#!/bin/bash
set -e

# Production deploy script — each service runs as independent container
# Nginx reverse proxy with SSL is pre-configured on the host
# Usage: Clone repo, then run ./deploy.sh from the repo root

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
DB_HOST="172.17.0.1"  # Docker bridge gateway (Linux). Use host.docker.internal on Mac/Windows.

echo "=== Expense Tracker Deploy ==="
echo "App directory: $APP_DIR"

# 1. Database — independent container with persistent volume
if ! docker ps --format '{{.Names}}' | grep -q '^expense-db$'; then
    echo "[1/4] Starting PostgreSQL..."
    docker run -d \
        --name expense-db \
        --restart unless-stopped \
        -e POSTGRES_USER=expense_user \
        -e POSTGRES_PASSWORD=expense_pass \
        -e POSTGRES_DB=expense_tracker \
        -p 127.0.0.1:5432:5432 \
        -v expense_pgdata:/var/lib/postgresql/data \
        postgres:16-alpine
    echo "Waiting for DB to initialize..."
    sleep 5
else
    echo "[1/4] PostgreSQL already running"
fi

# 2. Backend — multi-stage build, connects to DB via host network
echo "[2/4] Building backend..."
docker build -t expense-backend "$APP_DIR/backend"
docker rm -f expense-backend 2>/dev/null || true
docker run -d \
    --name expense-backend \
    --restart unless-stopped \
    -e DATABASE_URL="postgresql+asyncpg://expense_user:expense_pass@${DB_HOST}:5432/expense_tracker" \
    -e APP_ENV=production \
    -e ALLOWED_ORIGINS="https://mayank06711.xyz,https://www.mayank06711.xyz,http://mayank06711.xyz" \
    -p 127.0.0.1:8000:8000 \
    expense-backend
echo "Backend started on :8000"

# 3. Frontend — multi-stage build (Node build -> nginx serve)
echo "[3/4] Building frontend..."
docker build -t expense-frontend \
    --build-arg VITE_API_URL=https://api.mayank06711.xyz \
    "$APP_DIR/frontend"
docker rm -f expense-frontend 2>/dev/null || true
docker run -d \
    --name expense-frontend \
    --restart unless-stopped \
    -p 127.0.0.1:3000:3000 \
    expense-frontend
echo "Frontend started on :3000"

# 4. Restart Nginx reverse proxy (picks up backend/frontend on localhost ports)
echo "[4/4] Restarting Nginx..."
docker rm -f nginx-proxy 2>/dev/null || true
docker run -d \
    --name nginx-proxy \
    --restart unless-stopped \
    -p 80:80 -p 443:443 \
    -v /home/ubuntu/deploy/nginx/nginx.conf:/etc/nginx/nginx.conf:ro \
    -v /home/ubuntu/deploy/nginx/conf.d:/etc/nginx/conf.d:ro \
    -v /home/ubuntu/deploy/nginx/ssl:/etc/nginx/ssl:ro \
    -v /var/www/certbot:/var/www/certbot:ro \
    --add-host=host.docker.internal:host-gateway \
    nginx:alpine
echo "Nginx proxy started on :80/:443"

echo ""
echo "=== Deploy complete ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "Frontend: https://mayank06711.xyz"
echo "API:      https://api.mayank06711.xyz"
echo "Health:   https://api.mayank06711.xyz/health"

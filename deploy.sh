#!/bin/bash
set -e

# Production deploy script — each service runs as its own container
# Nginx config is generated here (single source of truth)
# Usage: git clone <repo> && cd expense-tracker && sudo bash deploy.sh

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
DB_HOST="172.17.0.1"
DOMAIN="mayank06711.xyz"
API_DOMAIN="api.mayank06711.xyz"
SSL_DIR="/home/ubuntu/deploy/nginx/ssl"
CERTBOT_DIR="/var/www/certbot"

echo "=== Expense Tracker Deploy ==="
echo "App directory: $APP_DIR"

# ---------------------------------------------------------------
# 1. Database
# ---------------------------------------------------------------
if ! docker ps --format '{{.Names}}' | grep -q '^expense-db$'; then
    echo "[1/5] Starting PostgreSQL..."
    docker run -d \
        --name expense-db \
        --restart unless-stopped \
        -e POSTGRES_USER=expense_user \
        -e POSTGRES_PASSWORD=expense_pass \
        -e POSTGRES_DB=expense_tracker \
        -p 5432:5432 \
        -v expense_pgdata:/var/lib/postgresql/data \
        postgres:16-alpine
    sleep 5
else
    echo "[1/5] PostgreSQL already running"
fi

# ---------------------------------------------------------------
# 2. Backend
# ---------------------------------------------------------------
echo "[2/5] Building backend..."
docker build -t expense-backend "$APP_DIR/backend"
docker rm -f expense-backend 2>/dev/null || true
docker run -d \
    --name expense-backend \
    --restart unless-stopped \
    -e DATABASE_URL="postgresql+asyncpg://expense_user:expense_pass@${DB_HOST}:5432/expense_tracker" \
    -e APP_ENV=production \
    -e ALLOWED_ORIGINS="https://${DOMAIN},https://www.${DOMAIN},http://${DOMAIN}" \
    -p 8000:8000 \
    expense-backend
echo "Backend on :8000"

# ---------------------------------------------------------------
# 3. Frontend
# ---------------------------------------------------------------
echo "[3/5] Building frontend..."
docker build -t expense-frontend \
    --build-arg VITE_API_URL="https://${API_DOMAIN}" \
    "$APP_DIR/frontend"
docker rm -f expense-frontend 2>/dev/null || true
docker run -d \
    --name expense-frontend \
    --restart unless-stopped \
    -p 3000:3000 \
    expense-frontend
echo "Frontend on :3000"

# ---------------------------------------------------------------
# 4. Generate Nginx config (no CORS here — FastAPI handles it)
# ---------------------------------------------------------------
echo "[4/5] Writing Nginx config..."
mkdir -p /home/ubuntu/deploy/nginx/conf.d

cat > /home/ubuntu/deploy/nginx/conf.d/default.conf << NGINXEOF
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN} ${API_DOMAIN};
    location /.well-known/acme-challenge/ { root ${CERTBOT_DIR}; }
    location / { return 301 https://\$host\$request_uri; }
}

server {
    listen 443 ssl;
    server_name ${DOMAIN} www.${DOMAIN};
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://host.docker.internal:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

server {
    listen 443 ssl;
    server_name ${API_DOMAIN};
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://host.docker.internal:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

server {
    listen 80 default_server;
    server_name _;
    location /health { return 200 'OK'; add_header Content-Type text/plain; }
    location / { return 301 https://${DOMAIN}\$request_uri; }
}
NGINXEOF

# ---------------------------------------------------------------
# 5. Nginx reverse proxy
# ---------------------------------------------------------------
echo "[5/5] Starting Nginx..."
docker rm -f nginx-proxy 2>/dev/null || true
docker run -d \
    --name nginx-proxy \
    --restart unless-stopped \
    -p 80:80 -p 443:443 \
    -v /home/ubuntu/deploy/nginx/nginx.conf:/etc/nginx/nginx.conf:ro \
    -v /home/ubuntu/deploy/nginx/conf.d:/etc/nginx/conf.d:ro \
    -v ${SSL_DIR}:/etc/nginx/ssl:ro \
    -v ${CERTBOT_DIR}:/var/www/certbot:ro \
    --add-host=host.docker.internal:host-gateway \
    nginx:alpine

sleep 2

echo ""
echo "=== Deploy complete ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "Verifying..."
echo "Health: $(curl -sk https://localhost/health -H "Host: ${API_DOMAIN}" 2>/dev/null | head -c 80)"
echo "Frontend: $(curl -sk https://localhost/ -H "Host: ${DOMAIN}" 2>/dev/null | head -c 30)"
echo ""
echo "Live URLs:"
echo "  Frontend: https://${DOMAIN}"
echo "  API:      https://${API_DOMAIN}"
echo "  Health:   https://${API_DOMAIN}/health"

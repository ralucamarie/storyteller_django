#!/usr/bin/env bash
# One-time backend setup for Ubuntu 20.04+ (installs Python 3.12, Postgres, gunicorn, nginx).
# Run on the VPS as ubuntu:
#   GEMINI_API_KEY='...' bash vm-setup.sh
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/ralucamarie/storyteller_django.git}"
APP_ROOT="/home/ubuntu/storyteller"
PY_ROOT="/opt/python312"
DB_NAME="storyteller"
DB_USER="storyteller"
DOMAIN="${API_DOMAIN:-api.povesticupesti.ro}"
FRONTEND_URL="${FRONTEND_URL:-https://povesticupesti.ro}"

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  echo "WARN: GEMINI_API_KEY not set — AI assist disabled until added to .env"
  GEMINI_API_KEY=""
fi

echo "==> swap (helps pip / low-RAM VMs)"
if ! swapon --show | grep -q '/swapfile'; then
  sudo fallocate -l 1G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=1024
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

echo "==> firewall (iptables 80/443)"
sudo iptables -C INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || \
  sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -C INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || \
  sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y iptables-persistent >/dev/null 2>&1 || true
sudo netfilter-persistent save 2>/dev/null || true

echo "==> system packages"
sudo DEBIAN_FRONTEND=noninteractive apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  postgresql nginx git certbot python3-certbot-nginx \
  libpq-dev build-essential curl ca-certificates

echo "==> Python 3.12 (prebuilt standalone)"
if [[ ! -x "${PY_ROOT}/bin/python3.12" ]]; then
  PY_TAR="cpython-3.12.8+20241206-x86_64-unknown-linux-gnu-install_only.tar.gz"
  PY_URL="https://github.com/astral-sh/python-build-standalone/releases/download/20241206/${PY_TAR}"
  tmpdir="$(mktemp -d)"
  curl -fsSL "${PY_URL}" -o "${tmpdir}/${PY_TAR}"
  sudo mkdir -p "${PY_ROOT}"
  sudo tar -xzf "${tmpdir}/${PY_TAR}" -C "${PY_ROOT}" --strip-components=1
  rm -rf "${tmpdir}"
fi
"${PY_ROOT}/bin/python3.12" --version

echo "==> PostgreSQL database"
DB_PASS="$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)"
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1; then
  sudo -u postgres psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASS}';"
else
  sudo -u postgres psql -c "ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASS}';"
fi
if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
  sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"
fi
sudo -u postgres psql -d "${DB_NAME}" -c "GRANT ALL ON SCHEMA public TO ${DB_USER};"

echo "==> application code"
if [[ ! -d "${APP_ROOT}/.git" ]]; then
  git clone "${REPO_URL}" "${APP_ROOT}"
fi
cd "${APP_ROOT}"
git pull origin main

if [[ ! -x /home/ubuntu/storyteller/venv/bin/python ]]; then
  "${PY_ROOT}/bin/python3.12" -m venv /home/ubuntu/storyteller/venv
fi
source /home/ubuntu/storyteller/venv/bin/activate
pip install --upgrade pip wheel
pip install -r requirements.txt

SECRET_KEY="$("${PY_ROOT}/bin/python3.12" -c 'import secrets; print(secrets.token_urlsafe(50))')"
cat > "${APP_ROOT}/.env" <<ENV
DJANGO_SECRET_KEY=${SECRET_KEY}
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=${DOMAIN},158.101.174.104

DATABASE_URL=postgres://${DB_USER}:${DB_PASS}@localhost:5432/${DB_NAME}
DATABASE_SSL_REQUIRE=False

CORS_ALLOWED_ORIGINS=${FRONTEND_URL},https://www.povesticupesti.ro
CSRF_TRUSTED_ORIGINS=${FRONTEND_URL},https://www.povesticupesti.ro
FRONTEND_URL=${FRONTEND_URL}

GEMINI_API_KEY=${GEMINI_API_KEY}
GEMINI_MODEL=gemini-2.5-flash
ENV
chmod 600 "${APP_ROOT}/.env"

cd "${APP_ROOT}"
python manage.py migrate --noinput
python manage.py collectstatic --noinput

if ! python manage.py shell -c "from django.contrib.auth import get_user_model; exit(0 if get_user_model().objects.filter(is_superuser=True).exists() else 1)"; then
  ADMIN_PASS="$(openssl rand -base64 16 | tr -d '/+=' | head -c 16)"
  python manage.py shell <<PY
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser(
    email="admin@povesticupesti.ro",
    password="${ADMIN_PASS}",
    name="Admin",
    surname="User",
    author_name="admin",
)
PY
  echo "ADMIN_EMAIL=admin@povesticupesti.ro"
  echo "ADMIN_PASSWORD=${ADMIN_PASS}"
fi

echo "==> gunicorn systemd"
sudo tee /etc/systemd/system/gunicorn.service >/dev/null <<'UNIT'
[Unit]
Description=gunicorn daemon for Storyteller (Django)
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/storyteller
ExecStart=/home/ubuntu/storyteller/venv/bin/gunicorn \
    --workers 2 \
    --timeout 60 \
    --bind 127.0.0.1:8001 \
    storyteller.wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

echo "==> nginx"
sudo tee /etc/nginx/sites-available/storyteller >/dev/null <<NGINX
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    client_max_body_size 25M;

    location /static/ {
        alias /home/ubuntu/storyteller/staticfiles/;
        access_log off;
        expires 30d;
    }

    location /media/ {
        alias /home/ubuntu/storyteller/media/;
        access_log off;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/storyteller /etc/nginx/sites-enabled/storyteller
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn
sudo systemctl restart gunicorn
sudo systemctl reload nginx

echo "==> health check (local HTTP)"
curl -sf -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1/api/stories/ || \
  curl -sf -o /dev/null -w "HTTP %{http_code}\n" -H "Host: ${DOMAIN}" http://127.0.0.1/api/stories/

echo "SETUP_COMPLETE"

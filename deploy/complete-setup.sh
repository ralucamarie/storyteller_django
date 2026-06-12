#!/usr/bin/env bash
set -euo pipefail
DB_PASS="${1:?usage: complete-setup.sh DB_PASSWORD}"
cd /home/ubuntu/storyteller
source /home/ubuntu/storyteller/venv/bin/activate
sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgres://storyteller:${DB_PASS}@localhost:5432/storyteller|" .env
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
sudo cp deploy/gunicorn.service /etc/systemd/system/gunicorn.service
sudo cp deploy/nginx-storyteller.conf /etc/nginx/sites-available/storyteller
sudo ln -sf /etc/nginx/sites-available/storyteller /etc/nginx/sites-enabled/storyteller
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn
sudo systemctl restart gunicorn
sudo nginx -t
sudo systemctl reload nginx
curl -sf -o /dev/null -w "local_api HTTP %{http_code}\n" -H "Host: api.povesticupesti.ro" http://127.0.0.1/api/stories/
echo DONE

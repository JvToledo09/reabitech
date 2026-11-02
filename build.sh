#!/usr/bin/env bash
set -o errexit

echo "=== Build REABITECH ==="
echo "DATABASE_URL definida: $([ -n "$DATABASE_URL" ] && echo 'sim' || echo 'nao')"

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput

echo "=== Build concluido ==="
#!/usr/bin/env bash
set -o errexit

echo "=== Build REABITECH ==="
echo "DATABASE_URL definida: $([ -n "$DATABASE_URL" ] && echo 'sim' || echo 'nao')"
echo "DEBUG=$DEBUG"

pip install -r requirements.txt
python manage.py collectstatic --noinput

echo "=== Build concluido ==="
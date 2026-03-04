#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Superuser (agar env o'zgaruvchilar qo'yilgan bo'lsa)
if [[ -n "$DJANGO_SUPERUSER_USERNAME" && -n "$DJANGO_SUPERUSER_PASSWORD" && -n "$DJANGO_SUPERUSER_EMAIL" ]]; then
  python manage.py createsuperuser --noinput || true
fi
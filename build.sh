#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# ---- Create / update admin user (Render) ----
python manage.py shell -c "import os; \
from django.contrib.auth import get_user_model; \
User=get_user_model(); \
u=os.environ.get('DJANGO_SUPERUSER_USERNAME') or os.environ.get('ADMIN_USERNAME'); \
e=os.environ.get('DJANGO_SUPERUSER_EMAIL','') or os.environ.get('ADMIN_EMAIL',''); \
p=os.environ.get('DJANGO_SUPERUSER_PASSWORD') or os.environ.get('ADMIN_PASSWORD'); \
assert u and p, 'SUPERUSER env yoq'; \
obj,created=User.objects.get_or_create(username=u, defaults={'email': e, 'is_staff': True, 'is_superuser': True}); \
obj.email=e or obj.email; \
obj.is_staff=True; obj.is_superuser=True; \
obj.set_password(p); obj.save(); \
print('ADMIN_OK', created)"
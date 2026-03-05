#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate

# ---- Create / update admin user (Render) ----
python manage.py shell -c "import os
from django.contrib.auth import get_user_model
User=get_user_model()

u=os.environ.get('DJANGO_SUPERUSER_USERNAME')
p=os.environ.get('DJANGO_SUPERUSER_PASSWORD')
e=os.environ.get('DJANGO_SUPERUSER_EMAIL','')

assert u and p, 'DJANGO_SUPERUSER_USERNAME/PASSWORD env yoq'

obj, _ = User.objects.get_or_create(username=u, defaults={'email': e})
obj.email = e or obj.email
obj.is_staff = True
obj.is_superuser = True
obj.set_password(p)
obj.save()
print('ADMIN_RESET_OK', u)
"
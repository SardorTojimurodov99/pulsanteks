This cleaned package was assembled from the latest uploaded project zips.

What was cleaned:
- removed nested duplicate folders like orders/orders/orders
- removed __pycache__ and .pyc files
- kept the top-level working app code only
- included seed_groups and seed_machines commands

Recommended deploy commands:
python manage.py makemigrations
python manage.py migrate
python manage.py seed_groups
python manage.py seed_machines
python manage.py check
python manage.py collectstatic --noinput

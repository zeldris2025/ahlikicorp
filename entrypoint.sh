#!/bin/bash
set -e

echo "Running migrations..."
python manage.py migrate

echo "Seeding initial data..."
python manage.py seed_data || true

echo "Starting Gunicorn server..."
exec gunicorn ahlikicorp.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --access-logfile - \
    --error-logfile -

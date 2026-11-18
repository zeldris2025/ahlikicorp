#!/bin/bash
set -e

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate --noinput

# Demo data (sample users, products, locations) only when asked for, so a
# restart never adds it on top of real content.
if [ "${SEED_DATA:-False}" = "True" ]; then
    echo "Seeding initial data..."
    python manage.py seed_data || true
fi

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

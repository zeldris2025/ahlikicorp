#!/bin/bash
# Azure App Service startup command:  bash startup.sh
#
# Runs on every start/deploy. It only ever moves the database FORWARD
# (migrate applies new migrations) — it never deletes, flushes or replaces it.
# The database and uploads live in /home/data (see DATA_DIR in settings.py),
# outside the code folder that each deployment overwrites.
set -e
cd "$(dirname "$0")"

echo "Applying database migrations (existing data is kept)..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Demo accounts have publicly known passwords, so they are never created in
# production unless explicitly asked for (App Setting SEED_DEMO_DATA=true).
if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
    echo "Seeding demo data..."
    python manage.py seed_data
fi

# SQLite on Azure's shared /home storage copes badly with several processes
# writing at once, so use a single worker with threads. With a real database
# server (DATABASE_URL set) use multiple workers.
if [ -n "$DATABASE_URL" ]; then
    WORKER_ARGS="--workers ${GUNICORN_WORKERS:-3}"
else
    WORKER_ARGS="--workers 1 --threads ${GUNICORN_THREADS:-4}"
fi

echo "Starting Gunicorn..."
exec gunicorn ahlikicorp.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    $WORKER_ARGS \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

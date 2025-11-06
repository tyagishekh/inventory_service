#!/bin/sh

set -e

echo "Waiting for PostgreSQL to be ready..."

# Simple loop to wait for the DB connection
until python -c "import psycopg2; psycopg2.connect(dbname='inventory_db', user='dev', password='dev', host='db')" >/dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "PostgreSQL is up - continuing..."

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn server..."
exec gunicorn inventory_service.wsgi:application --bind 0.0.0.0:8000 --workers 2


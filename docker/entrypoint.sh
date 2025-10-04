#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h ${POSTGRES_HOST:-db} -p ${POSTGRES_PORT:-5432} -U ${POSTGRES_USER:-openchat} > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL started"

echo "Waiting for Redis..."
until redis-cli -h ${REDIS_HOST:-redis} ping > /dev/null 2>&1; do
  echo "Redis is unavailable - sleeping"
  sleep 1
done
echo "Redis started"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || true

echo "Starting application..."
exec "$@"

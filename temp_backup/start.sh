#!/bin/bash

# Nexocart Backend Startup Script
# Optimized for Neon database connections

echo "Starting Nexocart Backend..."

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn with optimized settings for Neon
echo "Starting Gunicorn server..."
exec gunicorn core.wsgi:application \
    --config gunicorn.conf.py \
    --log-level info \
    --access-logfile - \
    --error-logfile -
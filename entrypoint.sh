#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Function to check if database is ready
wait_for_db() {
    echo "Waiting for database..."
    while ! nc -z db 5432; do
        sleep 1
    done
    echo "Database is ready."
}

# Wait for the database to be ready
wait_for_db

# Run database migrations
echo "Running database migrations..."
# PYTHONPATH=. alembic upgrade head # 기존 방식 주석 처리 (혹시 남아있다면)
PYTHONPATH=/app alembic upgrade head # PYTHONPATH 명시적 설정 추가

# Start the application
echo "Starting application..."
exec "$@" 
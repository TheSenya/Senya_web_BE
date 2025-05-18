#!/bin/bash

# Database migration setup
echo "Setting up database migrations..."

# Check if migrations directory exists and has version files
if [ ! -d "/app/migrations/versions" ] || [ -z "$(ls -A /app/migrations/versions)" ]; then
    echo "No migrations found. Generating initial migration..."
    alembic revision --autogenerate -m "Initial migration"
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application in production mode
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info 
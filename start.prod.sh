#!/bin/bash

# Wait for database to be ready
# echo "Waiting for database to be ready..."
# sleep 10

# Run database migrations
# echo "Running database migrations..."
# alembic upgrade head

# Start the application
echo "Starting application in production mode..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
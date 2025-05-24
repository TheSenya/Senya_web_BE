#!/bin/bash

# Create certificate directory if it doesn't exist
mkdir -p /app/cert

# Check if we have SSL certificates in environment variables (CI environment)
if [ ! -z "$SSL_KEY" ] && [ ! -z "$SSL_CERT" ]; then
    echo "Using SSL certificates from environment variables"
    # Decode base64 certificates
    echo "$SSL_KEY" | base64 -d > /app/cert/key.pem
    echo "$SSL_CERT" | base64 -d > /app/cert/cert.pem
    export SSL_KEY_PATH=/app/cert/key.pem
    export SSL_CERT_PATH=/app/cert/cert.pem
else
    echo "Using local SSL certificates"
fi

# Debug information
echo "SSL_KEY_PATH: $SSL_KEY_PATH"
echo "SSL_CERT_PATH: $SSL_CERT_PATH"
ls -la /app/cert

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

# Start the application without SSL (Nginx will handle SSL termination)
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level "${UVICORN_LOG_LEVEL:-debug}"
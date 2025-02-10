#!/bin/bash

# Check if we have SSL certificates in environment variables (CI environment)
if [ ! -z "$SSL_KEY" ] && [ ! -z "$SSL_CERT" ]; then
    echo "Using SSL certificates from environment variables"
    echo "$SSL_KEY" > /app/cert/key.pem
    echo "$SSL_CERT" > /app/cert/cert.pem
    SSL_KEY_PATH=/app/cert/key.pem
    SSL_CERT_PATH=/app/cert/cert.pem
fi

# Start the application with the appropriate certificate paths
exec uvicorn app.main:app --host 0.0.0.0 --port 443 --reload --log-level debug \
    --ssl-keyfile "$SSL_KEY_PATH" \
    --ssl-certfile "$SSL_CERT_PATH"
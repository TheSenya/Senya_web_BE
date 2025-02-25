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

# Start the application with the appropriate certificate paths
exec uvicorn app.main:app --host 0.0.0.0 --port 443 --reload --log-level debug \
    --ssl-keyfile "$SSL_KEY_PATH" \
    --ssl-certfile "$SSL_CERT_PATH"
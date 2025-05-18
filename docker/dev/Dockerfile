# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=development

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for certificates
RUN mkdir -p /app/cert

# Copy start script and make it executable
COPY docker/dev/start.sh .
RUN chmod +x start.sh

# Expose the port that the application listens on
EXPOSE 8000

# Set default paths for SSL certificates
ENV SSL_CERT_PATH=/cert/localhost+1.pem
ENV SSL_KEY_PATH=/cert/localhost+1-key.pem

# Use the development start script
ENTRYPOINT ["./start.sh"] 
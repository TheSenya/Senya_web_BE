# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
# ^ This prevents Python from writing .pyc files (compiled bytecode) to disk
# .pyc files are normally created to speed up module loading
# Setting this to 1 is a good practice in Docker containers because:
#   - It reduces container size
#   - Avoids potential permission issues
#   - Makes the container behavior more predictable
ENV PYTHONUNBUFFERED=1
# ^ This forces Python to run in unbuffered mode
# When set to 1:
#   - Python's output streams (stdout and stderr) are sent straight to the terminal without being buffered
#   - This ensures that you see Python output in real-time in your Docker logs
#   - Particularly useful for debugging and logging, as you don't have to wait for the buffer to fill up
#   - Prevents Python from buffering output which could be lost if the container crashes
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*
# ^ Update package list and install required system packages:
#   - apt-get update: Updates the package index files to get latest package info
#   - apt-get install -y: Installs packages without requiring confirmation (-y flag)
#   - gcc: GNU C Compiler, needed for compiling C extensions for Python packages ex. psycopg2 or django-cors-headers
# Then clean up to reduce image size:
#   - rm -rf /var/lib/apt/lists/*: This removes the package lists downloaded by apt-get update
#     This is done to reduce the size of the Docker image, as package lists can be quite large
#     and are not needed after the packages have been installed.

# Copy the requirements file into the image
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the image
COPY . .

# Expose the port that the application listens on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# ^ This command runs the FastAPI application using Uvicorn ASGI server
#   - "main:app" specifies the Python module containing the FastAPI app and the app object to use
#     "main" is the name of the Python module (file) containing the FastAPI app definition (main.py)
#     "app" is the name of the FastAPI app object defined in that module (in the main.py file)
#   - "--host 0.0.0.0" makes the server accessible externally by any network interface on the host machine
#   - "--port 8000" specifies the port on which the server will listen for incoming connections

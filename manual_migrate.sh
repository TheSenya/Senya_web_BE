#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo "Error: .env file not found"
    exit 1
fi

# Check required environment variables
required_vars=("POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_DB" "DATABASE_HOST" "DATABASE_PORT")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var is not set"
        exit 1
    fi
done

# Function to check database connection
check_db_connection() {
    echo "Checking database connection..."
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $DATABASE_HOST -p $DATABASE_PORT -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1" > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "Error: Could not connect to database"
        exit 1
    fi
    echo "Database connection successful"
}

# Function to show current migration status
show_status() {
    echo "Current migration status:"
    alembic current
    echo "Available migrations:"
    alembic history
}

# Function to run migrations
run_migrations() {
    echo "Running migrations..."
    alembic upgrade head
    if [ $? -eq 0 ]; then
        echo "Migrations completed successfully"
    else
        echo "Migration failed"
        exit 1
    fi
}

# Main script
echo "Starting database migration process..."

# Check database connection
check_db_connection

# Show current status
show_status

# Ask for confirmation
read -p "Do you want to proceed with migrations? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Migration cancelled"
    exit 0
fi

# Run migrations
run_migrations 
#!/bin/bash

# Exit on any error
set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if we're in production
is_production() {
    [ "$ENVIRONMENT" = "production" ]
}

# Function to check database connection
check_db_connection() {
    log "Checking database connection..."
    if ! alembic current > /dev/null 2>&1; then
        log "ERROR: Cannot connect to database"
        exit 1
    fi
}

# Function to backup database
backup_database() {
    if is_production; then
        log "Creating database backup..."
        BACKUP_FILE="/backups/backup_$(date +%Y%m%d_%H%M%S).sql"
        pg_dump -h "$DATABASE_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$BACKUP_FILE"
        log "Backup created at $BACKUP_FILE"
    fi
}

# Function to check for pending migrations
check_pending_migrations() {
    log "Checking for pending migrations..."
    if alembic current | grep -q "head"; then
        log "No pending migrations"
        return 0
    else
        log "Found pending migrations"
        return 1
    fi
}

# Main migration process
main() {
    log "Starting migration process..."

    # Check database connection
    check_db_connection

    # Backup database in production
    if is_production; then
        backup_database
    fi

    # Check for pending migrations
    if check_pending_migrations; then
        log "Database is up to date"
        exit 0
    fi

    # Run migrations
    log "Running migrations..."
    alembic upgrade head

    # Verify migration
    if check_pending_migrations; then
        log "Migration completed successfully"
    else
        log "ERROR: Migration may have failed"
        exit 1
    fi
}

# Run main process
main 
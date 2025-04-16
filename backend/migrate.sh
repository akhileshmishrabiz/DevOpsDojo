#!/bin/bash

# Exit on error
set -e

# Export Flask app
export FLASK_APP=${FLASK_APP:-run.py}

echo "Running database migrations..."

# Check if migrations directory exists
if [ ! -d "migrations" ]; then
    echo "Initializing migrations directory..."
    flask db init
    
    # Clean up alembic_version table if it exists
    echo "Checking for alembic_version table..."
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USERNAME" -d "$DB_NAME" -c "SELECT to_regclass('alembic_version')" | grep -q "alembic_version"; then
        echo "Cleaning alembic_version table to prevent revision conflicts..."
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USERNAME" -d "$DB_NAME" -c "DROP TABLE alembic_version;"
    fi
fi

# Check if there are any existing migrations
if [ ! "$(ls -A migrations/versions 2>/dev/null)" ]; then
    echo "No existing migrations found. Creating initial migration..."
    
    # Ensure alembic_version is clean
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USERNAME" -d "$DB_NAME" -c "SELECT to_regclass('alembic_version')" | grep -q "alembic_version"; then
        echo "Cleaning alembic_version table to prevent revision conflicts..."
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USERNAME" -d "$DB_NAME" -c "DROP TABLE alembic_version;"
    fi
    
    # Create and apply initial migration
    flask db migrate -m "Initial migration"
    echo "Applying initial migration..."
    flask db upgrade
else
    # Try to upgrade first (in case there are existing migrations)
    echo "Attempting to upgrade existing migrations..."
    flask db upgrade || {
        echo "Error upgrading migrations. Attempting to reset and create new migration..."
        
        # If the migration fails, clean up and start fresh
        echo "Removing existing migration versions..."
        rm -rf migrations/versions/*
        
        # Drop alembic_version table to start clean
        echo "Dropping alembic_version table..."
        PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USERNAME" -d "$DB_NAME" -c "DROP TABLE IF EXISTS alembic_version;"
        
        # Create and apply new migration
        echo "Creating fresh migration..."
        flask db migrate -m "Reset migration"
        echo "Applying fresh migration..."
        flask db upgrade
    }
fi

echo "Checking if seed data is needed..."
# Only run seed data if topics table is empty
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USERNAME" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM topics" 2>/dev/null | grep -q "0" && {
    echo "Running seed data..."
    python seed_data.py
} || {
    echo "Database already contains data, skipping seed"
}

echo "Database setup completed successfully!"
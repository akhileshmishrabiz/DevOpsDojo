#!/bin/bash

host="$1"
shift
cmd="$@"

echo "Waiting for database..."
until PGPASSWORD=postgres psql -h "$host" -U "postgres" -d "devops_learning" -c '\q' 2>/dev/null; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

echo "Database is up - running migrations"

# Run migrations using migrate.sh
./migrate.sh || {
    echo "Migration failed"
    exit 1
}

echo "Starting application"
# Execute the passed command
exec $cmd

# add the question to db
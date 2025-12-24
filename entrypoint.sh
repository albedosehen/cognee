#!/bin/bash

set -e  # Exit on error
echo "Debug mode: $DEBUG"
echo "Environment: $ENVIRONMENT"

# Set default ports if not specified
DEBUG_PORT=${DEBUG_PORT:-5678}
HTTP_PORT=${HTTP_PORT:-8000}
echo "Debug port: $DEBUG_PORT"
echo "HTTP port: $HTTP_PORT"

# Run Alembic migrations with proper error handling.
# Note on UserAlreadyExists error handling:
# During database migrations, we attempt to create a default user. If this user
# already exists (e.g., from a previous deployment or migration), it's not a
# critical error and shouldn't prevent the application from starting. This is
# different from other migration errors which could indicate database schema
# inconsistencies and should cause the startup to fail. This check allows for
# smooth redeployments and container restarts while maintaining data integrity.
echo "Running database migrations..."

# Use a temporary file for migration output to allow real-time logging
MIGRATION_LOG=$(mktemp)
trap "rm -f $MIGRATION_LOG" EXIT

# Run migrations with real-time output and capture for error checking
if alembic upgrade head 2>&1 | tee "$MIGRATION_LOG"; then
    echo "Database migrations completed successfully."
else
    MIGRATION_EXIT_CODE=$?
    MIGRATION_OUTPUT=$(cat "$MIGRATION_LOG")
    
    echo "Migration command exited with code: $MIGRATION_EXIT_CODE"
    
    # Check for known non-critical errors
    if echo "$MIGRATION_OUTPUT" | grep -q "UserAlreadyExists\|User default_user@example.com already exists"; then
        echo "Warning: Default user already exists, continuing startup..."
    elif echo "$MIGRATION_OUTPUT" | grep -q "table.*already exists"; then
        echo "Tables already exist but alembic_version is missing/out of sync."
        echo "This typically happens when upgrading from code that used create_all() instead of migrations."
        echo "Attempting to stamp database to current schema version..."
        
        # Stamp the database as being at the head revision
        if alembic stamp head; then
            echo "Database successfully stamped to head revision."
        else
            echo "Failed to stamp database. Migration output:"
            cat "$MIGRATION_LOG"
            echo "Please manually verify schema and run 'alembic stamp head'."
            exit 1
        fi
    else
        echo "Migration failed with unexpected error:"
        cat "$MIGRATION_LOG"
        exit 1
    fi
fi

echo "Starting server..."

# Add startup delay to ensure DB is ready
sleep 2

# Modified Gunicorn startup with error handling
if [ "$ENVIRONMENT" = "dev" ] || [ "$ENVIRONMENT" = "local" ]; then
    if [ "$DEBUG" = "true" ]; then
        echo "Waiting for the debugger to attach..."
        exec debugpy --wait-for-client --listen 0.0.0.0:$DEBUG_PORT -m gunicorn -w 1 -k uvicorn.workers.UvicornWorker -t 30000 --bind=0.0.0.0:$HTTP_PORT --log-level debug --reload --access-logfile - --error-logfile - cognee.api.client:app
    else
        exec gunicorn -w 1 -k uvicorn.workers.UvicornWorker -t 30000 --bind=0.0.0.0:$HTTP_PORT --log-level debug --reload --access-logfile - --error-logfile - cognee.api.client:app
    fi
else
    exec gunicorn -w 1 -k uvicorn.workers.UvicornWorker -t 30000 --bind=0.0.0.0:$HTTP_PORT --log-level error --access-logfile - --error-logfile - cognee.api.client:app
fi

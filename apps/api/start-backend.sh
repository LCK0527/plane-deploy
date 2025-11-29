#!/bin/bash

# Start Django backend for Time Tracking development

set -e

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables
export REDIS_URL="${REDIS_URL:-redis://localhost:6379}"

# Check which port Docker PostgreSQL is actually using
DOCKER_DB_CONTAINER=$(docker ps -q -f name=plane-db)
if [ ! -z "$DOCKER_DB_CONTAINER" ]; then
    # Docker container is running, check what port it's mapped to
    DOCKER_PORT=$(docker port $DOCKER_DB_CONTAINER 2>/dev/null | grep "5432/tcp" | cut -d ':' -f2 | cut -d '-' -f1 || echo "")
    if [ ! -z "$DOCKER_PORT" ]; then
        POSTGRES_PORT=$DOCKER_PORT
        echo "✅ Found Docker PostgreSQL container on port ${POSTGRES_PORT}"
    else
        # Fallback: check if 5432 is available, otherwise try 5433
        if lsof -Pi :5432 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
            POSTGRES_PORT=5433
            echo "⚠️  Port 5432 in use, trying port 5433"
        else
            POSTGRES_PORT=5432
        fi
    fi
else
    # No Docker container, use default
    if lsof -Pi :5432 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        POSTGRES_PORT=5433
        echo "⚠️  Port 5432 in use, trying port 5433"
    else
        POSTGRES_PORT=5432
    fi
fi

# Try to get credentials from .env file if it exists
if [ -f "../.env" ]; then
    POSTGRES_USER=$(grep -E "^POSTGRES_USER=" ../.env | cut -d '=' -f2 | tr -d '"' | head -1)
    POSTGRES_PASSWORD=$(grep -E "^POSTGRES_PASSWORD=" ../.env | cut -d '=' -f2 | tr -d '"' | head -1)
    POSTGRES_DB=$(grep -E "^POSTGRES_DB=" ../.env | cut -d '=' -f2 | tr -d '"' | head -1)
fi

# Set defaults if not found
POSTGRES_USER=${POSTGRES_USER:-plane}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-plane}
POSTGRES_DB=${POSTGRES_DB:-plane}

# With POSTGRES_HOST_AUTH_METHOD=trust, we can connect without password
# But psycopg still needs the format, so we'll try with password first, then without
export DATABASE_URL="${DATABASE_URL:-postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}}"
echo "📊 Using database: ${POSTGRES_DB} on port ${POSTGRES_PORT} (user: ${POSTGRES_USER})"

echo "🔧 Running migrations..."
python manage.py migrate

echo "🚀 Starting Django development server on http://localhost:8000"
python manage.py runserver 8000


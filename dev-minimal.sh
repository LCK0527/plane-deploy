#!/bin/bash

# Minimal dev setup for Time Tracking feature
# This only starts the essential services needed for testing

set -e

REPO_ROOT="/Users/philip/Desktop/Linux Final Project/Plane"
cd "$REPO_ROOT"

echo "🚀 Starting minimal dev environment for Time Tracking..."
echo ""

# Check if port 5432 is in use
if lsof -Pi :5432 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 5432 is already in use by a local PostgreSQL service"
    echo "   Using docker-compose-local-minimal.yml with port 5433 instead"
    echo ""
    # Create network if it doesn't exist
    docker network create dev_env 2>/dev/null || true
    # Use alternative compose file with port 5433
    docker-compose -f docker-compose-local-minimal.yml up -d
    export DOCKER_POSTGRES_PORT=5433
else
    # Start only essential Docker services
    echo "📦 Starting Docker services (PostgreSQL & Redis)..."
    docker-compose -f docker-compose-local.yml up -d plane-db plane-redis
    export DOCKER_POSTGRES_PORT=5432
fi

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 3

# Check if services are running
if ! docker ps | grep -q "plane-db"; then
    echo "❌ Database container failed to start"
    exit 1
fi

if ! docker ps | grep -q "plane-redis"; then
    echo "❌ Redis container failed to start"
    exit 1
fi

echo "✅ Docker services are running"
echo ""
echo "📝 Next steps:"
echo "   1. Start the backend API (in a separate terminal):"
if [ "$DOCKER_POSTGRES_PORT" = "5433" ]; then
    echo "      cd apps/api"
    echo "      source venv/bin/activate"
    echo "      export REDIS_URL='redis://localhost:6379'"
    echo "      export DATABASE_URL='postgresql://plane:plane@localhost:5433/plane'"
    echo "      python manage.py migrate"
    echo "      python manage.py runserver 8000"
else
    echo "      cd apps/api"
    echo "      ./start-backend.sh"
fi
echo ""
echo "   2. Start the frontend (in another terminal):"
echo "      cd apps/web"
echo "      pnpm dev"
echo ""
echo "   3. Open http://localhost:3000 in your browser"
echo ""
echo "💡 To stop Docker services:"
if [ "$DOCKER_POSTGRES_PORT" = "5433" ]; then
    echo "   docker-compose -f docker-compose-local-minimal.yml down"
else
    echo "   docker-compose -f docker-compose-local.yml stop plane-db plane-redis"
fi


# Minimal Dev Setup for Time Tracking Feature

This guide shows you how to run **only** what's needed to test the Time Tracking feature, without starting the entire Plane monorepo.

## Quick Start (3 Terminals)

### Terminal 1: Start Docker Services
```bash
cd "/Users/philip/Desktop/Linux Final Project/Plane"
./dev-minimal.sh
```

The script will automatically detect if port 5432 is in use and use port 5433 instead.

Or manually:
```bash
# If port 5432 is free:
docker-compose -f docker-compose-local.yml up -d plane-db plane-redis

# If port 5432 is in use:
docker network create dev_env 2>/dev/null || true
docker-compose -f docker-compose-local-minimal.yml up -d
```

### Terminal 2: Start Backend API
```bash
cd "/Users/philip/Desktop/Linux Final Project/Plane/apps/api"
./start-backend.sh
```

Or manually:
```bash
cd apps/api
source venv/bin/activate
export REDIS_URL="redis://localhost:6379"
export DATABASE_URL="postgresql://plane:plane@localhost:5432/plane"
python manage.py migrate
python manage.py runserver 8000
```

### Terminal 3: Start Frontend
```bash
cd "/Users/philip/Desktop/Linux Final Project/Plane/apps/web"
pnpm dev
```

## What's Running

- **PostgreSQL** (port 5432) - Database
- **Redis** (port 6379) - Cache
- **Django API** (port 8000) - Backend
- **Next.js Frontend** (port 3000) - Frontend

## Environment Variables

The frontend needs to know where the API is. Create `apps/web/.env.local` with:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

**Important:** If this is not set, the frontend won't be able to connect to the backend API. The default is an empty string which will cause API calls to fail.

You can also set it as an environment variable before running `pnpm dev`:
```bash
export NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
pnpm dev
```

## Testing Time Tracking

1. Open http://localhost:3000
2. Log in to your workspace
3. Navigate to a project
4. Open any work item/issue
5. The Time Tracking widget should appear in the sidebar (if time tracking is enabled for the project)

## Stopping Services

```bash
# Stop Docker services
docker-compose -f docker-compose-local.yml stop plane-db plane-redis

# Or stop everything
docker-compose -f docker-compose-local.yml down
```

## Troubleshooting

### Port 5432 already in use
The script automatically detects this and uses port 5433 instead. Make sure your backend uses the correct port:
- If using port 5433: `DATABASE_URL="postgresql://plane:plane@localhost:5433/plane"`
- The `start-backend.sh` script automatically detects and uses the correct port

### Backend can't connect to database
- Make sure Docker services are running: `docker ps`
- Check which port PostgreSQL is using: `docker ps | grep plane-db`
- If using port 5433, make sure `DATABASE_URL` uses port 5433
- The database uses `trust` authentication, so no password is required from Docker containers, but the connection string format still needs credentials

### Frontend can't connect to backend
- Verify backend is running on port 8000
- Check `NEXT_PUBLIC_API_BASE_URL` is set correctly
- Check browser console for CORS errors

### Port already in use
- Stop other services using those ports
- Or change ports in docker-compose-local.yml and update environment variables


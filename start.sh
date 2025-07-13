#!/bin/bash
set -e

echo "=== Starting Autopublicador Web API ==="
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

echo "Python version: $(python --version)"
echo "PORT environment variable: $PORT"
echo "Environment variables:"
env | grep -E '^(PORT|DATABASE_URL|REDIS_URL|ENVIRONMENT)' || echo "No relevant env vars found"

# Verificar que main.py existe
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found in current directory"
    exit 1
fi

echo "main.py found, checking dependencies..."
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')" || { echo "FastAPI import failed"; exit 1; }
python -c "import uvicorn; print(f'Uvicorn version: {uvicorn.__version__}')" || { echo "Uvicorn import failed"; exit 1; }

echo "Testing application import..."
python -c "from main import app; print('Application imported successfully')" || { echo "Application import failed"; exit 1; }

# Ejecutar migraciones de Alembic si existe alembic.ini
if [ -f "alembic.ini" ]; then
    echo "Running Alembic migrations..."
    alembic upgrade head || echo "Migration failed, continuing..."
else
    echo "No alembic.ini found, skipping migrations"
fi

echo "Starting FastAPI application on port ${PORT:-8000}..."
echo "Health check will be available at: http://localhost:${PORT:-8000}/ping"

# Iniciar la aplicación
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info --access-log
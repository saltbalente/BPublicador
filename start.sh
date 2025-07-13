#!/bin/bash
set -e

# Configurar variables de entorno por defecto
export PORT=${PORT:-8000}
export ENVIRONMENT=${ENVIRONMENT:-production}
export LOG_LEVEL=${LOG_LEVEL:-info}

echo "=== Railway FastAPI Startup Script ==="
echo "Timestamp: $(date)"
echo "Current directory: $(pwd)"
echo "Python version: $(python --version)"
echo "PORT: $PORT"
echo "ENVIRONMENT: $ENVIRONMENT"

# Verificar estructura de directorios
echo "Directory structure:"
ls -la

# Verificar que main.py existe
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found in current directory"
    echo "Available files:"
    find . -name "*.py" -type f | head -10
    exit 1
fi

# Verificar dependencias críticas
echo "Checking critical dependencies..."
python -c "import sys; print(f'Python executable: {sys.executable}')" || exit 1
python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')" || { echo "FastAPI not available"; exit 1; }
python -c "import uvicorn; print(f'Uvicorn: {uvicorn.__version__}')" || { echo "Uvicorn not available"; exit 1; }
python -c "import sqlalchemy; print(f'SQLAlchemy: {sqlalchemy.__version__}')" || echo "SQLAlchemy not available (optional)"

# Test básico de importación de la aplicación
echo "Testing application import..."
python -c "from main import app; print('✓ Application imported successfully')" || {
    echo "✗ Application import failed"
    echo "Trying to diagnose the issue..."
    python -c "import main" 2>&1 | head -20
    exit 1
}

# Verificar que los endpoints de health están definidos
echo "Checking health endpoints..."
python -c "
from main import app
routes = [route.path for route in app.routes if hasattr(route, 'path')]
health_endpoints = ['/ping', '/ready', '/healthz']
for endpoint in health_endpoints:
    if endpoint in routes:
        print(f'✓ {endpoint} endpoint available')
    else:
        print(f'✗ {endpoint} endpoint missing')
        exit(1)
print('✓ All health endpoints configured')
" || {
    echo "✗ Health endpoint configuration failed"
    exit 1
}

# Ejecutar migraciones si es necesario
if [ -f "alembic.ini" ] && [ -n "$DATABASE_URL" ]; then
    echo "Running database migrations..."
    python -c "import alembic; print(f'Alembic: {alembic.__version__}')" || { echo "Alembic not available"; exit 1; }
    alembic upgrade head || {
        echo "Migration failed, but continuing..."
        echo "This might be expected if database is not yet available"
    }
else
    echo "Skipping migrations (no alembic.ini or DATABASE_URL)"
fi

# Configurar uvicorn con parámetros optimizados para Railway
echo "Starting FastAPI application..."
echo "Server will be available at: http://0.0.0.0:$PORT"
echo "Health check endpoint: http://0.0.0.0:$PORT/ping"
echo "Ready endpoint: http://0.0.0.0:$PORT/ready"

# Usar exec para reemplazar el proceso shell
exec uvicorn main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --log-level $LOG_LEVEL \
    --access-log \
    --loop asyncio \
    --http httptools \
    --lifespan on
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

# Verificar que main.py existe en la raíz
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found in current directory"
    echo "Available files:"
    find . -name "*.py" -type f | head -10
    exit 1
fi

# Verificar que el directorio backend existe
if [ ! -d "backend" ]; then
    echo "ERROR: backend directory not found"
    echo "Available directories:"
    ls -la
    exit 1
fi

# Verificar dependencias críticas
echo "Checking critical dependencies..."
python -c "import sys; print(f'Python executable: {sys.executable}')" || exit 1

# Verificar que podemos importar desde backend
echo "Testing backend imports..."
PYTHONPATH="./backend:$PYTHONPATH" python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')" || { echo "FastAPI not available"; exit 1; }
PYTHONPATH="./backend:$PYTHONPATH" python -c "import uvicorn; print(f'Uvicorn: {uvicorn.__version__}')" || { echo "Uvicorn not available"; exit 1; }
PYTHONPATH="./backend:$PYTHONPATH" python -c "import sqlalchemy; print(f'SQLAlchemy: {sqlalchemy.__version__}')" || echo "SQLAlchemy not available (optional)"

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

# Las migraciones ya se ejecutaron en la fase de build de nixpacks
echo "Skipping migrations (already executed in build phase)"

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
#!/bin/bash
set -e

# Verificar que estamos en el directorio correcto
echo "Current directory: $(pwd)"
echo "Contents: $(ls -la)"

# Verificar que main.py existe
if [ ! -f "main.py" ]; then
    echo "Error: main.py not found in current directory"
    exit 1
fi

# Ejecutar migraciones si es necesario
if [ -f "alembic.ini" ]; then
    echo "Running database migrations..."
    python -m alembic upgrade head || echo "Migration failed, continuing..."
fi

# Iniciar la aplicación
echo "Starting FastAPI application..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
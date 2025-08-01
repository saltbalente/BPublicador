"""
Main application optimized for Vercel deployment
"""
import os
import sys
from pathlib import Path

# Configurar el path para importaciones
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Inicializar la aplicación para Vercel
def init_for_vercel():
    """Inicialización específica para Vercel"""
    try:
        # Ejecutar inicialización de base de datos
        from vercel_init import init_database, create_directories
        create_directories()
        init_database()
        print("✅ Vercel initialization completed")
    except Exception as e:
        print(f"⚠️ Vercel initialization warning: {e}")

# Ejecutar inicialización solo en Vercel
if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
    init_for_vercel()

# Importar la aplicación principal
from main import app

# Configuraciones específicas para Vercel
if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
    # Configurar variables de entorno para producción
    os.environ.setdefault("ENVIRONMENT", "production")
    os.environ.setdefault("DEBUG", "false")
    os.environ.setdefault("DATABASE_URL", "sqlite:///./autopublicador.db")

# Handler para Vercel
def handler(request, context):
    """Handler principal para Vercel"""
    return app(request, context)

# Exportar la aplicación para Vercel
app = app
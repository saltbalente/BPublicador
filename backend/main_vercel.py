"""Punto de entrada optimizado para Vercel"""
import os
import sys
from pathlib import Path

# Configurar rutas de importación
current_dir = Path(__file__).parent
backend_dir = current_dir
project_root = current_dir.parent

# Añadir directorios al path de Python
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

# Configurar variables de entorno para Vercel
if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
    print("🚀 Inicializando aplicación para Vercel...")
    
    # Ejecutar inicialización específica para Vercel
    from vercel_init import initialize_for_vercel
    initialize_for_vercel()
    
    # Configurar variables de entorno para producción
    os.environ.setdefault("ENVIRONMENT", "production")
    os.environ.setdefault("DEBUG", "false")
    os.environ.setdefault("DATABASE_URL", "sqlite:///./autopublicador.db")
    
    # Importar y validar configuración de producción
    try:
        from config_production import config
        print("✅ Configuración de producción cargada")
    except ImportError as e:
        print(f"⚠️ Error al cargar configuración de producción: {e}")

# Importar y exportar la aplicación principal
from main import app

# Exportar para Vercel
__all__ = ["app"]
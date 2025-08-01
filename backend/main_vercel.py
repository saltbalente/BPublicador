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

# Configurar variables de entorno ANTES de cualquier importación
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("DATABASE_URL", "sqlite:///./autopublicador.db")

# Configurar variables de entorno para Vercel
if os.getenv("VERCEL") or os.getenv("VERCEL_ENV") or os.getenv("ENVIRONMENT") == "production":
    print("🚀 Inicializando aplicación para Vercel...")
    
    # Ejecutar inicialización específica para Vercel
    try:
        from vercel_init import initialize_for_vercel
        initialize_for_vercel()
        print("✅ Inicialización de Vercel completada")
    except Exception as e:
        print(f"⚠️ Error en inicialización de Vercel: {e}")
    
    # Importar y validar configuración de producción
    try:
        from config_production import config
        print("✅ Configuración de producción cargada")
    except ImportError as e:
        print(f"⚠️ Error al cargar configuración de producción: {e}")

# Importar la aplicación principal con manejo robusto de errores
app = None

try:
    # Asegurar que estamos en el directorio correcto
    original_cwd = os.getcwd()
    os.chdir(str(backend_dir))
    
    # Configurar PYTHONPATH para las importaciones
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    # Importar la aplicación
    from main import app
    
    # Restaurar directorio de trabajo
    os.chdir(original_cwd)
    
    print("✅ Aplicación FastAPI cargada correctamente")
    print(f"✅ App title: {getattr(app, 'title', 'N/A')}")
    
except Exception as e:
    print(f"❌ Error al cargar la aplicación principal: {e}")
    print(f"❌ Error type: {type(e).__name__}")
    
    # Restaurar directorio de trabajo en caso de error
    try:
        os.chdir(original_cwd)
    except:
        pass
    
    # Crear una aplicación básica como fallback
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI(
        title="Autopublicador - Modo Seguro", 
        description="Aplicación en modo seguro debido a error en carga principal",
        version="1.0.0-safe"
    )
    
    @app.get("/")
    async def root():
        return {
            "status": "safe_mode",
            "message": "Aplicación ejecutándose en modo seguro",
            "error": str(e),
            "error_type": type(e).__name__
        }
    
    @app.get("/health")
    async def health():
        return {"status": "ok", "mode": "safe"}

# Verificar que tenemos una aplicación válida
if app is None:
    from fastapi import FastAPI
    app = FastAPI(title="Autopublicador - Error Crítico")
    
    @app.get("/")
    async def critical_error():
        return {"error": "Error crítico al cargar la aplicación"}

# Exportar para Vercel
__all__ = ["app"]
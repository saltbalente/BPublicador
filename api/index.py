"""Punto de entrada principal para Vercel Functions"""
import os
import sys
from pathlib import Path

# Configurar rutas de importación
current_dir = Path(__file__).parent
project_root = current_dir.parent
backend_dir = project_root / "backend"

# Añadir directorios al path de Python
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

# Configurar variables de entorno ANTES de cualquier importación
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("DEBUG", "false")

# Configurar variables de entorno para Vercel
if os.getenv("VERCEL") or os.getenv("VERCEL_ENV") or os.getenv("ENVIRONMENT") == "production":
    print("🚀 Inicializando aplicación para Vercel...")
    
    # Ejecutar inicialización específica para Vercel
    try:
        sys.path.insert(0, str(backend_dir))
        from vercel_init import initialize_for_vercel
        initialize_for_vercel()
        print("✅ Inicialización de Vercel completada")
    except Exception as e:
        print(f"⚠️ Error en inicialización de Vercel: {e}")

# Importar la aplicación principal
app = None

try:
    # Asegurar que estamos en el directorio correcto
    original_cwd = os.getcwd()
    os.chdir(str(backend_dir))
    
    # Importar la aplicación
    from main import app
    
    # Restaurar directorio de trabajo
    os.chdir(original_cwd)
    
    print("✅ Aplicación FastAPI cargada correctamente")
    
except Exception as e:
    print(f"❌ Error al cargar la aplicación principal: {e}")
    
    # Restaurar directorio de trabajo en caso de error
    try:
        os.chdir(original_cwd)
    except:
        pass
    
    # Crear una aplicación básica como fallback
    from fastapi import FastAPI
    
    app = FastAPI(
        title="Autopublicador - Modo Seguro", 
        description="Aplicación en modo seguro",
        version="1.0.0-safe"
    )
    
    @app.get("/")
    async def root():
        return {
            "status": "safe_mode",
            "message": "Aplicación ejecutándose en modo seguro",
            "error": str(e)
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
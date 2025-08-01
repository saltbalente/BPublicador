import os
import sys
from pathlib import Path

# Configurar rutas de importación
# En Vercel, el script se ejecuta desde la raíz del proyecto.
project_root = Path.cwd()
backend_dir = project_root / 'backend'

# Añadir directorios al path de Python
# Es crucial que 'backend' esté en el path para que las importaciones como 'from main import app' funcionen.
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

# Configurar variables de entorno ANTES de cualquier importación
os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("DEBUG", "false")

# Importar la aplicación principal con manejo robusto de errores
app = None

try:
    # Vercel ejecuta desde la raíz, por lo que las importaciones relativas a 'backend' deben funcionar
    # si 'backend' está en el PYTHONPATH.
    # Se cambia la importación para evitar un ciclo de importación.
    from backend.application import create_app
    app = create_app()
    print("✅ Aplicación FastAPI cargada correctamente")
    print(f"✅ App title: {getattr(app, 'title', 'N/A')}")
    
except Exception as e:
    print(f"❌ Error al cargar la aplicación principal: {e}")
    print(f"❌ Error type: {type(e).__name__}")
    import traceback
    print("Traceback:")
    traceback.print_exc()
    
    # Crear una aplicación básica como fallback para diagnóstico
    from fastapi import FastAPI
    
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
            "error_type": type(e).__name__,
            "python_path": sys.path,
            "cwd": os.getcwd()
        }

# Verificar que tenemos una aplicación válida
if app is None:
    from fastapi import FastAPI
    app = FastAPI(title="Autopublicador - Error Crítico")
    
    @app.get("/")
    async def critical_error():
        return {"error": "Error crítico al cargar la aplicación"}

# Exportar para Vercel
__all__ = ["app"]
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

# Crear aplicación FastAPI ultra-simple
app = FastAPI(
    title="Autopublicador Web API - Simple",
    version="1.0.0",
    description="API simplificada para Render deployment"
)

# Configurar CORS básico
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoints de health check básicos
@app.get("/")
def root():
    """Endpoint raíz"""
    return {"message": "Autopublicador Web API", "status": "running"}

@app.get("/ping")
def ping():
    """Endpoint ultra-simple de ping"""
    return {"status": "ok"}

@app.get("/health")
def health():
    """Endpoint de health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "autopublicador-api-simple"
    }

@app.get("/debug/env")
def debug_env():
    """Endpoint de diagnóstico de variables de entorno"""
    return {
        "PORT": os.getenv("PORT", "Not set"),
        "DATABASE_URL": os.getenv("DATABASE_URL", "Not set"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "Not set"),
        "DEBUG": os.getenv("DEBUG", "Not set"),
        "PYTHON_VERSION": os.getenv("PYTHON_VERSION", "Not set")
    }

@app.get("/ready")
def ready():
    """Endpoint para verificar que la app está lista"""
    return {
        "status": "ready", 
        "service": "autopublicador-api",
        "port": os.getenv("PORT", "unknown")
    }

@app.get("/healthz")
def healthz():
    """Endpoint de health check compatible con Kubernetes/Railway"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main_simple:app", host="0.0.0.0", port=port, reload=False)
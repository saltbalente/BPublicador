from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import os

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Crear aplicación FastAPI
app = FastAPI(
    title="Autopublicador Web API",
    version="1.0.0",
    description="API para generación automática de contenido con IA"
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
        "service": "autopublicador-api"
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
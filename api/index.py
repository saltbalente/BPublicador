"""Punto de entrada de diagnóstico para Vercel"""
from fastapi import FastAPI

app = FastAPI(
    title="Diagnóstico de Vercel",
    description="Un 'Hola Mundo' para verificar la configuración del build.",
    version="1.0.0-diagnostic"
)

@app.get("/")
async def root():
    return {"status": "ok", "message": "¡El build de Vercel funciona!"}

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    return {
        "status": "ok",
        "message": "¡El build de Vercel funciona!",
        "path_captured": full_path
    }
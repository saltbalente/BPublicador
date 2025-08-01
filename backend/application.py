# backend/application.py

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.core.database import get_db
from app.models.content import Content
from sqlalchemy.orm import Session
import time
from datetime import datetime
import os
import html
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
content_logger = logging.getLogger("content_update")
content_logger.setLevel(logging.DEBUG)

def create_app() -> FastAPI:
    """Crea y configura una instancia de la aplicación FastAPI."""
    app_instance = FastAPI(
        title="Autopublicador Web API",
        version="1.0.0",
        description="API para generación automática de contenido con IA"
    )

    # Manejador de excepciones genérico
    @app_instance.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logging.error(f"Error no capturado: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error interno del servidor: {exc}"},
        )

    # Middleware de CORS
    app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # O configurar orígenes específicos
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rutas para archivos estáticos (frontend y assets)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_path = os.path.join(base_dir, "..", "frontend", "dist")
    images_path = os.path.join(base_dir, "static", "images")

    if not os.path.exists(frontend_path):
        logging.warning(f"El directorio del frontend no existe: {frontend_path}")
    if not os.path.exists(images_path):
        os.makedirs(images_path)
        logging.info(f"Directorio de imágenes creado: {images_path}")

    app_instance.mount("/static", StaticFiles(directory=frontend_path), name="static")
    app_instance.mount("/images", StaticFiles(directory=images_path), name="images")

    # Configuración de plantillas Jinja2
    templates = Jinja2Templates(directory=frontend_path)

    def unescape_html(s: str) -> str:
        return html.unescape(s)

    templates.env.filters['unescape_html'] = unescape_html

    # Las importaciones de rutas se mueven aquí para evitar ciclos
    from app.api.v1.router import api_router
    app_instance.include_router(api_router, prefix=settings.API_V1_STR)

    # Endpoint para la raíz del sitio (sirve el index.html)
    @app_instance.get("/", response_class=HTMLResponse)
    async def read_root(request: Request, db: Session = Depends(get_db)):
        try:
            contents = db.query(Content).order_by(Content.created_at.desc()).limit(10).all()
            return templates.TemplateResponse("index.html", {"request": request, "contents": contents})
        except Exception as e:
            logging.error(f"Error al acceder a la base de datos en la ruta raíz: {e}", exc_info=True)
            raise HTTPException(status_code=503, detail="No se pudo conectar a la base de datos.")

    # Catch-all para el enrutamiento del lado del cliente de Vue
    @app_instance.get("/{full_path:path}", response_class=FileResponse)
    async def serve_vue_app(full_path: str):
        file_path = os.path.join(frontend_path, 'index.html')
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="index.html no encontrado")
        return FileResponse(file_path)

    return app_instance
from fastapi import APIRouter
from app.api.v1 import auth, keywords, content, keyword_analysis, image_generation, scheduler, analytics, categories, tags, seo_schemas, users, security, publication, templates, visual_config

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["autenticación"]
)

api_router.include_router(
    keywords.router,
    prefix="/keywords",
    tags=["palabras-clave"]
)

api_router.include_router(
    content.router,
    prefix="/content",
    tags=["contenido"]
)

api_router.include_router(
    categories.router,
    prefix="/categories",
    tags=["categorías"]
)

api_router.include_router(
    tags.router,
    prefix="/tags",
    tags=["etiquetas"]
)

api_router.include_router(
    seo_schemas.router,
    prefix="/seo-schemas",
    tags=["esquemas-seo"]
)

api_router.include_router(
    keyword_analysis.router,
    prefix="/keyword-analysis",
    tags=["análisis-keywords"]
)

api_router.include_router(
    image_generation.router,
    prefix="/image-generation",
    tags=["generación-imágenes"]
)

api_router.include_router(
    scheduler.router,
    prefix="/scheduler",
    tags=["programador"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["usuarios"]
)

api_router.include_router(
    security.router,
    prefix="/security",
    tags=["seguridad"]
)

api_router.include_router(
    publication.router,
    prefix="/publication",
    tags=["publicación-web"]
)

api_router.include_router(
    templates.router,
    prefix="/templates",
    tags=["templates"]
)

api_router.include_router(
    visual_config.router,
    prefix="/visual-config",
    tags=["configuración-visual"]
)
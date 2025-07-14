from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.core.database import get_db
from app.api.dependencies import get_current_active_user
from app.models.user import User
from app.services.landing_generator import LandingPageGenerator
from pydantic import BaseModel

# Router para las funcionalidades de Landing Pages
router = APIRouter()

# ============================================================================
# MODELOS PYDANTIC PARA LANDINGS
# ============================================================================

class LandingPageCreate(BaseModel):
    """Modelo para crear una nueva landing page"""
    title: str
    description: Optional[str] = None
    template_id: Optional[int] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = None

class LandingPageUpdate(BaseModel):
    """Modelo para actualizar una landing page"""
    title: Optional[str] = None
    description: Optional[str] = None
    template_id: Optional[int] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = None
    is_active: Optional[bool] = None

class TemplateCreate(BaseModel):
    """Modelo para crear un nuevo template"""
    name: str
    description: Optional[str] = None
    category: str
    html_content: str
    css_content: Optional[str] = None
    js_content: Optional[str] = None

class LandingGenerateRequest(BaseModel):
    """Modelo para generar landing page con IA"""
    keywords: str
    phone_number: str
    ai_provider: Optional[str] = "openai"
    theme_category: Optional[str] = "general"

# ============================================================================
# ENDPOINTS PARA CREADOR DE LANDING PAGES
# ============================================================================

@router.get("/creador/templates", response_model=None)
async def get_templates(
    category: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene la lista de templates disponibles para crear landing pages
    """
    try:
        # Placeholder - implementar cuando se creen los modelos de templates
        return {
            "success": True,
            "message": "Templates endpoint - En desarrollo",
            "templates": [],
            "total": 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener templates: {str(e)}"
        )

@router.post("/creador/landing-pages", response_model=None)
async def create_landing_page(
    landing_data: LandingPageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crea una nueva landing page
    """
    try:
        # Placeholder - implementar cuando se creen los modelos de landing pages
        return {
            "success": True,
            "message": "Landing page creada exitosamente - En desarrollo",
            "landing_page_id": None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear landing page: {str(e)}"
        )

@router.post("/creador/generate", response_model=None)
async def generate_landing_page_with_ai(
    request: LandingGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Genera una landing page completa optimizada usando IA
    
    Crea una landing page ultra-optimizada para SEO con:
    - Título principal atractivo con keywords
    - Pregunta que genere interés
    - Texto introductorio persuasivo
    - Lista de beneficios/servicios
    - Llamadas a la acción
    - Sección "Quién soy"
    - Habilidades
    - Testimonios
    - Botón de WhatsApp fijo
    - Pie de página optimizado
    """
    try:
        # Validar entrada
        if not request.keywords.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Las palabras clave son requeridas"
            )
        
        if not request.phone_number.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El número de teléfono es requerido"
            )
        
        # Inicializar generador
        generator = LandingPageGenerator(db, current_user)
        
        # Generar landing page
        result = await generator.generate_landing_page(
            keywords=request.keywords,
            phone_number=request.phone_number,
            ai_provider=request.ai_provider,
            theme_category=request.theme_category
        )
        
        return {
            "success": True,
            "message": "Landing page generada exitosamente",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar landing page: {str(e)}"
        )

@router.get("/creador/landing-pages", response_model=None)
async def get_user_landing_pages(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene las landing pages del usuario actual
    """
    try:
        from app.services.landing_service import LandingPageService
        
        service = LandingPageService(db)
        landing_pages = service.get_landing_pages_by_user(
            user_id=current_user.id,
            skip=offset,
            limit=limit
        )
        
        # Convertir a formato de respuesta
        landing_pages_data = []
        for lp in landing_pages:
            landing_pages_data.append({
                "id": lp.id,
                "title": lp.title,
                "slug": lp.slug,
                "description": lp.description,
                "is_published": lp.is_published,
                "is_active": lp.is_active,
                "created_at": lp.created_at.isoformat() if lp.created_at else None,
                "published_at": lp.published_at.isoformat() if lp.published_at else None,
                "seo_title": lp.seo_title,
                "seo_description": lp.seo_description,
                "preview_url": f"/landing/{lp.slug}"
            })
        
        return {
            "success": True,
            "message": "Landing pages obtenidas exitosamente",
            "landing_pages": landing_pages_data,
            "total": len(landing_pages_data),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener landing pages: {str(e)}"
        )

@router.get("/creador/landing-pages/{landing_id}", response_model=None)
async def get_landing_page_details(
    landing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene los detalles completos de una landing page específica
    """
    try:
        from app.services.landing_service import LandingPageService
        
        service = LandingPageService(db)
        landing_page = service.get_landing_page(landing_id, current_user.id)
        
        return {
            "success": True,
            "message": "Landing page obtenida exitosamente",
            "landing_page": {
                "id": landing_page.id,
                "title": landing_page.title,
                "slug": landing_page.slug,
                "description": landing_page.description,
                "html_content": landing_page.html_content,
                "css_content": landing_page.css_content,
                "js_content": landing_page.js_content,
                "seo_title": landing_page.seo_title,
                "seo_description": landing_page.seo_description,
                "seo_keywords": landing_page.seo_keywords,
                "is_published": landing_page.is_published,
                "is_active": landing_page.is_active,
                "created_at": landing_page.created_at.isoformat() if landing_page.created_at else None,
                "published_at": landing_page.published_at.isoformat() if landing_page.published_at else None,
                "settings": landing_page.settings,
                "preview_url": f"/landing/{landing_page.slug}",
                "edit_url": f"/landings/creador/edit/{landing_page.id}"
            }
        }
    except Exception as e:
        if "no encontrada" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Landing page no encontrada"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener landing page: {str(e)}"
        )

@router.put("/creador/landing-pages/{landing_id}", response_model=None)
async def update_landing_page(
    landing_id: int,
    update_data: LandingPageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Actualiza una landing page
    """
    try:
        from app.services.landing_service import LandingPageService
        
        service = LandingPageService(db)
        
        # Convertir a diccionario excluyendo valores None
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        
        landing_page = service.update_landing_page(landing_id, current_user.id, update_dict)
        
        return {
            "success": True,
            "message": "Landing page actualizada exitosamente",
            "landing_page": {
                "id": landing_page.id,
                "title": landing_page.title,
                "slug": landing_page.slug,
                "seo_description": landing_page.seo_description,
                "seo_title": landing_page.seo_title,
                "seo_keywords": landing_page.seo_keywords,
                "is_active": landing_page.is_active,
                "is_published": landing_page.is_published
            }
        }
    except Exception as e:
        if "no encontrada" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Landing page no encontrada"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar landing page: {str(e)}"
        )

@router.put("/creador/landing-pages/{landing_id}/publish", response_model=None)
async def publish_landing_page(
    landing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Publica una landing page
    """
    try:
        from app.services.landing_service import LandingPageService
        
        service = LandingPageService(db)
        landing_page = service.publish_landing_page(landing_id, current_user.id)
        
        return {
            "success": True,
            "message": "Landing page publicada exitosamente",
            "landing_page": {
                "id": landing_page.id,
                "title": landing_page.title,
                "slug": landing_page.slug,
                "is_published": landing_page.is_published,
                "published_at": landing_page.published_at.isoformat() if landing_page.published_at else None,
                "public_url": f"/landing/{landing_page.slug}"
            }
        }
    except Exception as e:
        if "no encontrada" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Landing page no encontrada"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al publicar landing page: {str(e)}"
        )

@router.put("/creador/landing-pages/{landing_id}/unpublish", response_model=None)
async def unpublish_landing_page(
    landing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Despublica una landing page
    """
    try:
        from app.services.landing_service import LandingPageService
        
        service = LandingPageService(db)
        landing_page = service.unpublish_landing_page(landing_id, current_user.id)
        
        return {
            "success": True,
            "message": "Landing page despublicada exitosamente",
            "landing_page": {
                "id": landing_page.id,
                "title": landing_page.title,
                "slug": landing_page.slug,
                "is_published": landing_page.is_published
            }
        }
    except Exception as e:
        if "no encontrada" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Landing page no encontrada"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al despublicar landing page: {str(e)}"
        )

@router.delete("/creador/landing-pages/{landing_id}", response_model=None)
async def delete_landing_page(
    landing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Elimina una landing page
    """
    try:
        from app.services.landing_service import LandingPageService
        
        service = LandingPageService(db)
        success = service.delete_landing_page(landing_id, current_user.id)
        
        if success:
            return {
                "success": True,
                "message": "Landing page eliminada exitosamente"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar landing page"
            )
    except Exception as e:
        if "no encontrada" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Landing page no encontrada"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar landing page: {str(e)}"
        )

# ============================================================================
# ENDPOINTS PARA OPTIMIZACIÓN SEO
# ============================================================================

@router.get("/seo/analysis/{landing_page_id}", response_model=None)
async def analyze_seo(
    landing_page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Analiza el SEO de una landing page específica
    """
    try:
        # Placeholder - implementar análisis SEO
        return {
            "success": True,
            "message": "Análisis SEO - En desarrollo",
            "seo_score": 0,
            "recommendations": [],
            "issues": []
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al analizar SEO: {str(e)}"
        )

@router.post("/seo/optimize/{landing_page_id}", response_model=None)
async def optimize_seo(
    landing_page_id: int,
    seo_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Aplica optimizaciones SEO a una landing page
    """
    try:
        # Placeholder - implementar optimización SEO
        return {
            "success": True,
            "message": "Optimización SEO aplicada - En desarrollo",
            "changes_applied": []
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al optimizar SEO: {str(e)}"
        )

@router.get("/seo/keywords/suggestions", response_model=None)
async def get_keyword_suggestions(
    topic: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene sugerencias de keywords para SEO
    """
    try:
        # Placeholder - implementar sugerencias de keywords
        return {
            "success": True,
            "message": "Sugerencias de keywords - En desarrollo",
            "keywords": [],
            "topic": topic
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener sugerencias: {str(e)}"
        )

# ============================================================================
# ENDPOINTS PARA TEMAS Y PLANTILLAS
# ============================================================================

@router.get("/temas/categories", response_model=None)
async def get_theme_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene las categorías de temas disponibles
    """
    try:
        # Placeholder - implementar categorías de temas
        return {
            "success": True,
            "message": "Categorías de temas - En desarrollo",
            "categories": [
                {"id": 1, "name": "Negocios", "count": 0},
                {"id": 2, "name": "E-commerce", "count": 0},
                {"id": 3, "name": "Portafolio", "count": 0},
                {"id": 4, "name": "Blog", "count": 0},
                {"id": 5, "name": "Eventos", "count": 0}
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener categorías: {str(e)}"
        )

@router.get("/temas/templates", response_model=None)
async def get_theme_templates(
    category_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene los templates de temas disponibles
    """
    try:
        # Placeholder - implementar templates de temas
        return {
            "success": True,
            "message": "Templates de temas - En desarrollo",
            "templates": [],
            "total": 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener templates: {str(e)}"
        )

@router.post("/temas/customize", response_model=None)
async def customize_theme(
    template_id: int,
    customizations: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Personaliza un tema con configuraciones específicas
    """
    try:
        # Placeholder - implementar personalización de temas
        return {
            "success": True,
            "message": "Tema personalizado - En desarrollo",
            "customized_template_id": None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al personalizar tema: {str(e)}"
        )

# ============================================================================
# ENDPOINTS GENERALES
# ============================================================================

@router.get("/dashboard", response_model=None)
async def get_landings_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene estadísticas generales del dashboard de landings
    """
    try:
        # Placeholder - implementar dashboard de landings
        return {
            "success": True,
            "message": "Dashboard de Landings - En desarrollo",
            "stats": {
                "total_landing_pages": 0,
                "active_landing_pages": 0,
                "total_visits": 0,
                "conversion_rate": 0.0
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener dashboard: {str(e)}"
        )
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

# ============================================================================
# ENUMS Y TIPOS
# ============================================================================

class LandingStatus(str, Enum):
    """Estados de una landing page"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class TemplateCategory(str, Enum):
    """Categorías de templates"""
    BUSINESS = "business"
    ECOMMERCE = "ecommerce"
    PORTFOLIO = "portfolio"
    BLOG = "blog"
    LANDING = "landing"
    CORPORATE = "corporate"
    CREATIVE = "creative"
    EDUCATION = "education"
    HEALTH = "health"
    TECHNOLOGY = "technology"

class DifficultyLevel(str, Enum):
    """Niveles de dificultad para templates"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

# ============================================================================
# ESQUEMAS BASE PARA LANDING PAGES
# ============================================================================

class LandingPageBase(BaseModel):
    """Esquema base para landing pages"""
    title: str = Field(..., min_length=1, max_length=200, description="Título de la landing page")
    description: Optional[str] = Field(None, max_length=500, description="Descripción de la landing page")
    html_content: Optional[str] = Field(None, description="Contenido HTML de la landing page")
    css_content: Optional[str] = Field(None, description="CSS personalizado")
    js_content: Optional[str] = Field(None, description="JavaScript personalizado")
    seo_title: Optional[str] = Field(None, max_length=60, description="Título SEO (máx 60 caracteres)")
    seo_description: Optional[str] = Field(None, max_length=160, description="Meta descripción SEO (máx 160 caracteres)")
    seo_keywords: Optional[str] = Field(None, max_length=500, description="Keywords SEO separadas por comas")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Configuraciones adicionales")
    is_active: bool = Field(True, description="Si la landing page está activa")
    is_published: bool = Field(False, description="Si la landing page está publicada")
    template_id: Optional[int] = Field(None, description="ID del template utilizado")

    @validator('seo_title')
    def validate_seo_title(cls, v):
        if v and len(v) > 60:
            raise ValueError('El título SEO no puede exceder 60 caracteres')
        return v

    @validator('seo_description')
    def validate_seo_description(cls, v):
        if v and len(v) > 160:
            raise ValueError('La meta descripción no puede exceder 160 caracteres')
        return v

class LandingPageCreate(LandingPageBase):
    """Esquema para crear una landing page"""
    pass

class LandingPageUpdate(BaseModel):
    """Esquema para actualizar una landing page"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    html_content: Optional[str] = None
    css_content: Optional[str] = None
    js_content: Optional[str] = None
    seo_title: Optional[str] = Field(None, max_length=60)
    seo_description: Optional[str] = Field(None, max_length=160)
    seo_keywords: Optional[str] = Field(None, max_length=500)
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_published: Optional[bool] = None
    template_id: Optional[int] = None

class LandingPage(LandingPageBase):
    """Esquema completo de una landing page"""
    id: int
    slug: str
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================================================
# ESQUEMAS PARA TEMPLATES
# ============================================================================

class LandingTemplateBase(BaseModel):
    """Esquema base para templates de landing pages"""
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del template")
    description: Optional[str] = Field(None, max_length=500, description="Descripción del template")
    category: TemplateCategory = Field(..., description="Categoría del template")
    html_template: str = Field(..., description="HTML base del template")
    css_template: Optional[str] = Field(None, description="CSS base del template")
    js_template: Optional[str] = Field(None, description="JavaScript base del template")
    preview_image: Optional[str] = Field(None, max_length=500, description="URL de imagen de preview")
    is_premium: bool = Field(False, description="Si es un template premium")
    is_active: bool = Field(True, description="Si el template está activo")
    customizable_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Campos personalizables")
    default_settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Configuraciones por defecto")
    tags: Optional[str] = Field(None, max_length=500, description="Tags separados por comas")
    difficulty_level: DifficultyLevel = Field(DifficultyLevel.BEGINNER, description="Nivel de dificultad")

class LandingTemplateCreate(LandingTemplateBase):
    """Esquema para crear un template"""
    pass

class LandingTemplateUpdate(BaseModel):
    """Esquema para actualizar un template"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[TemplateCategory] = None
    html_template: Optional[str] = None
    css_template: Optional[str] = None
    js_template: Optional[str] = None
    preview_image: Optional[str] = Field(None, max_length=500)
    is_premium: Optional[bool] = None
    is_active: Optional[bool] = None
    customizable_fields: Optional[Dict[str, Any]] = None
    default_settings: Optional[Dict[str, Any]] = None
    tags: Optional[str] = Field(None, max_length=500)
    difficulty_level: Optional[DifficultyLevel] = None

class LandingTemplate(LandingTemplateBase):
    """Esquema completo de un template"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================================================
# ESQUEMAS PARA SEO
# ============================================================================

class LandingSEOConfigBase(BaseModel):
    """Esquema base para configuración SEO"""
    meta_robots: str = Field("index,follow", max_length=100, description="Directivas para robots")
    canonical_url: Optional[str] = Field(None, max_length=500, description="URL canónica")
    og_title: Optional[str] = Field(None, max_length=60, description="Título Open Graph")
    og_description: Optional[str] = Field(None, max_length=160, description="Descripción Open Graph")
    og_image: Optional[str] = Field(None, max_length=500, description="Imagen Open Graph")
    og_type: str = Field("website", max_length=50, description="Tipo Open Graph")
    twitter_card: str = Field("summary_large_image", max_length=50, description="Tipo de Twitter Card")
    twitter_title: Optional[str] = Field(None, max_length=60, description="Título Twitter")
    twitter_description: Optional[str] = Field(None, max_length=160, description="Descripción Twitter")
    twitter_image: Optional[str] = Field(None, max_length=500, description="Imagen Twitter")
    schema_markup: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Schema.org markup")
    custom_head_tags: Optional[str] = Field(None, description="Tags HTML personalizados para <head>")

class LandingSEOConfigCreate(LandingSEOConfigBase):
    """Esquema para crear configuración SEO"""
    pass

class LandingSEOConfigUpdate(BaseModel):
    """Esquema para actualizar configuración SEO"""
    meta_robots: Optional[str] = Field(None, max_length=100)
    canonical_url: Optional[str] = Field(None, max_length=500)
    og_title: Optional[str] = Field(None, max_length=60)
    og_description: Optional[str] = Field(None, max_length=160)
    og_image: Optional[str] = Field(None, max_length=500)
    og_type: Optional[str] = Field(None, max_length=50)
    twitter_card: Optional[str] = Field(None, max_length=50)
    twitter_title: Optional[str] = Field(None, max_length=60)
    twitter_description: Optional[str] = Field(None, max_length=160)
    twitter_image: Optional[str] = Field(None, max_length=500)
    schema_markup: Optional[Dict[str, Any]] = None
    custom_head_tags: Optional[str] = None

class LandingSEOConfig(LandingSEOConfigBase):
    """Esquema completo de configuración SEO"""
    id: int
    landing_page_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================================================
# ESQUEMAS PARA ANALYTICS
# ============================================================================

class LandingAnalyticsBase(BaseModel):
    """Esquema base para analytics"""
    page_views: int = Field(0, ge=0, description="Número de vistas de página")
    unique_visitors: int = Field(0, ge=0, description="Visitantes únicos")
    bounce_rate: int = Field(0, ge=0, le=100, description="Tasa de rebote (0-100)")
    avg_time_on_page: int = Field(0, ge=0, description="Tiempo promedio en página (segundos)")
    conversions: int = Field(0, ge=0, description="Número de conversiones")
    conversion_rate: int = Field(0, ge=0, le=100, description="Tasa de conversión (0-100)")
    traffic_sources: Optional[Dict[str, int]] = Field(default_factory=dict, description="Fuentes de tráfico")
    device_types: Optional[Dict[str, int]] = Field(default_factory=dict, description="Tipos de dispositivos")
    browser_stats: Optional[Dict[str, int]] = Field(default_factory=dict, description="Estadísticas de navegadores")
    date: datetime = Field(..., description="Fecha de las métricas")

class LandingAnalyticsCreate(LandingAnalyticsBase):
    """Esquema para crear analytics"""
    landing_page_id: int = Field(..., description="ID de la landing page")

class LandingAnalytics(LandingAnalyticsBase):
    """Esquema completo de analytics"""
    id: int
    landing_page_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================================================
# ESQUEMAS DE RESPUESTA
# ============================================================================

class LandingPageWithTemplate(LandingPage):
    """Landing page con información del template"""
    template: Optional[LandingTemplate] = None

class LandingPageWithAnalytics(LandingPage):
    """Landing page con analytics"""
    analytics_summary: Optional[Dict[str, Any]] = None

class LandingPageFull(LandingPage):
    """Landing page con toda la información relacionada"""
    template: Optional[LandingTemplate] = None
    seo_config: Optional[LandingSEOConfig] = None
    analytics_summary: Optional[Dict[str, Any]] = None

class LandingPageList(BaseModel):
    """Lista paginada de landing pages"""
    items: List[LandingPage]
    total: int
    page: int
    per_page: int
    pages: int

class TemplateList(BaseModel):
    """Lista de templates"""
    items: List[LandingTemplate]
    total: int

class SEOAnalysis(BaseModel):
    """Resultado del análisis SEO"""
    score: int = Field(..., ge=0, le=100, description="Puntuación SEO (0-100)")
    recommendations: List[str] = Field(..., description="Lista de recomendaciones")
    analysis_date: str = Field(..., description="Fecha del análisis")

class AnalyticsSummary(BaseModel):
    """Resumen de analytics"""
    total_views: int
    total_visitors: int
    avg_bounce_rate: float
    period_days: int
    daily_data: List[Dict[str, Any]]

# ============================================================================
# ESQUEMAS PARA RESPUESTAS DE API
# ============================================================================

class LandingResponse(BaseModel):
    """Respuesta estándar para operaciones de landing pages"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    """Respuesta de error"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
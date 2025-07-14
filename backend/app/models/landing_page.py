from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# ============================================================================
# MODELO PARA LANDING PAGES
# ============================================================================

class LandingPage(Base):
    """
    Modelo para almacenar landing pages creadas por los usuarios
    """
    __tablename__ = "landing_pages"

    # Campos principales
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    slug = Column(String(250), unique=True, index=True)  # URL amigable
    description = Column(Text, nullable=True)
    
    # Contenido de la landing page
    html_content = Column(Text, nullable=True)  # HTML generado
    css_content = Column(Text, nullable=True)   # CSS personalizado
    js_content = Column(Text, nullable=True)    # JavaScript personalizado
    
    # Configuración SEO
    seo_title = Column(String(60), nullable=True)        # Título SEO (max 60 chars)
    seo_description = Column(String(160), nullable=True) # Meta description (max 160 chars)
    seo_keywords = Column(String(500), nullable=True)    # Keywords separadas por comas
    
    # Estado y configuración
    is_active = Column(Boolean, default=True, index=True)
    is_published = Column(Boolean, default=False, index=True)
    
    # Configuraciones adicionales (JSON)
    settings = Column(JSON, nullable=True)  # Configuraciones específicas de la landing
    
    # Relaciones
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("landing_templates.id"), nullable=True)
    theme_id = Column(Integer, ForeignKey("themes.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones ORM
    user = relationship("User", back_populates="landing_pages")
    template = relationship("LandingTemplate", back_populates="landing_pages")
    theme = relationship("Theme", back_populates="landing_pages")
    analytics = relationship("LandingAnalytics", back_populates="landing_page", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<LandingPage(id={self.id}, title='{self.title}', user_id={self.user_id})>"

# ============================================================================
# MODELO PARA TEMPLATES DE LANDING PAGES
# ============================================================================

class LandingTemplate(Base):
    """
    Modelo para almacenar templates/plantillas de landing pages
    """
    __tablename__ = "landing_templates"

    # Campos principales
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)  # business, ecommerce, portfolio, etc.
    
    # Contenido del template
    html_template = Column(Text, nullable=False)  # HTML base del template
    css_template = Column(Text, nullable=True)    # CSS base del template
    js_template = Column(Text, nullable=True)     # JavaScript base del template
    
    # Configuración del template
    preview_image = Column(String(500), nullable=True)  # URL de imagen de preview
    is_premium = Column(Boolean, default=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Configuraciones personalizables (JSON)
    customizable_fields = Column(JSON, nullable=True)  # Campos que se pueden personalizar
    default_settings = Column(JSON, nullable=True)     # Configuraciones por defecto
    
    # Metadatos
    tags = Column(String(500), nullable=True)  # Tags separados por comas
    difficulty_level = Column(String(20), default="beginner")  # beginner, intermediate, advanced
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones ORM
    landing_pages = relationship("LandingPage", back_populates="template")
    
    def __repr__(self):
        return f"<LandingTemplate(id={self.id}, name='{self.name}', category='{self.category}')>"

# ============================================================================
# MODELO PARA ANALYTICS DE LANDING PAGES
# ============================================================================

class LandingAnalytics(Base):
    """
    Modelo para almacenar analytics y métricas de landing pages
    """
    __tablename__ = "landing_analytics"

    # Campos principales
    id = Column(Integer, primary_key=True, index=True)
    
    # Métricas básicas
    page_views = Column(Integer, default=0, index=True)
    unique_visitors = Column(Integer, default=0)
    bounce_rate = Column(Integer, default=0)  # Porcentaje (0-100)
    avg_time_on_page = Column(Integer, default=0)  # Segundos
    
    # Métricas de conversión
    conversions = Column(Integer, default=0)
    conversion_rate = Column(Integer, default=0)  # Porcentaje (0-100)
    
    # Datos de tráfico
    traffic_sources = Column(JSON, nullable=True)  # Fuentes de tráfico
    device_types = Column(JSON, nullable=True)     # Tipos de dispositivos
    browser_stats = Column(JSON, nullable=True)    # Estadísticas de navegadores
    
    # Fecha de las métricas
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Relaciones
    landing_page_id = Column(Integer, ForeignKey("landing_pages.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones ORM
    landing_page = relationship("LandingPage", back_populates="analytics")
    
    def __repr__(self):
        return f"<LandingAnalytics(id={self.id}, landing_page_id={self.landing_page_id}, date={self.date})>"

# ============================================================================
# MODELO PARA CONFIGURACIONES SEO
# ============================================================================

class LandingSEOConfig(Base):
    """
    Modelo para almacenar configuraciones SEO específicas de landing pages
    """
    __tablename__ = "landing_seo_configs"

    # Campos principales
    id = Column(Integer, primary_key=True, index=True)
    
    # Configuraciones SEO avanzadas
    meta_robots = Column(String(100), default="index,follow")
    canonical_url = Column(String(500), nullable=True)
    og_title = Column(String(60), nullable=True)        # Open Graph title
    og_description = Column(String(160), nullable=True) # Open Graph description
    og_image = Column(String(500), nullable=True)       # Open Graph image
    og_type = Column(String(50), default="website")     # Open Graph type
    
    # Twitter Cards
    twitter_card = Column(String(50), default="summary_large_image")
    twitter_title = Column(String(60), nullable=True)
    twitter_description = Column(String(160), nullable=True)
    twitter_image = Column(String(500), nullable=True)
    
    # Schema.org structured data
    schema_markup = Column(JSON, nullable=True)
    
    # Configuraciones adicionales
    custom_head_tags = Column(Text, nullable=True)  # Tags HTML personalizados para <head>
    
    # Relaciones
    landing_page_id = Column(Integer, ForeignKey("landing_pages.id"), nullable=False, unique=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones ORM
    landing_page = relationship("LandingPage", uselist=False)
    
    def __repr__(self):
        return f"<LandingSEOConfig(id={self.id}, landing_page_id={self.landing_page_id})>"
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
from .tag import content_tags
import enum

class ContentStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    GENERATING = "generating"
    FAILED = "failed"

class Content(Base):
    __tablename__ = "content"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(300), unique=True, nullable=False, index=True)  # URL amigable
    content = Column(Text, nullable=False)
    excerpt = Column(Text)  # Resumen del contenido
    
    # Campos SEO
    meta_title = Column(String(60))  # Título SEO optimizado
    meta_description = Column(String(160))
    focus_keyword = Column(String(100))  # Palabra clave principal
    canonical_url = Column(String(500))  # URL canónica
    
    # Campos para Schema.org
    author_name = Column(String(100))  # Nombre del autor para Schema.org
    publisher_name = Column(String(100), default="Consultas Esotéricas Latam")  # Nombre del publisher
    featured_image_url = Column(String(500))  # URL de imagen destacada
    featured_image_alt = Column(String(255))  # Alt text de imagen destacada
    featured_image_caption = Column(Text)  # Caption de imagen destacada
    article_section = Column(String(100))  # Sección del artículo para Schema.org
    schema_type = Column(String(50), default="Article")  # Tipo de Schema.org
    
    # Configuración de contenido
    content_type = Column(String(50), default="post")
    word_count = Column(Integer)
    reading_time = Column(Integer)  # Tiempo de lectura estimado en minutos
    status = Column(Enum(ContentStatus), default=ContentStatus.DRAFT)
    
    # Configuración de publicación
    is_featured = Column(Boolean, default=False)
    allow_comments = Column(Boolean, default=True)
    is_indexed = Column(Boolean, default=True)  # Si debe ser indexado por buscadores
    
    # Relaciones
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    category_id = Column(Integer, ForeignKey("categories.id"))
    
    # Fechas
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)
    scheduled_at = Column(DateTime)  # Para contenido programado
    
    # Relaciones
    keyword = relationship("Keyword", back_populates="content_items")
    user = relationship("User", back_populates="content_items")
    category = relationship("Category", back_populates="content_items")
    tags = relationship("Tag", secondary=content_tags, back_populates="content_items")
    images = relationship("ContentImage", back_populates="content")
    seo_schemas = relationship("SEOSchema", back_populates="content")
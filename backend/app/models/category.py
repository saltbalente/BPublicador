from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Category(Base):
    """Modelo para categorías de contenido"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(Text)
    parent_id = Column(Integer, nullable=True)  # Para categorías jerárquicas
    is_active = Column(Boolean, default=True)
    seo_title = Column(String(60))  # Título SEO optimizado
    seo_description = Column(String(160))  # Meta descripción
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    content_items = relationship("Content", back_populates="category")
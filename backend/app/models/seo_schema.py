from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class SchemaType(str, enum.Enum):
    ARTICLE = "Article"
    BLOG_POSTING = "BlogPosting"
    NEWS_ARTICLE = "NewsArticle"
    HOW_TO = "HowTo"
    FAQ = "FAQPage"
    RECIPE = "Recipe"
    PRODUCT = "Product"
    ORGANIZATION = "Organization"
    PERSON = "Person"
    LOCAL_BUSINESS = "LocalBusiness"

class SEOSchema(Base):
    """Modelo para schemas SEO estructurados"""
    __tablename__ = "seo_schemas"
    
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("content.id"), nullable=False)
    schema_type = Column(SQLEnum(SchemaType), nullable=False)  # Tipo de schema
    schema_data = Column(JSON)  # Datos del schema en formato JSON
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    content = relationship("Content", back_populates="seo_schemas")
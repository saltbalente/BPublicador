from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Theme(Base):
    """Modelo para temas de landing pages"""
    __tablename__ = "themes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(150), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)  # esoteric, business, health, etc.
    
    # Estilos CSS del tema
    css_content = Column(Text, nullable=False)
    
    # Variables del tema (colores, fuentes, etc.)
    theme_variables = Column(JSON, default={})
    
    # Configuración adicional
    settings = Column(JSON, default={})
    
    # Estado del tema
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Metadatos
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones ORM
    landing_pages = relationship("LandingPage", back_populates="theme")
    
    def __repr__(self):
        return f"<Theme(id={self.id}, name='{self.name}', category='{self.category}')>"
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class ManualImage(Base):
    """Modelo para imágenes generadas manualmente"""
    __tablename__ = "manual_images"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=True)  # Opcional
    image_path = Column(String(500), nullable=False)
    alt_text = Column(String(255))
    prompt_used = Column(Text)  # Prompt usado para generar la imagen
    style = Column(String(50))  # Estilo usado
    size = Column(String(20))   # Tamaño usado
    quality = Column(String(20))  # Calidad usada
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="manual_images")
    keyword = relationship("Keyword", back_populates="manual_images")
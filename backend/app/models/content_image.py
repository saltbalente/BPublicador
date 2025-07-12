from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class ContentImage(Base):
    """Modelo para imágenes asociadas al contenido"""
    __tablename__ = "content_images"
    
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("content.id"), nullable=False)
    image_path = Column(String(500), nullable=False)
    alt_text = Column(String(255))
    prompt_used = Column(Text)  # Prompt usado para generar la imagen
    position = Column(Integer, default=1)  # Posición en el contenido (0 = imagen destacada)
    is_featured = Column(Boolean, default=False)  # Si es imagen destacada
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    content = relationship("Content", back_populates="images")
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base

class ImageStyle(str, enum.Enum):
    MYSTICAL = "mystical"
    ARTISTIC = "artistic"
    PHOTOREALISTIC = "photorealistic"
    WATERCOLOR = "watercolor"
    GOTHIC = "gothic"
    FANTASY = "fantasy"
    MINIMALIST = "minimalist"
    VINTAGE = "vintage"

class ImageQuality(str, enum.Enum):
    STANDARD = "standard"
    HD = "hd"

class ImageSize(str, enum.Enum):
    SMALL = "256x256"
    MEDIUM = "512x512"
    LARGE = "1024x1024"
    WIDE = "1792x1024"
    TALL = "1024x1792"

class ImagePlacement(str, enum.Enum):
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"
    SCATTERED = "scattered"

class ImageProvider(str, enum.Enum):
    GEMINI = "gemini"
    OPENAI = "openai"

class GeminiAspectRatio(str, enum.Enum):
    SQUARE = "1:1"
    HORIZONTAL = "16:9"
    VERTICAL = "9:16"
    CLASSIC = "4:3"
    PORTRAIT = "3:4"

class GeminiSafetyLevel(str, enum.Enum):
    BLOCK_MEDIUM_AND_ABOVE = "BLOCK_MEDIUM_AND_ABOVE"
    BLOCK_ONLY_HIGH = "BLOCK_ONLY_HIGH"
    BLOCK_LOW_AND_ABOVE = "BLOCK_LOW_AND_ABOVE"

class ImageConfig(Base):
    """Modelo para configuración de generación de imágenes"""
    __tablename__ = "image_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=True)  # NULL = configuración global
    
    # Configuración global
    num_images = Column(Integer, default=2)  # Número de imágenes por contenido
    image_size = Column(SQLEnum(ImageSize), default=ImageSize.LARGE)
    image_quality = Column(SQLEnum(ImageQuality), default=ImageQuality.STANDARD)
    image_placement = Column(SQLEnum(ImagePlacement), default=ImagePlacement.SCATTERED)
    style = Column(SQLEnum(ImageStyle), default=ImageStyle.MYSTICAL)
    auto_generate = Column(Boolean, default=True)  # Generación automática habilitada
    include_featured = Column(Boolean, default=True)  # Incluir imagen destacada
    
    # Configuración de proveedor
    image_provider = Column(SQLEnum(ImageProvider), default=ImageProvider.GEMINI)
    
    # Configuraciones específicas de Gemini
    gemini_aspect_ratio = Column(SQLEnum(GeminiAspectRatio), default=GeminiAspectRatio.SQUARE)
    gemini_safety_level = Column(SQLEnum(GeminiSafetyLevel), default=GeminiSafetyLevel.BLOCK_MEDIUM_AND_ABOVE)
    gemini_person_generation = Column(Boolean, default=True)
    
    # Configuración específica de keyword
    custom_prompt = Column(Text, nullable=True)  # Prompt personalizado para esta keyword
    custom_style = Column(SQLEnum(ImageStyle), nullable=True)  # Estilo específico
    custom_count = Column(Integer, nullable=True)  # Número específico de imágenes
    
    # Metadatos
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="image_configs")
    keyword = relationship("Keyword", back_populates="image_configs")
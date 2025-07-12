from sqlalchemy import Column, Integer, String, DateTime, Enum, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum

class KeywordStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class KeywordPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Keyword(Base):
    __tablename__ = "keywords"
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), unique=True, index=True, nullable=False)
    status = Column(Enum(KeywordStatus), default=KeywordStatus.PENDING)
    priority = Column(Enum(KeywordPriority), default=KeywordPriority.MEDIUM)
    search_volume = Column(Integer, default=0)
    difficulty = Column(Float, default=0.0)
    category = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    used_at = Column(DateTime)
    # Relaciones
    content_items = relationship("Content", back_populates="keyword")
    image_configs = relationship("ImageConfig", back_populates="keyword")
    manual_images = relationship("ManualImage", back_populates="keyword")
    # analytics = relationship("KeywordAnalytics", back_populates="keyword")
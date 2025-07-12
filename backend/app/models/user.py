from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    api_key_deepseek = Column(String(255))
    api_key_openai = Column(String(255))
    daily_limit = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Relaciones
    content_items = relationship("Content", back_populates="user")
    image_configs = relationship("ImageConfig", back_populates="user")
    manual_images = relationship("ManualImage", back_populates="user")
    # usage_stats = relationship("UsageStats", back_populates="user")
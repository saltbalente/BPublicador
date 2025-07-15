"""Database models for EBPublicador."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any

from api.core.database import Base


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Post(Base, TimestampMixin):
    """Content post model."""
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(Text)
    
    # SEO and metadata
    meta_title = Column(String(255))
    meta_description = Column(Text)
    keywords = Column(String(500))
    
    # Publishing
    status = Column(String(20), default="draft", index=True)  # draft, published, archived
    published_at = Column(DateTime(timezone=True))
    
    # Content type and theme
    content_type = Column(String(50), default="article", index=True)
    theme = Column(String(100), default="default")
    
    # AI generation metadata
    ai_generated = Column(Boolean, default=False)
    ai_model = Column(String(50))
    generation_prompt = Column(Text)
    
    # Analytics and engagement
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    
    # JSON fields for flexible data
    custom_fields = Column(JSON, default=dict)
    seo_data = Column(JSON, default=dict)
    
    # Relationships
    images = relationship("PostImage", back_populates="post", cascade="all, delete-orphan")
    tags = relationship("PostTag", back_populates="post", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Post(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    @property
    def is_published(self) -> bool:
        return self.status == "published" and self.published_at is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "content": self.content,
            "excerpt": self.excerpt,
            "status": self.status,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "content_type": self.content_type,
            "theme": self.theme,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "ai_generated": self.ai_generated,
            "custom_fields": self.custom_fields,
            "seo_data": self.seo_data
        }


class PostImage(Base, TimestampMixin):
    """Images associated with posts."""
    __tablename__ = "post_images"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    
    # Image info
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Image properties
    width = Column(Integer)
    height = Column(Integer)
    alt_text = Column(String(255))
    caption = Column(Text)
    
    # Image type and usage
    image_type = Column(String(50), default="content")  # featured, content, gallery, thumbnail
    is_featured = Column(Boolean, default=False)
    
    # AI generation info
    ai_generated = Column(Boolean, default=False)
    generation_prompt = Column(Text)
    ai_model = Column(String(50))
    
    # Cloud storage info
    cloud_url = Column(String(500))
    cloud_public_id = Column(String(255))
    
    # Relationships
    post = relationship("Post", back_populates="images")
    
    def __repr__(self):
        return f"<PostImage(id={self.id}, filename='{self.filename}', post_id={self.post_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "file_path": self.file_path,
            "alt_text": self.alt_text,
            "caption": self.caption,
            "image_type": self.image_type,
            "is_featured": self.is_featured,
            "ai_generated": self.ai_generated,
            "cloud_url": self.cloud_url,
            "width": self.width,
            "height": self.height,
            "file_size": self.file_size
        }


class PostTag(Base, TimestampMixin):
    """Tags for posts."""
    __tablename__ = "post_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(100), nullable=False, index=True)
    color = Column(String(7), default="#3B82F6")  # Hex color
    
    # Relationships
    post = relationship("Post", back_populates="tags")
    
    def __repr__(self):
        return f"<PostTag(id={self.id}, name='{self.name}', post_id={self.post_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "color": self.color
        }


class Theme(Base, TimestampMixin):
    """Website themes."""
    __tablename__ = "themes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(150), nullable=False)
    description = Column(Text)
    
    # Theme configuration
    config = Column(JSON, default=dict)
    css_variables = Column(JSON, default=dict)
    
    # Theme metadata
    version = Column(String(20), default="1.0.0")
    author = Column(String(100))
    preview_image = Column(String(500))
    
    # Status
    is_active = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Theme(id={self.id}, name='{self.name}', active={self.is_active})>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "config": self.config,
            "css_variables": self.css_variables,
            "version": self.version,
            "author": self.author,
            "preview_image": self.preview_image,
            "is_active": self.is_active,
            "is_default": self.is_default
        }


class GenerationHistory(Base, TimestampMixin):
    """History of AI content generation."""
    __tablename__ = "generation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Generation request
    prompt = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False)  # text, image, both
    ai_model = Column(String(50), nullable=False)
    
    # Generation result
    status = Column(String(20), default="pending")  # pending, completed, failed
    result_data = Column(JSON, default=dict)
    error_message = Column(Text)
    
    # Performance metrics
    generation_time = Column(Integer)  # milliseconds
    tokens_used = Column(Integer)
    cost_estimate = Column(String(20))
    
    # Associated content
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True, index=True)
    
    def __repr__(self):
        return f"<GenerationHistory(id={self.id}, type='{self.content_type}', status='{self.status}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "content_type": self.content_type,
            "ai_model": self.ai_model,
            "status": self.status,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "generation_time": self.generation_time,
            "tokens_used": self.tokens_used,
            "cost_estimate": self.cost_estimate,
            "created_at": self.created_at.isoformat()
        }


class Settings(Base, TimestampMixin):
    """Application settings."""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    description = Column(Text)
    category = Column(String(50), default="general", index=True)
    
    def __repr__(self):
        return f"<Settings(key='{self.key}', category='{self.category}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "category": self.category
        }


# Export all models
__all__ = [
    "Post",
    "PostImage", 
    "PostTag",
    "Theme",
    "GenerationHistory",
    "Settings",
    "TimestampMixin"
]
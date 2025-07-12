from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import re

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_active: bool = True
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('El nombre debe tener al menos 2 caracteres')
        return v.strip()
    
    @validator('seo_title')
    def validate_seo_title(cls, v):
        if v and len(v) > 60:
            raise ValueError('El título SEO no puede exceder 60 caracteres')
        return v
    
    @validator('seo_description')
    def validate_seo_description(cls, v):
        if v and len(v) > 160:
            raise ValueError('La descripción SEO no puede exceder 160 caracteres')
        return v

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    is_active: Optional[bool] = None

class Category(CategoryBase):
    id: int
    slug: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CategoryWithContent(Category):
    content_count: Optional[int] = 0
    
    class Config:
        from_attributes = True
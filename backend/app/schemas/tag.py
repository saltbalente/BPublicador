from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import re

class TagBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = "#007bff"
    is_active: bool = True
    
    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('El nombre debe tener al menos 2 caracteres')
        if len(v.strip()) > 50:
            raise ValueError('El nombre no puede exceder 50 caracteres')
        return v.strip().lower()
    
    @validator('color')
    def validate_color(cls, v):
        if not re.match(r'^#[0-9A-Fa-f]{6}$', v):
            raise ValueError('El color debe ser un código hexadecimal válido (ej: #007bff)')
        return v

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None

class Tag(TagBase):
    id: int
    slug: str
    usage_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TagWithContent(Tag):
    content_count: Optional[int] = 0
    
    class Config:
        from_attributes = True
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ThemeBase(BaseModel):
    """Esquema base para temas"""
    name: str = Field(..., min_length=1, max_length=100, description="Nombre único del tema")
    display_name: str = Field(..., min_length=1, max_length=150, description="Nombre para mostrar")
    description: Optional[str] = Field(None, description="Descripción del tema")
    category: str = Field(..., min_length=1, max_length=50, description="Categoría del tema")
    css_content: str = Field(..., min_length=1, description="Contenido CSS del tema")
    theme_variables: Optional[Dict[str, Any]] = Field(default={}, description="Variables del tema")
    settings: Optional[Dict[str, Any]] = Field(default={}, description="Configuraciones adicionales")
    is_active: Optional[bool] = Field(default=True, description="Si el tema está activo")
    is_default: Optional[bool] = Field(default=False, description="Si es el tema por defecto")

class ThemeCreate(ThemeBase):
    """Esquema para crear un tema"""
    pass

class ThemeUpdate(BaseModel):
    """Esquema para actualizar un tema"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    css_content: Optional[str] = Field(None, min_length=1)
    theme_variables: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None

class ThemeResponse(ThemeBase):
    """Esquema de respuesta para temas"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ThemeListResponse(BaseModel):
    """Esquema para lista de temas"""
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    category: str
    is_active: bool
    is_default: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ApplyThemeRequest(BaseModel):
    """Esquema para aplicar tema a landing page"""
    theme_id: int = Field(..., description="ID del tema a aplicar")
    landing_page_id: int = Field(..., description="ID de la landing page")
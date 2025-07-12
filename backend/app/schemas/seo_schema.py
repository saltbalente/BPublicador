from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class SchemaType(str, Enum):
    ARTICLE = "Article"
    BLOG_POSTING = "BlogPosting"
    NEWS_ARTICLE = "NewsArticle"
    HOW_TO = "HowTo"
    FAQ = "FAQPage"
    RECIPE = "Recipe"
    PRODUCT = "Product"
    ORGANIZATION = "Organization"
    PERSON = "Person"
    LOCAL_BUSINESS = "LocalBusiness"

class SEOSchemaBase(BaseModel):
    schema_type: str
    schema_data: Dict[str, Any]
    is_active: bool = True
    
    @validator('schema_type')
    def validate_schema_type(cls, v):
        valid_types = [e.value for e in SchemaType]
        if v not in valid_types:
            raise ValueError(f'Tipo de schema inválido. Debe ser uno de: {", ".join(valid_types)}')
        return v
    
    @validator('schema_data')
    def validate_schema_data(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Los datos del schema deben ser un objeto JSON válido')
        if '@type' not in v:
            raise ValueError('Los datos del schema deben incluir el campo @type')
        return v

class SEOSchemaCreate(SEOSchemaBase):
    content_id: int

class SEOSchemaUpdate(BaseModel):
    schema_type: Optional[str] = None
    schema_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class SEOSchema(SEOSchemaBase):
    id: int
    content_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Esquemas predefinidos para diferentes tipos de contenido
class ArticleSchema(BaseModel):
    headline: str
    description: str
    author: str
    datePublished: str
    dateModified: Optional[str] = None
    image: Optional[str] = None
    url: str
    
class BlogPostingSchema(BaseModel):
    headline: str
    description: str
    author: str
    datePublished: str
    dateModified: Optional[str] = None
    image: Optional[str] = None
    url: str
    wordCount: Optional[int] = None
    
class HowToSchema(BaseModel):
    name: str
    description: str
    image: Optional[str] = None
    totalTime: Optional[str] = None
    supply: Optional[List[str]] = None
    tool: Optional[List[str]] = None
    step: List[Dict[str, str]]
    
class FAQSchema(BaseModel):
    mainEntity: List[Dict[str, Any]]
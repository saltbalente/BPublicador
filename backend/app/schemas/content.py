from pydantic import BaseModel, validator
from typing import Optional, TYPE_CHECKING, List, Union
from datetime import datetime
from enum import Enum
import re

if TYPE_CHECKING:
    from .keyword import Keyword
    from .user import User
    from .category import Category
    from .tag import Tag
    from .seo_schema import SEOSchema

class ContentStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    REVIEW = "review"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    FAILED = "failed"

class ContentBase(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    
    # Campos SEO
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    focus_keyword: Optional[str] = None
    canonical_url: Optional[str] = None
    
    # Campos Schema.org
    author_name: Optional[str] = None
    publisher_name: Optional[str] = "Mi Sitio Web"
    featured_image_url: Optional[str] = None
    featured_image_alt: Optional[str] = None
    featured_image_caption: Optional[str] = None
    article_section: Optional[str] = None
    schema_type: Optional[str] = "Article"
    
    # Configuración
    status: ContentStatus = ContentStatus.DRAFT
    content_type: str = "post"
    template_theme: str = "default"
    is_featured: bool = False
    allow_comments: bool = True
    is_indexed: bool = True
    
    # Relaciones
    keyword_id: Optional[int] = None
    category_id: Optional[int] = None
    
    # Fechas
    scheduled_at: Optional[datetime] = None
    
    @validator('title')
    def validate_title(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('El título debe tener al menos 5 caracteres')
        if len(v) > 255:
            raise ValueError('El título no puede exceder 255 caracteres')
        return v.strip()
    
    @validator('meta_title')
    def validate_meta_title(cls, v):
        if v and len(v) > 60:
            raise ValueError('El meta título no puede exceder 60 caracteres')
        return v
    
    @validator('meta_description')
    def validate_meta_description(cls, v):
        if v and len(v) > 200:
            raise ValueError('La meta descripción no puede exceder 200 caracteres')
        return v
    
    @validator('canonical_url')
    def validate_canonical_url(cls, v):
        if v and not re.match(r'^https?://', v):
            raise ValueError('La URL canónica debe ser una URL válida')
        return v

class ContentCreate(BaseModel):
    title: str
    content: Optional[str] = ""
    excerpt: Optional[str] = None
    
    # Campos SEO
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    focus_keyword: Optional[str] = None
    canonical_url: Optional[str] = None
    
    # Campos Schema.org
    author_name: Optional[str] = None
    publisher_name: Optional[str] = "Mi Sitio Web"
    featured_image_url: Optional[str] = None
    featured_image_alt: Optional[str] = None
    featured_image_caption: Optional[str] = None
    article_section: Optional[str] = None
    schema_type: Optional[str] = "Article"
    
    # Configuración
    status: ContentStatus = ContentStatus.DRAFT
    content_type: str = "post"
    template_theme: str = "default"
    is_featured: bool = False
    allow_comments: bool = True
    is_indexed: bool = True
    
    # Relaciones
    keyword_id: Optional[int] = None
    category_id: Optional[Union[int, str]] = None  # Puede ser ID existente o nombre de nueva categoría
    tag_ids: Optional[List[int]] = []
    
    # Fechas
    scheduled_at: Optional[datetime] = None
    
    @validator('title')
    def validate_title(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('El título debe tener al menos 5 caracteres')
        if len(v) > 255:
            raise ValueError('El título no puede exceder 255 caracteres')
        return v.strip()
    
    @validator('meta_title')
    def validate_meta_title(cls, v):
        if v and len(v) > 60:
            raise ValueError('El meta título no puede exceder 60 caracteres')
        return v
    
    @validator('meta_description')
    def validate_meta_description(cls, v):
        if v and len(v) > 200:
            raise ValueError('La meta descripción no puede exceder 200 caracteres')
        return v
    
    @validator('canonical_url')
    def validate_canonical_url(cls, v):
        if v and not re.match(r'^https?://', v):
            raise ValueError('La URL canónica debe ser una URL válida')
        return v

class ContentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    
    # Campos SEO
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    focus_keyword: Optional[str] = None
    canonical_url: Optional[str] = None
    
    # Campos Schema.org
    author_name: Optional[str] = None
    publisher_name: Optional[str] = None
    featured_image_url: Optional[str] = None
    featured_image_alt: Optional[str] = None
    featured_image_caption: Optional[str] = None
    article_section: Optional[str] = None
    schema_type: Optional[str] = None
    
    # Configuración
    content_type: Optional[str] = None
    template_theme: Optional[str] = None
    status: Optional[ContentStatus] = None
    is_featured: Optional[bool] = None
    allow_comments: Optional[bool] = None
    is_indexed: Optional[bool] = None
    
    # Relaciones
    category_id: Optional[Union[int, str]] = None  # Puede ser ID existente o nombre de nueva categoría
    tag_ids: Optional[List[int]] = None
    
    # Fechas
    scheduled_at: Optional[datetime] = None
    
    @validator('category_id', pre=True)
    def validate_category_id(cls, v):
        # Convertir strings vacíos a None
        if v == '' or v == 'null' or v == 'undefined':
            return None
        # Si es un string que parece un número, convertirlo a int
        if isinstance(v, str) and v.isdigit():
            return int(v)
        return v
    
    @validator('meta_title', 'meta_description', 'focus_keyword', 'canonical_url', 
               'author_name', 'publisher_name', 'featured_image_url', 'featured_image_alt', 
               'featured_image_caption', 'article_section', 'schema_type', 'content_type', 
               'template_theme', 'excerpt', pre=True)
    def validate_string_fields(cls, v):
        # Convertir strings vacíos a None
        if v == '' or v == 'null' or v == 'undefined':
            return None
        return v
    
    @validator('title')
    def validate_title(cls, v):
        if v is not None and len(v.strip()) < 5:
            raise ValueError('El título debe tener al menos 5 caracteres')
        if v is not None and len(v) > 255:
            raise ValueError('El título no puede exceder 255 caracteres')
        return v.strip() if v else v
    
    @validator('meta_title')
    def validate_meta_title(cls, v):
        if v and len(v) > 60:
            raise ValueError('El meta título no puede exceder 60 caracteres')
        return v
    
    @validator('meta_description')
    def validate_meta_description(cls, v):
        if v and len(v) > 200:
            raise ValueError('La meta descripción no puede exceder 200 caracteres')
        return v
    
    @validator('canonical_url')
    def validate_canonical_url(cls, v):
        if v and not re.match(r'^https?://', v):
            raise ValueError('La URL canónica debe ser una URL válida')
        return v

class Content(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    excerpt: Optional[str] = None
    
    # Campos SEO
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    focus_keyword: Optional[str] = None
    canonical_url: Optional[str] = None
    
    # Campos Schema.org
    author_name: Optional[str] = None
    publisher_name: Optional[str] = "Mi Sitio Web"
    featured_image_url: Optional[str] = None
    featured_image_alt: Optional[str] = None
    featured_image_caption: Optional[str] = None
    article_section: Optional[str] = None
    schema_type: Optional[str] = "Article"
    
    # Configuración
    content_type: str = "post"
    template_theme: str = "default"
    status: ContentStatus = ContentStatus.DRAFT
    is_featured: bool = False
    allow_comments: bool = True
    is_indexed: bool = True
    
    # Relaciones
    keyword_id: Optional[int] = None
    category_id: Optional[int] = None
    
    # Fechas
    scheduled_at: Optional[datetime] = None
    
    word_count: Optional[int] = None
    reading_time: Optional[int] = None
    user_id: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ContentWithRelations(Content):
    keyword: Optional['Keyword'] = None
    user: Optional['User'] = None
    category: Optional['Category'] = None
    tags: Optional[List['Tag']] = []
    seo_schemas: Optional[List['SEOSchema']] = []
    
    class Config:
        from_attributes = True

class ContentWithKeyword(Content):
    keyword: Optional['Keyword'] = None
    
    class Config:
        from_attributes = True

class ContentWithUser(Content):
    user: Optional['User'] = None
    
    class Config:
        from_attributes = True

# Esquemas para el editor visual
class ContentBlock(BaseModel):
    type: str  # paragraph, heading, image, list, etc.
    content: str
    attributes: Optional[dict] = {}
    
class VisualContent(BaseModel):
    blocks: List[ContentBlock]
    
class ContentGenerationRequest(BaseModel):
    keyword_id: int
    content_type: str = "article"
    word_count: int = 800
    tone: str = "professional"
    include_images: bool = True
    seo_optimized: bool = True
    
class ContentPublishRequest(BaseModel):
    content_id: int
    publish_now: bool = True
    scheduled_at: Optional[datetime] = None
    update_sitemap: bool = True
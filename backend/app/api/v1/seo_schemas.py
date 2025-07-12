from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.api.dependencies import get_db, get_current_active_user
from app.models.seo_schema import SEOSchema as SEOSchemaModel
from app.models.content import Content as ContentModel
from app.schemas.seo_schema import (
    SEOSchema,
    SEOSchemaCreate,
    SEOSchemaUpdate,
    SchemaType,
    ArticleSchema,
    BlogPostingSchema,
    HowToSchema,
    FAQSchema
)
from app.schemas.user import User
import json
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=List[SEOSchema])
def get_seo_schemas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    schema_type: Optional[SchemaType] = None,
    content_id: Optional[int] = None,
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener lista de esquemas SEO"""
    query = db.query(SEOSchemaModel)
    
    if active_only:
        query = query.filter(SEOSchemaModel.is_active == True)
    
    if schema_type:
        query = query.filter(SEOSchemaModel.schema_type == schema_type)
    
    if content_id:
        query = query.filter(SEOSchemaModel.content_id == content_id)
    
    query = query.order_by(SEOSchemaModel.created_at.desc())
    schemas = query.offset(skip).limit(limit).all()
    
    return schemas

@router.get("/types", response_model=List[str])
def get_schema_types(
    current_user: User = Depends(get_current_active_user)
):
    """Obtener tipos de esquemas disponibles"""
    return [schema_type.value for schema_type in SchemaType]

@router.get("/templates/{schema_type}", response_model=Dict[str, Any])
def get_schema_template(
    schema_type: SchemaType,
    current_user: User = Depends(get_current_active_user)
):
    """Obtener plantilla de esquema por tipo"""
    templates = {
        SchemaType.ARTICLE: {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "",
            "description": "",
            "image": "",
            "author": {
                "@type": "Person",
                "name": ""
            },
            "publisher": {
                "@type": "Organization",
                "name": "",
                "logo": {
                    "@type": "ImageObject",
                    "url": ""
                }
            },
            "datePublished": "",
            "dateModified": ""
        },
        SchemaType.BLOG_POSTING: {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": "",
            "description": "",
            "image": "",
            "author": {
                "@type": "Person",
                "name": ""
            },
            "publisher": {
                "@type": "Organization",
                "name": ""
            },
            "datePublished": "",
            "dateModified": "",
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": ""
            }
        },
        SchemaType.HOW_TO: {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": "",
            "description": "",
            "image": "",
            "totalTime": "",
            "estimatedCost": {
                "@type": "MonetaryAmount",
                "currency": "USD",
                "value": "0"
            },
            "supply": [],
            "tool": [],
            "step": []
        },
        SchemaType.FAQ: {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": []
        },
        SchemaType.PRODUCT: {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "",
            "description": "",
            "image": "",
            "brand": {
                "@type": "Brand",
                "name": ""
            },
            "offers": {
                "@type": "Offer",
                "price": "",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock"
            }
        },
        SchemaType.RECIPE: {
            "@context": "https://schema.org",
            "@type": "Recipe",
            "name": "",
            "description": "",
            "image": "",
            "author": {
                "@type": "Person",
                "name": ""
            },
            "prepTime": "",
            "cookTime": "",
            "totalTime": "",
            "recipeYield": "",
            "recipeIngredient": [],
            "recipeInstructions": []
        },
        SchemaType.EVENT: {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": "",
            "description": "",
            "image": "",
            "startDate": "",
            "endDate": "",
            "location": {
                "@type": "Place",
                "name": "",
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": "",
                    "addressLocality": "",
                    "addressRegion": "",
                    "postalCode": "",
                    "addressCountry": ""
                }
            },
            "organizer": {
                "@type": "Organization",
                "name": ""
            }
        },
        SchemaType.ORGANIZATION: {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "",
            "description": "",
            "url": "",
            "logo": "",
            "contactPoint": {
                "@type": "ContactPoint",
                "telephone": "",
                "contactType": "customer service"
            },
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "",
                "addressLocality": "",
                "addressRegion": "",
                "postalCode": "",
                "addressCountry": ""
            }
        },
        SchemaType.LOCAL_BUSINESS: {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": "",
            "description": "",
            "image": "",
            "telephone": "",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "",
                "addressLocality": "",
                "addressRegion": "",
                "postalCode": "",
                "addressCountry": ""
            },
            "openingHours": [],
            "priceRange": ""
        }
    }
    
    return templates.get(schema_type, {})

@router.get("/{schema_id}", response_model=SEOSchema)
def get_seo_schema(
    schema_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener esquema SEO por ID"""
    schema = db.query(SEOSchemaModel).filter(SEOSchemaModel.id == schema_id).first()
    if not schema:
        raise HTTPException(status_code=404, detail="Esquema SEO no encontrado")
    
    return schema

@router.post("/", response_model=SEOSchema)
def create_seo_schema(
    schema: SEOSchemaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Crear nuevo esquema SEO"""
    # Verificar que el contenido existe
    content = db.query(ContentModel).filter(ContentModel.id == schema.content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    
    # Verificar que no existe otro esquema del mismo tipo para el mismo contenido
    existing = db.query(SEOSchemaModel).filter(
        SEOSchemaModel.content_id == schema.content_id,
        SEOSchemaModel.schema_type == schema.schema_type,
        SEOSchemaModel.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un esquema {schema.schema_type.value} activo para este contenido"
        )
    
    db_schema = SEOSchemaModel(
        content_id=schema.content_id,
        schema_type=schema.schema_type,
        schema_data=schema.schema_data,
        is_active=schema.is_active
    )
    
    db.add(db_schema)
    db.commit()
    db.refresh(db_schema)
    
    return db_schema

@router.put("/{schema_id}", response_model=SEOSchema)
def update_seo_schema(
    schema_id: int,
    schema_update: SEOSchemaUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar esquema SEO"""
    db_schema = db.query(SEOSchemaModel).filter(SEOSchemaModel.id == schema_id).first()
    if not db_schema:
        raise HTTPException(status_code=404, detail="Esquema SEO no encontrado")
    
    # Verificar unicidad si se cambia el tipo
    if schema_update.schema_type and schema_update.schema_type != db_schema.schema_type:
        existing = db.query(SEOSchemaModel).filter(
            SEOSchemaModel.content_id == db_schema.content_id,
            SEOSchemaModel.schema_type == schema_update.schema_type,
            SEOSchemaModel.is_active == True,
            SEOSchemaModel.id != schema_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe un esquema {schema_update.schema_type.value} activo para este contenido"
            )
    
    # Actualizar campos
    update_data = schema_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_schema, field, value)
    
    db_schema.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_schema)
    
    return db_schema

@router.delete("/{schema_id}", response_model=None)
def delete_seo_schema(
    schema_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Eliminar esquema SEO"""
    db_schema = db.query(SEOSchemaModel).filter(SEOSchemaModel.id == schema_id).first()
    if not db_schema:
        raise HTTPException(status_code=404, detail="Esquema SEO no encontrado")
    
    db.delete(db_schema)
    db.commit()
    
    return {"message": "Esquema SEO eliminado exitosamente"}

@router.post("/generate/{schema_type}", response_model=Dict[str, Any])
def generate_schema_from_content(
    schema_type: SchemaType,
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generar esquema automáticamente desde el contenido"""
    content = db.query(ContentModel).filter(ContentModel.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    
    # Obtener plantilla base
    template = get_schema_template(schema_type, current_user)
    
    # Rellenar automáticamente con datos del contenido
    if schema_type in [SchemaType.ARTICLE, SchemaType.BLOG_POSTING]:
        template.update({
            "headline": content.title,
            "description": content.meta_description or content.excerpt,
            "datePublished": content.created_at.isoformat() if content.created_at else "",
            "dateModified": content.updated_at.isoformat() if content.updated_at else "",
            "author": {
                "@type": "Person",
                "name": content.author.username if content.author else ""
            }
        })
        
        if content.featured_image:
            template["image"] = content.featured_image
    
    elif schema_type == SchemaType.FAQ:
        # Intentar extraer preguntas y respuestas del contenido
        # Esto es una implementación básica, se puede mejorar con IA
        template["mainEntity"] = [
            {
                "@type": "Question",
                "name": "Pregunta de ejemplo",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Respuesta de ejemplo"
                }
            }
        ]
    
    return template

@router.post("/validate", response_model=Dict[str, Any])
def validate_schema(
    schema_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """Validar esquema JSON-LD"""
    errors = []
    warnings = []
    
    # Validaciones básicas
    if "@context" not in schema_data:
        errors.append("Falta el campo @context")
    elif schema_data["@context"] != "https://schema.org":
        warnings.append("Se recomienda usar https://schema.org como @context")
    
    if "@type" not in schema_data:
        errors.append("Falta el campo @type")
    
    # Validaciones específicas por tipo
    schema_type = schema_data.get("@type")
    
    if schema_type in ["Article", "BlogPosting"]:
        required_fields = ["headline", "author", "datePublished"]
        for field in required_fields:
            if field not in schema_data or not schema_data[field]:
                errors.append(f"Campo requerido faltante: {field}")
    
    elif schema_type == "FAQPage":
        if "mainEntity" not in schema_data or not schema_data["mainEntity"]:
            errors.append("FAQPage debe tener al menos una pregunta en mainEntity")
    
    elif schema_type == "HowTo":
        required_fields = ["name", "step"]
        for field in required_fields:
            if field not in schema_data or not schema_data[field]:
                errors.append(f"Campo requerido faltante: {field}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

@router.get("/content/{content_id}", response_model=List[SEOSchema])
def get_schemas_by_content(
    content_id: int,
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener todos los esquemas de un contenido específico"""
    query = db.query(SEOSchemaModel).filter(SEOSchemaModel.content_id == content_id)
    
    if active_only:
        query = query.filter(SEOSchemaModel.is_active == True)
    
    schemas = query.order_by(SEOSchemaModel.created_at.desc()).all()
    return schemas
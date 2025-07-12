from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.dependencies import get_db, get_current_active_user
from app.models.category import Category as CategoryModel
from app.models.content import Content as ContentModel
from app.schemas.category import (
    Category,
    CategoryCreate,
    CategoryUpdate,
    CategoryWithContent
)
from app.schemas.user import User
import re

router = APIRouter()

def create_slug(name: str) -> str:
    """Crear slug a partir del nombre"""
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

@router.get("/", response_model=List[CategoryWithContent])
def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener lista de categorías"""
    query = db.query(CategoryModel)
    
    if active_only:
        query = query.filter(CategoryModel.is_active == True)
    
    categories = query.offset(skip).limit(limit).all()
    
    # Agregar conteo de contenido para cada categoría
    result = []
    for category in categories:
        content_count = db.query(ContentModel).filter(
            ContentModel.category_id == category.id
        ).count()
        
        category_dict = category.__dict__.copy()
        category_dict['content_count'] = content_count
        result.append(CategoryWithContent(**category_dict))
    
    return result

@router.get("/{category_id}", response_model=CategoryWithContent)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener categoría por ID"""
    category = db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    content_count = db.query(ContentModel).filter(
        ContentModel.category_id == category.id
    ).count()
    
    category_dict = category.__dict__.copy()
    category_dict['content_count'] = content_count
    
    return CategoryWithContent(**category_dict)

@router.post("/", response_model=Category)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Crear nueva categoría"""
    # Verificar que no existe una categoría con el mismo nombre
    existing = db.query(CategoryModel).filter(
        CategoryModel.name == category.name
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una categoría con ese nombre"
        )
    
    # Crear slug único
    base_slug = create_slug(category.name)
    slug = base_slug
    counter = 1
    while db.query(CategoryModel).filter(CategoryModel.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Verificar categoría padre si se especifica
    if category.parent_id:
        parent = db.query(CategoryModel).filter(
            CategoryModel.id == category.parent_id
        ).first()
        if not parent:
            raise HTTPException(
                status_code=404,
                detail="Categoría padre no encontrada"
            )
    
    db_category = CategoryModel(
        name=category.name,
        slug=slug,
        description=category.description,
        parent_id=category.parent_id,
        seo_title=category.seo_title,
        seo_description=category.seo_description,
        is_active=category.is_active
    )
    
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return db_category

@router.put("/{category_id}", response_model=Category)
def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar categoría"""
    db_category = db.query(CategoryModel).filter(
        CategoryModel.id == category_id
    ).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Verificar nombre único si se está actualizando
    if category_update.name and category_update.name != db_category.name:
        existing = db.query(CategoryModel).filter(
            CategoryModel.name == category_update.name,
            CategoryModel.id != category_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Ya existe una categoría con ese nombre"
            )
        
        # Actualizar slug
        new_slug = create_slug(category_update.name)
        counter = 1
        while db.query(CategoryModel).filter(
            CategoryModel.slug == new_slug,
            CategoryModel.id != category_id
        ).first():
            new_slug = f"{create_slug(category_update.name)}-{counter}"
            counter += 1
        db_category.slug = new_slug
    
    # Verificar categoría padre si se especifica
    if category_update.parent_id:
        if category_update.parent_id == category_id:
            raise HTTPException(
                status_code=400,
                detail="Una categoría no puede ser padre de sí misma"
            )
        parent = db.query(CategoryModel).filter(
            CategoryModel.id == category_update.parent_id
        ).first()
        if not parent:
            raise HTTPException(
                status_code=404,
                detail="Categoría padre no encontrada"
            )
    
    # Actualizar campos
    update_data = category_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)
    
    db.commit()
    db.refresh(db_category)
    
    return db_category

@router.delete("/{category_id}", response_model=None)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Eliminar categoría"""
    db_category = db.query(CategoryModel).filter(
        CategoryModel.id == category_id
    ).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Verificar si tiene contenido asociado
    content_count = db.query(ContentModel).filter(
        ContentModel.category_id == category_id
    ).count()
    
    if content_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar la categoría porque tiene {content_count} contenidos asociados"
        )
    
    # Verificar si tiene subcategorías
    subcategories = db.query(CategoryModel).filter(
        CategoryModel.parent_id == category_id
    ).count()
    
    if subcategories > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar la categoría porque tiene {subcategories} subcategorías"
        )
    
    db.delete(db_category)
    db.commit()
    
    return {"message": "Categoría eliminada exitosamente"}

@router.get("/slug/{slug}", response_model=CategoryWithContent)
def get_category_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener categoría por slug"""
    category = db.query(CategoryModel).filter(
        CategoryModel.slug == slug,
        CategoryModel.is_active == True
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    content_count = db.query(ContentModel).filter(
        ContentModel.category_id == category.id
    ).count()
    
    category_dict = category.__dict__.copy()
    category_dict['content_count'] = content_count
    
    return CategoryWithContent(**category_dict)
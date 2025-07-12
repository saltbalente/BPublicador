from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.dependencies import get_db, get_current_active_user
from app.models.tag import Tag as TagModel
from app.models.content import Content as ContentModel
from app.schemas.tag import (
    Tag,
    TagCreate,
    TagUpdate,
    TagWithContent
)
from app.schemas.user import User
import re

router = APIRouter()

def create_slug(name: str) -> str:
    """Crear slug a partir del nombre"""
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

@router.get("/", response_model=List[TagWithContent])
def get_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(True),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener lista de etiquetas"""
    query = db.query(TagModel)
    
    if active_only:
        query = query.filter(TagModel.is_active == True)
    
    if search:
        query = query.filter(TagModel.name.contains(search.lower()))
    
    # Ordenar por uso (más usadas primero)
    query = query.order_by(TagModel.usage_count.desc())
    
    tags = query.offset(skip).limit(limit).all()
    
    # Agregar conteo de contenido para cada etiqueta
    result = []
    for tag in tags:
        content_count = len(tag.content_items) if tag.content_items else 0
        
        tag_dict = tag.__dict__.copy()
        tag_dict['content_count'] = content_count
        result.append(TagWithContent(**tag_dict))
    
    return result

@router.get("/popular", response_model=List[TagWithContent])
def get_popular_tags(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener etiquetas más populares"""
    tags = db.query(TagModel).filter(
        TagModel.is_active == True,
        TagModel.usage_count > 0
    ).order_by(TagModel.usage_count.desc()).limit(limit).all()
    
    result = []
    for tag in tags:
        content_count = len(tag.content_items) if tag.content_items else 0
        tag_dict = tag.__dict__.copy()
        tag_dict['content_count'] = content_count
        result.append(TagWithContent(**tag_dict))
    
    return result

@router.get("/{tag_id}", response_model=TagWithContent)
def get_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener etiqueta por ID"""
    tag = db.query(TagModel).filter(TagModel.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Etiqueta no encontrada")
    
    content_count = len(tag.content_items) if tag.content_items else 0
    tag_dict = tag.__dict__.copy()
    tag_dict['content_count'] = content_count
    
    return TagWithContent(**tag_dict)

@router.post("/", response_model=Tag)
def create_tag(
    tag: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Crear nueva etiqueta"""
    # Verificar que no existe una etiqueta con el mismo nombre
    existing = db.query(TagModel).filter(
        TagModel.name == tag.name.lower()
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Ya existe una etiqueta con ese nombre"
        )
    
    # Crear slug único
    base_slug = create_slug(tag.name)
    slug = base_slug
    counter = 1
    while db.query(TagModel).filter(TagModel.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    db_tag = TagModel(
        name=tag.name.lower(),
        slug=slug,
        description=tag.description,
        color=tag.color,
        is_active=tag.is_active
    )
    
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    
    return db_tag

@router.post("/bulk", response_model=List[Tag])
def create_tags_bulk(
    tag_names: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Crear múltiples etiquetas de una vez"""
    created_tags = []
    
    for name in tag_names:
        name = name.strip().lower()
        if not name or len(name) < 2:
            continue
            
        # Verificar si ya existe
        existing = db.query(TagModel).filter(TagModel.name == name).first()
        if existing:
            created_tags.append(existing)
            continue
        
        # Crear slug único
        base_slug = create_slug(name)
        slug = base_slug
        counter = 1
        while db.query(TagModel).filter(TagModel.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        db_tag = TagModel(
            name=name,
            slug=slug,
            is_active=True
        )
        
        db.add(db_tag)
        created_tags.append(db_tag)
    
    db.commit()
    
    # Refrescar todos los objetos
    for tag in created_tags:
        if tag.id:  # Solo refrescar si tiene ID (fue creado)
            db.refresh(tag)
    
    return created_tags

@router.put("/{tag_id}", response_model=Tag)
def update_tag(
    tag_id: int,
    tag_update: TagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar etiqueta"""
    db_tag = db.query(TagModel).filter(TagModel.id == tag_id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="Etiqueta no encontrada")
    
    # Verificar nombre único si se está actualizando
    if tag_update.name and tag_update.name.lower() != db_tag.name:
        existing = db.query(TagModel).filter(
            TagModel.name == tag_update.name.lower(),
            TagModel.id != tag_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Ya existe una etiqueta con ese nombre"
            )
        
        # Actualizar slug
        new_slug = create_slug(tag_update.name)
        counter = 1
        while db.query(TagModel).filter(
            TagModel.slug == new_slug,
            TagModel.id != tag_id
        ).first():
            new_slug = f"{create_slug(tag_update.name)}-{counter}"
            counter += 1
        db_tag.slug = new_slug
        db_tag.name = tag_update.name.lower()
    
    # Actualizar otros campos
    update_data = tag_update.dict(exclude_unset=True, exclude={'name'})
    for field, value in update_data.items():
        setattr(db_tag, field, value)
    
    db.commit()
    db.refresh(db_tag)
    
    return db_tag

@router.delete("/{tag_id}", response_model=None)
def delete_tag(
    tag_id: int,
    force: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Eliminar etiqueta"""
    db_tag = db.query(TagModel).filter(TagModel.id == tag_id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="Etiqueta no encontrada")
    
    # Verificar si tiene contenido asociado
    content_count = len(db_tag.content_items) if db_tag.content_items else 0
    
    if content_count > 0 and not force:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar la etiqueta porque tiene {content_count} contenidos asociados. Use force=true para forzar la eliminación."
        )
    
    db.delete(db_tag)
    db.commit()
    
    return {"message": "Etiqueta eliminada exitosamente"}

@router.get("/slug/{slug}", response_model=TagWithContent)
def get_tag_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener etiqueta por slug"""
    tag = db.query(TagModel).filter(
        TagModel.slug == slug,
        TagModel.is_active == True
    ).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Etiqueta no encontrada")
    
    content_count = len(tag.content_items) if tag.content_items else 0
    tag_dict = tag.__dict__.copy()
    tag_dict['content_count'] = content_count
    
    return TagWithContent(**tag_dict)

@router.post("/search", response_model=List[Tag])
def search_tags(
    query: str,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Buscar etiquetas por nombre"""
    if len(query.strip()) < 2:
        return []
    
    tags = db.query(TagModel).filter(
        TagModel.name.contains(query.lower()),
        TagModel.is_active == True
    ).order_by(TagModel.usage_count.desc()).limit(limit).all()
    
    return tags
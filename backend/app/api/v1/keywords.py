from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.api.dependencies import get_db, get_current_active_user
from app.models.keyword import Keyword as KeywordModel
from app.models.content import Content as ContentModel
from app.schemas.keyword import Keyword, KeywordCreate, KeywordUpdate, KeywordWithContent
from app.schemas.user import User

router = APIRouter()

@router.post("/", response_model=Keyword)
def create_keyword(
    keyword: KeywordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Crear nueva palabra clave"""
    # Verificar si la palabra clave ya existe
    existing_keyword = db.query(KeywordModel).filter(
        KeywordModel.keyword == keyword.keyword
    ).first()
    
    if existing_keyword:
        raise HTTPException(
            status_code=400,
            detail="La palabra clave ya existe"
        )
    
    db_keyword = KeywordModel(**keyword.dict())
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    
    return db_keyword

@router.get("/", response_model=List[Keyword])
def read_keywords(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener lista de palabras clave"""
    keywords = db.query(KeywordModel).offset(skip).limit(limit).all()
    return keywords

@router.get("/{keyword_id}", response_model=KeywordWithContent)
def read_keyword(
    keyword_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener palabra clave por ID"""
    keyword = db.query(KeywordModel).filter(KeywordModel.id == keyword_id).first()
    if keyword is None:
        raise HTTPException(status_code=404, detail="Palabra clave no encontrada")
    return keyword

@router.put("/{keyword_id}", response_model=Keyword)
def update_keyword(
    keyword_id: int,
    keyword_update: KeywordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar palabra clave"""
    keyword = db.query(KeywordModel).filter(KeywordModel.id == keyword_id).first()
    if keyword is None:
        raise HTTPException(status_code=404, detail="Palabra clave no encontrada")
    
    update_data = keyword_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(keyword, field, value)
    
    # Actualizar timestamp
    from datetime import datetime
    keyword.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(keyword)
    
    return keyword

@router.delete("/{keyword_id}", response_model=None)
def delete_keyword(
    keyword_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Eliminar palabra clave"""
    keyword = db.query(KeywordModel).filter(KeywordModel.id == keyword_id).first()
    if keyword is None:
        raise HTTPException(status_code=404, detail="Palabra clave no encontrada")
    
    # Verificar si tiene contenido asociado
    if keyword.content_items:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar la palabra clave porque tiene contenido asociado"
        )
    
    db.delete(keyword)
    db.commit()
    
    return {"message": "Palabra clave eliminada exitosamente"}

@router.get("/search/{search_term}", response_model=List[Keyword])
def search_keywords(
    search_term: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Buscar palabras clave por término"""
    keywords = db.query(KeywordModel).filter(
        KeywordModel.keyword.contains(search_term)
    ).all()
    return keywords

@router.get("/status/{status}", response_model=List[Keyword])
def get_keywords_by_status(
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener palabras clave por estado"""
    keywords = db.query(KeywordModel).filter(KeywordModel.status == status).all()
    return keywords
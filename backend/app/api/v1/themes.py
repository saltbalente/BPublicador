from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.theme import Theme
from app.models.landing_page import LandingPage
from app.schemas.theme import (
    ThemeCreate, ThemeUpdate, ThemeResponse, ThemeListResponse, ApplyThemeRequest
)
from app.api.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[ThemeListResponse])
def get_themes(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener lista de temas disponibles"""
    try:
        query = db.query(Theme)
        
        if active_only:
            query = query.filter(Theme.is_active == True)
        
        if category:
            query = query.filter(Theme.category == category)
        
        themes = query.offset(skip).limit(limit).all()
        return themes
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener temas: {str(e)}"
        )

@router.get("/{theme_id}", response_model=ThemeResponse)
def get_theme(
    theme_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener un tema específico"""
    try:
        theme = db.query(Theme).filter(Theme.id == theme_id).first()
        
        if not theme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tema no encontrado"
            )
        
        return theme
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener tema: {str(e)}"
        )

@router.post("/", response_model=ThemeResponse)
def create_theme(
    theme_data: ThemeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Crear un nuevo tema (solo administradores)"""
    try:
        # Verificar si ya existe un tema con ese nombre
        existing_theme = db.query(Theme).filter(Theme.name == theme_data.name).first()
        if existing_theme:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un tema con ese nombre"
            )
        
        # Crear el tema
        theme = Theme(**theme_data.dict())
        db.add(theme)
        db.commit()
        db.refresh(theme)
        
        return theme
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear tema: {str(e)}"
        )

@router.put("/{theme_id}", response_model=ThemeResponse)
def update_theme(
    theme_id: int,
    theme_data: ThemeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar un tema existente"""
    try:
        theme = db.query(Theme).filter(Theme.id == theme_id).first()
        
        if not theme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tema no encontrado"
            )
        
        # Actualizar campos
        update_data = theme_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(theme, field, value)
        
        db.commit()
        db.refresh(theme)
        
        return theme
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar tema: {str(e)}"
        )

@router.delete("/{theme_id}")
def delete_theme(
    theme_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Eliminar un tema"""
    try:
        theme = db.query(Theme).filter(Theme.id == theme_id).first()
        
        if not theme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tema no encontrado"
            )
        
        # Verificar si hay landing pages usando este tema
        landing_pages_count = db.query(LandingPage).filter(LandingPage.theme_id == theme_id).count()
        if landing_pages_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede eliminar el tema. Está siendo usado por {landing_pages_count} landing page(s)"
            )
        
        db.delete(theme)
        db.commit()
        
        return {"message": "Tema eliminado exitosamente"}
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar tema: {str(e)}"
        )

@router.post("/apply")
def apply_theme_to_landing(
    apply_data: ApplyThemeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Aplicar un tema a una landing page"""
    try:
        # Verificar que la landing page existe y pertenece al usuario
        landing_page = db.query(LandingPage).filter(
            LandingPage.id == apply_data.landing_page_id,
            LandingPage.user_id == current_user.id
        ).first()
        
        if not landing_page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Landing page no encontrada"
            )
        
        # Verificar que el tema existe y está activo
        theme = db.query(Theme).filter(
            Theme.id == apply_data.theme_id,
            Theme.is_active == True
        ).first()
        
        if not theme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tema no encontrado o inactivo"
            )
        
        # Aplicar el tema
        landing_page.theme_id = apply_data.theme_id
        
        # Actualizar el HTML completo de la landing page con el CSS del tema
        if theme.css_content and landing_page.html_content:
            html_content = landing_page.html_content
            
            # Buscar si ya existe una etiqueta <style> en el HTML
            if '<style>' in html_content:
                # Reemplazar el contenido de la etiqueta style existente
                import re
                pattern = r'<style[^>]*>.*?</style>'
                new_style = f'<style>\n{theme.css_content}\n</style>'
                html_content = re.sub(pattern, new_style, html_content, flags=re.DOTALL)
            else:
                # Agregar la etiqueta style en el head
                if '<head>' in html_content:
                    head_end = html_content.find('</head>')
                    if head_end != -1:
                        style_tag = f'\n<style>\n{theme.css_content}\n</style>\n'
                        html_content = html_content[:head_end] + style_tag + html_content[head_end:]
                else:
                    # Si no hay head, agregar al inicio del body
                    if '<body>' in html_content:
                        body_start = html_content.find('<body>') + 6
                        style_tag = f'\n<style>\n{theme.css_content}\n</style>\n'
                        html_content = html_content[:body_start] + style_tag + html_content[body_start:]
            
            landing_page.html_content = html_content
        
        # También actualizar el CSS separado
        if theme.css_content:
            landing_page.css_content = theme.css_content
        
        db.commit()
        db.refresh(landing_page)
        
        return {
            "success": True,
            "message": "Tema aplicado exitosamente",
            "landing_page_id": landing_page.id,
            "theme_id": theme.id,
            "theme_name": theme.display_name
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al aplicar tema: {str(e)}"
        )

@router.get("/categories/")
def get_theme_categories(db: Session = Depends(get_db)):
    """Obtener categorías de temas disponibles"""
    try:
        categories = db.query(Theme.category).filter(Theme.is_active == True).distinct().all()
        return {"categories": [cat[0] for cat in categories]}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener categorías: {str(e)}"
        )
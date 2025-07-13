from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.api.dependencies import get_db, get_current_active_user
from app.schemas.user import User
from pydantic import BaseModel
import json
import os

router = APIRouter()

# Esquemas para la configuración visual
class VisualConfig(BaseModel):
    theme: str = "light"
    articlesCount: int = 6
    layout: str = "grid"
    showExcerpts: bool = True
    showDates: bool = True
    showCategories: bool = True

class VisualConfigResponse(VisualConfig):
    pass

# Archivo donde se guardará la configuración
CONFIG_FILE = "visual_config.json"

def load_config() -> VisualConfig:
    """Cargar configuración desde archivo"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return VisualConfig(**data)
    except Exception as e:
        print(f"Error cargando configuración: {e}")
    
    # Retornar configuración por defecto
    return VisualConfig()

def save_config(config: VisualConfig) -> bool:
    """Guardar configuración en archivo"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config.dict(), f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error guardando configuración: {e}")
        return False

@router.get("/", response_model=VisualConfigResponse)
def get_visual_config():
    """Obtener configuración visual actual"""
    config = load_config()
    return VisualConfigResponse(**config.dict())

@router.post("/", response_model=VisualConfigResponse)
def save_visual_config(
    config: VisualConfig
):
    """Guardar configuración visual"""
    # Validar valores
    if config.theme not in ["light", "dark", "mystic", "esoteric"]:
        raise HTTPException(
            status_code=400,
            detail="Tema no válido. Debe ser: light, dark, mystic o esoteric"
        )
    
    if config.articlesCount < 3 or config.articlesCount > 12:
        raise HTTPException(
            status_code=400,
            detail="El número de artículos debe estar entre 3 y 12"
        )
    
    if config.layout not in ["grid", "list", "masonry", "featured"]:
        raise HTTPException(
            status_code=400,
            detail="Layout no válido. Debe ser: grid, list, masonry o featured"
        )
    
    # Guardar configuración
    if save_config(config):
        return VisualConfigResponse(**config.dict())
    else:
        raise HTTPException(
            status_code=500,
            detail="Error al guardar la configuración"
        )

@router.put("/", response_model=VisualConfigResponse)
def update_visual_config(
    config: VisualConfig
):
    """Actualizar configuración visual (alias para POST)"""
    return save_visual_config(config)

@router.delete("/")
def reset_visual_config():
    """Resetear configuración visual a valores por defecto"""
    try:
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        return {"message": "Configuración visual reseteada a valores por defecto"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al resetear configuración: {str(e)}"
        )
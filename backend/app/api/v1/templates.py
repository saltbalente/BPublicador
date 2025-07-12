from typing import List
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class Template(BaseModel):
    id: str
    name: str
    description: str
    preview_image: str = ""

@router.get("/", response_model=List[Template])
def get_templates():
    """Obtener lista de templates disponibles"""
    templates = [
        Template(
            id="default",
            name="Default",
            description="Template por defecto del sistema",
            preview_image="/static/theme-previews/default.jpg"
        ),
        Template(
            id="dark",
            name="Dark - Oscuro Minimalista",
            description="Diseño oscuro y elegante con tipografía moderna",
            preview_image="/static/theme-previews/dark.jpg"
        ),
        Template(
            id="light",
            name="Light - Claro Minimalista",
            description="Diseño claro y limpio con tipografía serif elegante",
            preview_image="/static/theme-previews/light.jpg"
        )
    ]
    
    return templates

@router.get("/{template_id}", response_model=Template)
def get_template(template_id: str):
    """Obtener información de un template específico"""
    templates = {
        "default": Template(
            id="default",
            name="Default",
            description="Template por defecto del sistema",
            preview_image="/static/theme-previews/default.jpg"
        ),
        "dark": Template(
            id="dark",
            name="Dark - Oscuro Minimalista",
            description="Diseño oscuro y elegante con tipografía moderna",
            preview_image="/static/theme-previews/dark.jpg"
        ),
        "light": Template(
            id="light",
            name="Light - Claro Minimalista",
            description="Diseño claro y limpio con tipografía serif elegante",
            preview_image="/static/theme-previews/light.jpg"
        )
    }
    
    if template_id not in templates:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Template no encontrado")
    
    return templates[template_id]
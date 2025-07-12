from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import openai
import requests
from app.api.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.user import User as UserSchema, UserUpdate
from app.services.auth import get_password_hash
from app.utils.validators import validate_api_key

router = APIRouter()

@router.get("/profile", response_model=UserSchema)
def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """Obtener perfil del usuario actual"""
    return current_user

@router.put("/profile", response_model=UserSchema)
def update_user_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar perfil del usuario"""
    update_data = user_update.dict(exclude_unset=True)
    
    # Si se está actualizando la contraseña, hashearla
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    # Validar API keys si se están actualizando
    if "api_key_openai" in update_data and update_data["api_key_openai"]:
        if not validate_api_key(update_data["api_key_openai"], "openai"):
            raise HTTPException(
                status_code=400,
                detail="Formato de API key de OpenAI inválido"
            )
    
    if "api_key_deepseek" in update_data and update_data["api_key_deepseek"]:
        if not validate_api_key(update_data["api_key_deepseek"], "deepseek"):
            raise HTTPException(
                status_code=400,
                detail="Formato de API key de DeepSeek inválido"
            )
    
    # Actualizar campos del usuario
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/test-api-connection", response_model=None)
def test_api_connection(
    provider: str,
    api_key: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Verificar conexión con API de IA"""
    
    if not validate_api_key(api_key, provider):
        raise HTTPException(
            status_code=400,
            detail=f"Formato de API key de {provider} inválido"
        )
    
    try:
        if provider.lower() == "openai":
            return _test_openai_connection(api_key)
        elif provider.lower() == "deepseek":
            return _test_deepseek_connection(api_key)
        else:
            raise HTTPException(
                status_code=400,
                detail="Proveedor no soportado. Use 'openai' o 'deepseek'"
            )
    except Exception as e:
        return {
            "success": False,
            "message": f"Error al conectar con {provider}: {str(e)}",
            "provider": provider
        }

def _test_openai_connection(api_key: str) -> Dict[str, Any]:
    """Probar conexión con OpenAI"""
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Hacer una llamada simple para verificar la conexión
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=5
        )
        
        return {
            "success": True,
            "message": "Conexión exitosa con OpenAI",
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    except openai.AuthenticationError:
        return {
            "success": False,
            "message": "API key de OpenAI inválida",
            "provider": "openai"
        }
    except openai.RateLimitError:
        return {
            "success": False,
            "message": "Límite de rate excedido en OpenAI",
            "provider": "openai"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error de conexión con OpenAI: {str(e)}",
            "provider": "openai"
        }

def _test_deepseek_connection(api_key: str) -> Dict[str, Any]:
    """Probar conexión con DeepSeek"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "max_tokens": 5
        }
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "message": "Conexión exitosa con DeepSeek",
                "provider": "deepseek",
                "model": "deepseek-chat",
                "usage": data.get("usage", {})
            }
        elif response.status_code == 401:
            return {
                "success": False,
                "message": "API key de DeepSeek inválida",
                "provider": "deepseek"
            }
        elif response.status_code == 429:
            return {
                "success": False,
                "message": "Límite de rate excedido en DeepSeek",
                "provider": "deepseek"
            }
        else:
            return {
                "success": False,
                "message": f"Error HTTP {response.status_code}: {response.text}",
                "provider": "deepseek"
            }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": "Timeout al conectar con DeepSeek",
            "provider": "deepseek"
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "message": "Error de conexión con DeepSeek",
            "provider": "deepseek"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error inesperado con DeepSeek: {str(e)}",
            "provider": "deepseek"
        }

@router.get("/api-status", response_model=None)
def get_api_status(current_user: User = Depends(get_current_active_user)) -> Dict[str, Any]:
    """Obtener estado de las APIs configuradas"""
    status = {
        "openai": {
            "configured": bool(current_user.api_key_openai),
            "key_preview": None
        },
        "deepseek": {
            "configured": bool(current_user.api_key_deepseek),
            "key_preview": None
        }
    }
    
    # Mostrar preview de las keys (primeros 8 caracteres + asteriscos)
    if current_user.api_key_openai:
        key = current_user.api_key_openai
        status["openai"]["key_preview"] = key[:8] + "*" * (len(key) - 8)
    
    if current_user.api_key_deepseek:
        key = current_user.api_key_deepseek
        status["deepseek"]["key_preview"] = key[:8] + "*" * (len(key) - 8)
    
    return status
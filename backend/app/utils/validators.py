import re
from typing import Optional
from fastapi import HTTPException

def validate_email(email: str) -> bool:
    """Validar formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password: str) -> bool:
    """Validar fortaleza de contraseña"""
    # Al menos 8 caracteres, una mayúscula, una minúscula, un número
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    return has_upper and has_lower and has_digit

def validate_username(username: str) -> bool:
    """Validar formato de nombre de usuario"""
    # Solo letras, números y guiones bajos, 3-20 caracteres
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None

def validate_keyword(keyword: str) -> bool:
    """Validar palabra clave"""
    # No vacía, máximo 100 caracteres, sin caracteres especiales peligrosos
    if not keyword or len(keyword) > 100:
        return False
    
    # Evitar caracteres que podrían ser problemáticos
    dangerous_chars = ['<', '>', '"', "'", '&', ';']
    return not any(char in keyword for char in dangerous_chars)

def validate_content_length(content: str, min_length: int = 100, max_length: int = 10000) -> bool:
    """Validar longitud de contenido"""
    return min_length <= len(content) <= max_length

def validate_api_key(api_key: str, provider: str) -> bool:
    """Validar formato de API key según el proveedor"""
    if not api_key:
        return False
    
    if provider.lower() == "openai":
        # OpenAI keys empiezan con 'sk-'
        return api_key.startswith('sk-') and len(api_key) > 20
    
    elif provider.lower() == "deepseek":
        # DeepSeek keys tienen formato específico
        return len(api_key) > 20
    
    return False

def sanitize_html(text: str) -> str:
    """Sanitizar HTML básico"""
    # Remover tags HTML básicos peligrosos
    dangerous_tags = ['<script', '<iframe', '<object', '<embed', '<form']
    
    for tag in dangerous_tags:
        text = re.sub(f'{tag}.*?>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    return text

def validate_file_upload(filename: str, allowed_extensions: list = None) -> bool:
    """Validar archivo subido"""
    if allowed_extensions is None:
        allowed_extensions = ['.txt', '.md', '.docx']
    
    if not filename:
        return False
    
    # Verificar extensión
    file_ext = '.' + filename.split('.')[-1].lower()
    return file_ext in allowed_extensions

def validate_rate_limit(user_count: int, user_limit: int) -> None:
    """Validar límite de tasa"""
    if user_count >= user_limit:
        raise HTTPException(
            status_code=429,
            detail="Has excedido tu límite de uso diario"
        )

def validate_content_status_transition(current_status: str, new_status: str) -> bool:
    """Validar transiciones válidas de estado de contenido"""
    valid_transitions = {
        'draft': ['generating', 'review', 'published'],
        'generating': ['review', 'failed'],
        'review': ['published', 'draft'],
        'published': ['draft'],  # Solo para despublicar
        'failed': ['draft', 'generating']
    }
    
    return new_status in valid_transitions.get(current_status, [])

def validate_search_query(query: str) -> bool:
    """Validar consulta de búsqueda"""
    if not query or len(query.strip()) < 2:
        return False
    
    # Evitar consultas muy largas
    if len(query) > 200:
        return False
    
    # Evitar caracteres especiales problemáticos
    dangerous_chars = ['<', '>', '"', "'", ';', '--']
    return not any(char in query for char in dangerous_chars)
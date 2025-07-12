import re
import unicodedata
from sqlalchemy.orm import Session
from app.models.content import Content

def generate_slug(text: str) -> str:
    """
    Genera un slug URL-friendly a partir de un texto.
    """
    # Convertir a minúsculas
    text = text.lower()
    
    # Normalizar caracteres unicode (eliminar acentos)
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Reemplazar espacios y caracteres especiales con guiones
    text = re.sub(r'[^a-z0-9]+', '-', text)
    
    # Eliminar guiones al inicio y final
    text = text.strip('-')
    
    # Limitar longitud
    text = text[:250]
    
    # Eliminar guión final si se cortó en medio de una palabra
    text = text.rstrip('-')
    
    return text or 'contenido'

def generate_unique_slug(db: Session, title: str, content_id: int = None) -> str:
    """
    Genera un slug único verificando que no exista en la base de datos.
    
    Args:
        db: Sesión de base de datos
        title: Título del contenido
        content_id: ID del contenido (para excluir en actualizaciones)
    
    Returns:
        str: Slug único
    """
    base_slug = generate_slug(title)
    slug = base_slug
    counter = 1
    
    while True:
        # Verificar si el slug ya existe
        query = db.query(Content).filter(Content.slug == slug)
        
        # Si estamos actualizando, excluir el contenido actual
        if content_id:
            query = query.filter(Content.id != content_id)
        
        existing = query.first()
        
        if not existing:
            return slug
        
        # Si existe, agregar un número al final
        slug = f"{base_slug}-{counter}"
        counter += 1
        
        # Evitar bucle infinito
        if counter > 1000:
            import uuid
            return f"{base_slug}-{str(uuid.uuid4())[:8]}"

def calculate_reading_time(content: str) -> int:
    """
    Calcula el tiempo de lectura estimado en minutos.
    Asume una velocidad de lectura promedio de 200 palabras por minuto.
    
    Args:
        content: Contenido del artículo
    
    Returns:
        int: Tiempo de lectura en minutos
    """
    if not content:
        return 0
    
    word_count = len(content.split())
    reading_time = max(1, round(word_count / 200))  # Mínimo 1 minuto
    
    return reading_time

def extract_excerpt(content: str, max_length: int = 160) -> str:
    """
    Extrae un resumen del contenido.
    
    Args:
        content: Contenido completo
        max_length: Longitud máxima del resumen
    
    Returns:
        str: Resumen del contenido
    """
    if not content:
        return ""
    
    # Remover etiquetas HTML básicas
    clean_content = re.sub(r'<[^>]+>', '', content)
    
    # Tomar las primeras palabras
    words = clean_content.split()
    excerpt = ""
    
    for word in words:
        if len(excerpt + " " + word) <= max_length - 3:  # -3 para "..."
            excerpt += (" " if excerpt else "") + word
        else:
            break
    
    if len(clean_content) > len(excerpt):
        excerpt += "..."
    
    return excerpt
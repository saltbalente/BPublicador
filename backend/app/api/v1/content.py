from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.models.content import Content
from app.models.keyword import Keyword
from app.models.image_config import ImageConfig
from app.schemas.content import (
    ContentCreate,
    ContentUpdate,
    Content as ContentSchema,
    ContentWithKeyword,
    ContentStatus
)
from app.services.content_generator import ContentGenerator

router = APIRouter()

@router.post("/", response_model=ContentSchema)
def create_content(
    content: ContentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Crear nuevo contenido"""
    # Verificar que la palabra clave existe (solo si se proporciona)
    if content.keyword_id:
        keyword = db.query(Keyword).filter(Keyword.id == content.keyword_id).first()
        if not keyword:
            raise HTTPException(status_code=404, detail="Palabra clave no encontrada")
    
    # Manejar categoría - puede ser ID existente o nombre de nueva categoría
    category_id = None
    if content.category_id:
        if isinstance(content.category_id, int):
            # Es un ID existente
            from app.models.category import Category
            category = db.query(Category).filter(Category.id == content.category_id).first()
            if not category:
                raise HTTPException(status_code=404, detail="Categoría no encontrada")
            category_id = content.category_id
        else:
            # Es un nombre de categoría, buscar o crear
            from app.models.category import Category
            category_name = content.category_id.strip()
            category = db.query(Category).filter(Category.name.ilike(category_name)).first()
            if not category:
                # Crear nueva categoría
                import re
                slug = re.sub(r'[^a-zA-Z0-9\s]', '', category_name.lower())
                slug = re.sub(r'\s+', '-', slug.strip())
                
                # Verificar que el slug sea único
                base_slug = slug
                counter = 1
                while db.query(Category).filter(Category.slug == slug).first():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                category = Category(
                    name=category_name,
                    slug=slug
                )
                db.add(category)
                db.commit()
                db.refresh(category)
            category_id = category.id
    
    # Verificar límite diario del usuario (simplificado por ahora)
    # TODO: Implementar contador diario real
    from datetime import datetime, date
    today = date.today()
    daily_content_count = db.query(Content).filter(
        Content.user_id == current_user.id,
        Content.created_at >= datetime.combine(today, datetime.min.time())
    ).count()
    
    if daily_content_count >= current_user.daily_limit:
        raise HTTPException(
            status_code=400,
            detail=f"Has alcanzado tu límite diario de contenido ({current_user.daily_limit})"
        )
    
    # Generar slug automáticamente
    import re
    from datetime import datetime
    
    slug = re.sub(r'[^a-zA-Z0-9\s]', '', content.title.lower())
    slug = re.sub(r'\s+', '-', slug.strip())
    
    # Verificar que el slug sea único
    base_slug = slug
    counter = 1
    while db.query(Content).filter(Content.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Determinar el estado basado en la entrada del usuario
    status = content.status
    if status == ContentStatus.PUBLISHED:
        # Si se publica, asegurarse de que no esté programado para el futuro
        if content.scheduled_at and content.scheduled_at > datetime.utcnow():
            status = ContentStatus.SCHEDULED
    elif content.scheduled_at and content.scheduled_at > datetime.utcnow():
        status = ContentStatus.SCHEDULED
    else:
        status = ContentStatus.DRAFT
    
    db_content = Content(
        title=content.title,
        content=content.content or "",
        excerpt=content.excerpt,
        slug=slug,
        meta_title=content.meta_title,
        meta_description=content.meta_description,
        focus_keyword=content.focus_keyword,
        canonical_url=content.canonical_url,
        content_type=content.content_type,
        template_theme=content.template_theme,
        status=status,
        is_featured=content.is_featured,
        allow_comments=content.allow_comments,
        is_indexed=content.is_indexed,
        keyword_id=content.keyword_id,
        category_id=category_id,
        scheduled_at=content.scheduled_at,
        user_id=current_user.id,
        word_count=len((content.content or "").split()) if content.content else 0
    )
    
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    
    # Manejar tags si se proporcionan
    if content.tag_ids:
        from app.models.tag import Tag
        from app.models.content_tag import ContentTag
        
        for tag_id in content.tag_ids:
            tag = db.query(Tag).filter(Tag.id == tag_id).first()
            if tag:
                content_tag = ContentTag(content_id=db_content.id, tag_id=tag_id)
                db.add(content_tag)
        
        db.commit()
    
    return db_content

@router.get("/", response_model=List[ContentWithKeyword])
def read_content(
    skip: int = 0,
    limit: int = 100,
    user_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener lista de contenido"""
    query = db.query(Content)
    
    if user_only:
        query = query.filter(Content.user_id == current_user.id)
    
    content = query.offset(skip).limit(limit).all()
    return content

@router.get("/{content_id}", response_model=ContentWithKeyword)
def read_content_item(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener contenido por ID"""
    content = db.query(Content).filter(Content.id == content_id).first()
    if content is None:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    
    # Verificar que el usuario tiene acceso al contenido
    if content.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes acceso a este contenido")
    
    return content

@router.put("/{content_id}", response_model=ContentSchema)
def update_content(
    content_id: int,
    content_update: ContentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Actualizar contenido"""
    import logging
    logger = logging.getLogger("content_update")
    
    content = db.query(Content).filter(Content.id == content_id).first()
    if content is None:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    
    # Verificar que el usuario tiene acceso al contenido
    if content.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes acceso a este contenido")

    logger.info(f"Actualizando contenido {content_id} con datos: {content_update.dict(exclude_unset=True)}")
    update_data = content_update.dict(exclude_unset=True)

    # Manejar categoría si se está actualizando
    if 'category_id' in update_data and update_data['category_id'] is not None:
        category_value = update_data['category_id']
        if isinstance(category_value, int):
            # Es un ID existente
            from app.models.category import Category
            category = db.query(Category).filter(Category.id == category_value).first()
            if not category:
                raise HTTPException(status_code=404, detail="Categoría no encontrada")
            update_data['category_id'] = category_value
        else:
            # Es un nombre de categoría, buscar o crear
            from app.models.category import Category
            category_name = category_value.strip()
            category = db.query(Category).filter(Category.name.ilike(category_name)).first()
            if not category:
                # Crear nueva categoría
                import re
                slug = re.sub(r'[^a-zA-Z0-9\s]', '', category_name.lower())
                slug = re.sub(r'\s+', '-', slug.strip())
                
                # Verificar que el slug sea único
                base_slug = slug
                counter = 1
                while db.query(Category).filter(Category.slug == slug).first():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                category = Category(
                    name=category_name,
                    slug=slug
                )
                db.add(category)
                db.commit()
                db.refresh(category)
            update_data['category_id'] = category.id

    # Si se está actualizando el slug, verificar que no exista en otro contenido
    if 'slug' in update_data and update_data['slug'] != content.slug:
        existing_content = db.query(Content).filter(Content.slug == update_data['slug']).first()
        if existing_content:
            raise HTTPException(status_code=400, detail="El slug ya está en uso")

    for field, value in update_data.items():
        setattr(content, field, value)

    # Actualizar word count si se cambió el contenido
    if 'content' in update_data:
        content.word_count = len(update_data['content'].split())
    
    # Actualizar fecha de publicación si se publica
    if update_data.get('status') == ContentStatus.PUBLISHED and not content.published_at:
        from datetime import datetime
        content.published_at = datetime.utcnow()
    
    db.commit()
    db.refresh(content)
    
    return content

@router.delete("/{content_id}", response_model=None)
def delete_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Eliminar contenido"""
    content = db.query(Content).filter(Content.id == content_id).first()
    if content is None:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    
    # Verificar que el usuario tiene acceso al contenido
    if content.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes acceso a este contenido")
    
    db.delete(content)
    db.commit()
    
    return {"message": "Contenido eliminado exitosamente"}

class GenerateContentRequest(BaseModel):
    provider: str = "auto"
    content_type: str = "article"
    additional_keywords: Optional[List[int]] = []

@router.post("/generate/{keyword_id}", response_model=None)
def generate_content(
    keyword_id: int,
    request: GenerateContentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generar contenido automáticamente para una palabra clave"""
    # Verificar que la palabra clave existe
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Palabra clave no encontrada")
    
    # Verificar límite diario del usuario
    from datetime import datetime, date
    today = date.today()
    daily_content_count = db.query(Content).filter(
        Content.user_id == current_user.id,
        Content.created_at >= datetime.combine(today, datetime.min.time())
    ).count()
    
    if daily_content_count >= current_user.daily_limit:
        raise HTTPException(
            status_code=400,
            detail=f"Has alcanzado tu límite diario de contenido ({current_user.daily_limit})"
        )
    
    # Generar slug único
    from app.utils.helpers import generate_unique_slug
    base_title = f"Generando contenido para: {keyword.keyword}"
    unique_slug = generate_unique_slug(db, base_title)
    
    # Crear contenido en estado "generando"
    db_content = Content(
        title=base_title,
        slug=unique_slug,
        content="",
        status=ContentStatus.GENERATING,
        keyword_id=keyword_id,
        user_id=current_user.id
    )
    
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    
    # Obtener keywords adicionales si se proporcionaron
    additional_keywords = []
    if request.additional_keywords:
        additional_keywords = db.query(Keyword).filter(
            Keyword.id.in_(request.additional_keywords)
        ).all()
    
    # Agregar tarea en segundo plano para generar contenido
    background_tasks.add_task(
        generate_content_task,
        db_content.id,
        keyword_id,
        current_user.id,
        request.provider,
        request.content_type,
        [kw.id for kw in additional_keywords]
    )
    
    return {
        "message": "Generación de contenido iniciada",
        "content_id": db_content.id,
        "status": "generating"
    }

async def generate_content_task(
    content_id: int,
    keyword_id: int,
    user_id: int,
    provider: str,
    content_type: str,
    additional_keyword_ids: Optional[List[int]] = None
):
    """Tarea en segundo plano para generar contenido e imágenes"""
    from app.core.database import SessionLocal
    import logging
    
    # Configurar logging específico para generación
    logger = logging.getLogger("content_generation")
    
    db = SessionLocal()
    try:
        content = db.query(Content).filter(Content.id == content_id).first()
        keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        
        if not all([content, keyword, user]):
            logger.error(f"Datos faltantes: content={content}, keyword={keyword}, user={user}")
            return
        
        logger.info(f"Iniciando generación de contenido para keyword: {keyword.keyword} (ID: {content_id})")
        
        # Actualizar estado de la palabra clave
        keyword.status = "processing"
        db.commit()
        
        try:
            # Verificar que el usuario tenga API keys configuradas
            if not user.api_key_openai and not user.api_key_deepseek:
                # Verificar si hay API keys globales en settings
                from app.core.config import settings
                if not hasattr(settings, 'OPENAI_API_KEY') and not hasattr(settings, 'DEEPSEEK_API_KEY'):
                    raise ValueError("No hay API keys configuradas. Por favor configura tus API keys en la sección de Configuración.")
            
            # Obtener keywords adicionales si se proporcionaron
            additional_keywords = []
            if additional_keyword_ids:
                additional_keywords = db.query(Keyword).filter(
                    Keyword.id.in_(additional_keyword_ids)
                ).all()
                logger.info(f"Keywords adicionales encontradas: {len(additional_keywords)}")
            
            # FASE 1: Generar contenido de texto
            logger.info("FASE 1: Iniciando generación de contenido de texto...")
            generator = ContentGenerator(user)
            
            # Si hay keywords adicionales, las incluimos en el contexto
            if additional_keywords:
                # Crear un contexto con todas las keywords
                all_keywords = [keyword] + additional_keywords
                keyword_context = ", ".join([kw.keyword for kw in all_keywords])
                
                # Modificar temporalmente la keyword principal para incluir el contexto
                original_keyword = keyword.keyword
                keyword.keyword = f"{original_keyword} (relacionado con: {keyword_context})"
                
                generated = await generator.generate_content(keyword, provider, content_type)
                
                # Restaurar la keyword original
                keyword.keyword = original_keyword
            else:
                generated = await generator.generate_content(keyword, provider, content_type)
            
            logger.info("Contenido de texto generado exitosamente")
            
            # Actualizar contenido
            from app.utils.helpers import generate_unique_slug, calculate_reading_time, extract_excerpt
            
            new_title = generated.get("title", f"Artículo sobre {keyword.keyword}")
            new_content = generated.get("content", "")
            
            content.title = new_title
            content.slug = generate_unique_slug(db, new_title, content.id)
            content.content = new_content
            content.excerpt = extract_excerpt(new_content)
            content.meta_description = generated.get("meta_description", extract_excerpt(new_content, 160))
            content.word_count = len(new_content.split())
            content.reading_time = calculate_reading_time(new_content)
            content.status = ContentStatus.DRAFT
            content.focus_keyword = keyword.keyword
            
            # Actualizar campos Schema.org
            content.author_name = generated.get("author_name", "Redactor IA")
            content.publisher_name = generated.get("publisher_name", "Mi Sitio Web")
            content.schema_type = generated.get("schema_type", "Article")
            content.article_section = generated.get("article_section", "General")
            
            # Guardar cambios del contenido
            db.commit()
            logger.info(f"Contenido actualizado: {new_title} ({content.word_count} palabras)")
            
            # FASE 2: Verificar configuración de imágenes y generar si está habilitado
            logger.info("FASE 2: Verificando configuración de imágenes...")
            
            # Verificar si la generación automática de imágenes está habilitada
            should_generate_images = check_auto_image_generation(user_id, keyword_id, db)
            
            if should_generate_images:
                logger.info("Generación automática de imágenes habilitada. Iniciando generación...")
                
                # Cambiar estado para indicar que se están generando imágenes
                content.status = ContentStatus.GENERATING  # Temporal para mostrar progreso
                db.commit()
                
                try:
                    from app.services.image_generator import ImageGenerator
                    image_generator = ImageGenerator(user)
                    
                    # Obtener configuración de imágenes
                    image_config = get_image_config_for_content(user_id, keyword_id, db)
                    num_images = image_config.get('num_images', 2)
                    
                    logger.info(f"Generando {num_images} imágenes para el contenido...")
                    
                    # Generar imágenes
                    generated_images = image_generator.generate_images_for_content(content_id, num_images)
                    
                    if generated_images:
                        logger.info(f"Se generaron {len(generated_images)} imágenes exitosamente")
                        
                        # Generar imagen destacada si está configurado
                        if image_config.get('include_featured', True):
                            logger.info("Generando imagen destacada...")
                            featured_image = image_generator.generate_featured_image(content_id)
                            if featured_image:
                                logger.info("Imagen destacada generada exitosamente")
                            else:
                                logger.warning("No se pudo generar la imagen destacada")
                    else:
                        logger.warning("No se generaron imágenes")
                        
                except Exception as img_error:
                    logger.error(f"Error generando imágenes: {str(img_error)}")
                    # No fallar todo el proceso por errores de imágenes
                    import traceback
                    logger.error(f"Traceback de error de imágenes: {traceback.format_exc()}")
                
                # Restaurar estado final del contenido
                content.status = ContentStatus.DRAFT
                db.commit()
                
            else:
                logger.info("Generación automática de imágenes deshabilitada")
            
            # Actualizar estado de la palabra clave
            keyword.status = "completed"
            logger.info(f"Generación completada exitosamente para: {keyword.keyword}")
            
        except Exception as e:
            # Logging detallado del error
            import traceback
            error_details = f"Error generando contenido: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            logger.error(f"ERROR EN GENERACIÓN: {error_details}")
            
            # Manejar errores
            content.status = ContentStatus.FAILED
            content.content = error_details
            keyword.status = "failed"
        
        db.commit()
        
    finally:
        db.close()


def check_auto_image_generation(user_id: int, keyword_id: int, db: Session) -> bool:
    """
    Verifica si la generación automática de imágenes está habilitada
    """
    try:
        # Verificar configuración global del usuario
        global_config = db.query(ImageConfig).filter(
            ImageConfig.user_id == user_id,
            ImageConfig.keyword_id.is_(None)
        ).first()
        
        if global_config:
            return global_config.auto_generate
        else:
            # Por defecto, la generación automática está habilitada
            return True
    except Exception as e:
        logger.error(f"Error checking auto image generation: {e}")
        return False


def get_image_config_for_content(user_id: int, keyword_id: int, db: Session) -> dict:
    """
    Obtiene la configuración de imágenes para el contenido
    """
    try:
        # Buscar configuración específica de la keyword
        keyword_config = db.query(ImageConfig).filter(
            ImageConfig.user_id == user_id,
            ImageConfig.keyword_id == keyword_id
        ).first()
        
        # Buscar configuración global del usuario
        global_config = db.query(ImageConfig).filter(
            ImageConfig.user_id == user_id,
            ImageConfig.keyword_id.is_(None)
        ).first()
        
        # Configuración por defecto
        config = {
            "num_images": 2,
            "style": "realistic",
            "include_featured": True,
            "custom_prompt": None
        }
        
        # Aplicar configuración global si existe
        if global_config:
            config["num_images"] = global_config.images_per_content
            config["style"] = global_config.image_style.value
            config["include_featured"] = global_config.include_featured
        
        # Aplicar configuración específica de keyword si existe (tiene prioridad)
        if keyword_config:
            if keyword_config.keyword_count is not None:
                config["num_images"] = keyword_config.keyword_count
            if keyword_config.keyword_style is not None:
                config["style"] = keyword_config.keyword_style.value
            if keyword_config.custom_prompt is not None:
                config["custom_prompt"] = keyword_config.custom_prompt
        
        return config
    except Exception as e:
        logger.error(f"Error getting image config: {e}")
        return {
            "num_images": 2,
            "style": "realistic",
            "include_featured": True,
            "custom_prompt": None
        }


@router.get("/status/{status}", response_model=List[ContentSchema])
def get_content_by_status(
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener contenido por estado"""
    content = db.query(Content).filter(
        Content.status == status,
        Content.user_id == current_user.id
    ).all()
    return content

@router.get("/generation-status/{content_id}", response_model=None)
def get_generation_status(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Verificar el estado de generación de contenido e imágenes"""
    content = db.query(Content).filter(
        Content.id == content_id,
        Content.user_id == current_user.id
    ).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    
    # Obtener información de imágenes
    from app.models.content_image import ContentImage
    images = db.query(ContentImage).filter(
        ContentImage.content_id == content_id
    ).all()
    
    # Determinar el estado de las imágenes
    image_status = "pending"
    if content.status == ContentStatus.GENERATING:
        if len(content.content) > 100:  # Si ya hay contenido, probablemente esté generando imágenes
            image_status = "generating"
        else:
            image_status = "pending"
    elif content.status in [ContentStatus.DRAFT, ContentStatus.PUBLISHED]:
        image_status = "completed" if images else "none"
    elif content.status == ContentStatus.FAILED:
        image_status = "failed"
    
    return {
        "content_id": content.id,
        "status": content.status,
        "title": content.title,
        "progress": {
            "text_generating": content.status == ContentStatus.GENERATING and len(content.content) < 100,
            "image_generating": content.status == ContentStatus.GENERATING and len(content.content) > 100,
            "completed": content.status in [ContentStatus.DRAFT, ContentStatus.PUBLISHED],
            "failed": content.status == ContentStatus.FAILED
        },
        "content_preview": content.content[:200] + "..." if len(content.content) > 200 else content.content,
        "word_count": content.word_count,
        "reading_time": content.reading_time,
        "images": {
            "status": image_status,
            "count": len(images),
            "featured_count": len([img for img in images if img.is_featured]),
            "regular_count": len([img for img in images if not img.is_featured])
        }
    }
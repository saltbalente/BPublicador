from celery import current_task
from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.content import Content
from app.models.keyword import Keyword
from app.models.user import User
from app.schemas.content import ContentStatus
from app.services.content_generator import ContentGenerator
import structlog

logger = structlog.get_logger()

@celery_app.task(bind=True)
def generate_content_task(
    self,
    content_id: int,
    keyword_id: int,
    user_id: int,
    provider: str = "openai",
    content_type: str = "article"
):
    """Tarea para generar contenido automáticamente"""
    db = SessionLocal()
    
    try:
        # Actualizar estado de la tarea
        current_task.update_state(
            state="PROGRESS",
            meta={"step": "Iniciando generación", "progress": 10}
        )
        
        # Obtener objetos de la base de datos
        content = db.query(Content).filter(Content.id == content_id).first()
        keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
        user = db.query(User).filter(User.id == user_id).first()
        
        if not all([content, keyword, user]):
            raise Exception("No se encontraron los objetos necesarios")
        
        logger.info(
            "Iniciando generación de contenido",
            content_id=content_id,
            keyword=keyword.keyword,
            user=user.username,
            provider=provider
        )
        
        # Actualizar estado de la palabra clave
        keyword.status = "processing"
        db.commit()
        
        current_task.update_state(
            state="PROGRESS",
            meta={"step": "Generando contenido con IA", "progress": 30}
        )
        
        # Generar contenido
        generator = ContentGenerator(user)
        generated = generator.generate_content(keyword, provider, content_type)
        
        current_task.update_state(
            state="PROGRESS",
            meta={"step": "Procesando contenido generado", "progress": 70}
        )
        
        # Actualizar contenido en la base de datos
        content.title = generated.get("title", f"Artículo sobre {keyword.keyword}")
        content.content = generated.get("content", "")
        content.meta_description = generated.get("meta_description", "")
        content.word_count = len(generated.get("content", "").split())
        content.status = ContentStatus.REVIEW
        
        # Actualizar estado de la palabra clave
        keyword.status = "completed"
        
        current_task.update_state(
            state="PROGRESS",
            meta={"step": "Guardando en base de datos", "progress": 90}
        )
        
        db.commit()
        
        logger.info(
            "Contenido generado exitosamente",
            content_id=content_id,
            word_count=content.word_count,
            title=content.title[:50] + "..."
        )
        
        return {
            "status": "completed",
            "content_id": content_id,
            "title": content.title,
            "word_count": content.word_count,
            "meta_description": content.meta_description
        }
        
    except Exception as e:
        logger.error(
            "Error generando contenido",
            content_id=content_id,
            error=str(e),
            exc_info=True
        )
        
        # Actualizar estado de error
        if 'content' in locals():
            content.status = ContentStatus.FAILED
            content.content = f"Error generando contenido: {str(e)}"
        
        if 'keyword' in locals():
            keyword.status = "failed"
        
        db.commit()
        
        # Relanzar la excepción para que Celery la registre
        raise self.retry(exc=e, countdown=60, max_retries=3)
        
    finally:
        db.close()

@celery_app.task
def reset_daily_limits():
    """Tarea para resetear los límites diarios de contenido"""
    db = SessionLocal()
    
    try:
        # Resetear contador diario de todos los usuarios
        users_updated = db.query(User).update(
            {User.daily_content_count: 0}
        )
        
        db.commit()
        
        logger.info(
            "Límites diarios reseteados",
            users_updated=users_updated
        )
        
        return {
            "status": "completed",
            "users_updated": users_updated,
            "message": "Límites diarios reseteados exitosamente"
        }
        
    except Exception as e:
        logger.error(
            "Error reseteando límites diarios",
            error=str(e),
            exc_info=True
        )
        db.rollback()
        raise e
        
    finally:
        db.close()

@celery_app.task
def cleanup_failed_content():
    """Tarea para limpiar contenido fallido después de cierto tiempo"""
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    
    try:
        # Eliminar contenido fallido de más de 7 días
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        failed_content = db.query(Content).filter(
            Content.status == ContentStatus.FAILED,
            Content.created_at < cutoff_date
        ).all()
        
        deleted_count = len(failed_content)
        
        for content in failed_content:
            db.delete(content)
        
        db.commit()
        
        logger.info(
            "Contenido fallido limpiado",
            deleted_count=deleted_count
        )
        
        return {
            "status": "completed",
            "deleted_count": deleted_count,
            "message": f"Se eliminaron {deleted_count} elementos de contenido fallido"
        }
        
    except Exception as e:
        logger.error(
            "Error limpiando contenido fallido",
            error=str(e),
            exc_info=True
        )
        db.rollback()
        raise e
        
    finally:
        db.close()
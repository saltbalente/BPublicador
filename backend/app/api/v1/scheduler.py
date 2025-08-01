from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, time
from app.core.database import get_db
from app.services.scheduler_service import SchedulerService
from app.api.dependencies import get_current_active_user
from app.models.user import User
from pydantic import BaseModel, validator

router = APIRouter()

class SchedulerConfig(BaseModel):
    enabled: bool
    interval_minutes: int
    max_daily_posts: int
    start_time: Optional[str] = None  # Format: "HH:MM"
    end_time: Optional[str] = None    # Format: "HH:MM"
    days_of_week: Optional[List[int]] = None  # 0=Monday, 6=Sunday
    auto_publish: bool = False
    generate_images: bool = True
    content_style: Optional[str] = "professional"
    word_count_min: Optional[int] = 500
    word_count_max: Optional[int] = 1500
    
    @validator('interval_minutes')
    def validate_interval(cls, v):
        if v < 5:
            raise ValueError('Minimum interval is 5 minutes')
        return v
    
    @validator('max_daily_posts')
    def validate_daily_posts(cls, v):
        if v < 1 or v > 50:
            raise ValueError('Daily posts must be between 1 and 50')
        return v
    
    @validator('days_of_week')
    def validate_days(cls, v):
        if v is not None:
            if not all(0 <= day <= 6 for day in v):
                raise ValueError('Days of week must be between 0 (Monday) and 6 (Sunday)')
        return v

class QueueItem(BaseModel):
    keyword_id: int
    scheduled_for: datetime
    priority: Optional[int] = 1
    content_style: Optional[str] = "professional"
    word_count: Optional[int] = 800
    generate_images: Optional[bool] = True

@router.get("/status", response_model=None)
async def get_scheduler_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene el estado actual del programador
    """
    try:
        scheduler_service = SchedulerService(db)
        scheduler_status = scheduler_service.get_scheduler_status(current_user.id)
        return scheduler_status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting scheduler status: {str(e)}"
        )

@router.post("/configure")
async def configure_scheduler(
    config: SchedulerConfig,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Configurar el programador automático"""
    try:
        scheduler_service = SchedulerService(db)
        result = await scheduler_service.configure_scheduler(current_user.id, config.dict())
        return {"message": "Scheduler configurado exitosamente", "config": result}
    except Exception as e:
        logger.error(f"Error configurando scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start", response_model=None)
async def start_scheduler(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Inicia el programador automático
    """
    try:
        scheduler_service = SchedulerService(db)
        result = scheduler_service.start_scheduler(current_user.id)
        return {
            "success": True,
            "message": "Scheduler started successfully",
            "next_execution": result.get("next_execution")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting scheduler: {str(e)}"
        )

@router.post("/stop", response_model=None)
async def stop_scheduler(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Detiene el programador automático
    """
    try:
        scheduler_service = SchedulerService(db)
        result = scheduler_service.stop_scheduler(current_user.id)
        return {
            "success": True,
            "message": "Scheduler stopped successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error stopping scheduler: {str(e)}"
        )

@router.get("/queue", response_model=None)
async def get_queue(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene la cola de tareas programadas
    """
    try:
        scheduler_service = SchedulerService(db)
        queue_items = await scheduler_service.get_queue(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            db=db
        )
        return {
            "queue_items": queue_items["items"],
            "total": queue_items["total"],
            "pending": queue_items["pending"],
            "processing": queue_items["processing"],
            "completed": queue_items["completed"],
            "failed": queue_items["failed"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting queue: {str(e)}"
        )

@router.post("/queue/add", response_model=None)
async def add_to_queue(
    item: QueueItem,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Añade un elemento a la cola de programación
    """
    try:
        scheduler_service = SchedulerService(db)
        result = await scheduler_service.add_to_queue(
            user_id=current_user.id,
            keyword_id=item.keyword_id,
            scheduled_for=item.scheduled_for,
            priority=item.priority,
            config={
                "content_style": item.content_style,
                "word_count": item.word_count,
                "generate_images": item.generate_images
            },
            db=db
        )
        return {
            "success": True,
            "message": "Item added to queue successfully",
            "queue_item_id": result["queue_item_id"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding to queue: {str(e)}"
        )

@router.delete("/queue/{item_id}", response_model=None)
async def remove_from_queue(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Elimina un elemento de la cola
    """
    try:
        scheduler_service = SchedulerService(db)
        await scheduler_service.remove_from_queue(
            item_id=item_id,
            user_id=current_user.id,
            db=db
        )
        return {
            "success": True,
            "message": "Item removed from queue successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing from queue: {str(e)}"
        )

@router.post("/queue/{item_id}/retry", response_model=None)
async def retry_queue_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Reintenta un elemento fallido de la cola
    """
    try:
        scheduler_service = SchedulerService(db)
        result = await scheduler_service.retry_queue_item(
            item_id=item_id,
            user_id=current_user.id,
            db=db
        )
        return {
            "success": True,
            "message": "Item queued for retry",
            "new_scheduled_time": result["scheduled_for"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrying queue item: {str(e)}"
        )

@router.get("/logs", response_model=None)
async def get_scheduler_logs(
    limit: int = 100,
    offset: int = 0,
    level: Optional[str] = None,  # info, warning, error
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene los logs del programador
    """
    try:
        scheduler_service = SchedulerService(db)
        logs = await scheduler_service.get_logs(
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            level=level
        )
        return {
            "logs": logs["items"],
            "total": logs["total"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting logs: {str(e)}"
        )

@router.get("/statistics", response_model=None)
async def get_scheduler_statistics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene estadísticas del programador
    """
    try:
        scheduler_service = SchedulerService(db)
        stats = await scheduler_service.get_statistics(
            user_id=current_user.id,
            days=days
        )
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting statistics: {str(e)}"
        )

@router.post("/test-run", response_model=None)
async def test_scheduler(
    keyword_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Ejecuta una prueba del programador con una keyword específica
    """
    try:
        scheduler_service = SchedulerService(db)
        result = await scheduler_service.test_generation(
            user_id=current_user.id,
            keyword_id=keyword_id,
            db=db
        )
        return {
            "success": True,
            "message": "Test generation completed",
            "content_id": result.get("content_id"),
            "generation_time": result.get("generation_time"),
            "word_count": result.get("word_count"),
            "images_generated": result.get("images_generated", 0)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in test run: {str(e)}"
        )

@router.get("/next-execution", response_model=None)
async def get_next_execution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene información sobre la próxima ejecución programada
    """
    try:
        scheduler_service = SchedulerService(db)
        next_exec = await scheduler_service.get_next_execution(current_user.id)
        return next_exec
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting next execution: {str(e)}"
        )
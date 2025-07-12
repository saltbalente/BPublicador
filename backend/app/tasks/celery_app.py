from celery import Celery
from app.core.config import settings

# Crear instancia de Celery
celery_app = Celery(
    "autopublicador",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.content_tasks"]
)

# Configuración de Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Configuración de rutas de tareas
celery_app.conf.task_routes = {
    "app.tasks.content_tasks.generate_content_task": "content_queue",
    "app.tasks.content_tasks.reset_daily_limits": "maintenance_queue",
}

# Configuración de tareas periódicas
celery_app.conf.beat_schedule = {
    "reset-daily-limits": {
        "task": "app.tasks.content_tasks.reset_daily_limits",
        "schedule": 86400.0,  # Cada 24 horas
    },
}
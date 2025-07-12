import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.keyword import Keyword, KeywordStatus
from app.models.content import Content, ContentStatus
from app.models.user import User
from app.services.content_generator import ContentGenerator
from app.services.image_generator import ImageGenerator
from app.utils.logging import get_logger
from app.core.config import settings
import json
from enum import Enum

logger = get_logger(__name__)

class ScheduleInterval(str, Enum):
    FIVE_MINUTES = "5min"
    FIFTEEN_MINUTES = "15min"
    THIRTY_MINUTES = "30min"
    HOURLY = "hourly"
    DAILY = "daily"
    TWICE_DAILY = "twicedaily"
    WEEKLY = "weekly"

class SchedulerService:
    """Servicio de programación automática para generación de contenido"""
    
    def __init__(self, db: Session):
        self.db = db
        self.image_generator = ImageGenerator(db)
        self.is_running = False
        self.current_task = None
        
    def start_scheduler(self, user_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """Iniciar el programador automático"""
        try:
            # Validar configuración
            validated_config = self._validate_scheduler_config(config)
            
            # Verificar que el usuario existe
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"Usuario {user_id} no encontrado")
            
            # Guardar configuración del scheduler
            scheduler_config = {
                "user_id": user_id,
                "interval": validated_config["interval"],
                "max_posts_per_day": validated_config["max_posts_per_day"],
                "schedule_time": validated_config.get("schedule_time"),
                "auto_publish": validated_config.get("auto_publish", False),
                "generate_images": validated_config.get("generate_images", True),
                "content_settings": validated_config.get("content_settings", {}),
                "started_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
            # Aquí normalmente guardarías en una tabla de configuración
            # Por ahora lo mantenemos en memoria/cache
            self._save_scheduler_config(user_id, scheduler_config)
            
            self.is_running = True
            
            logger.info(f"Scheduler iniciado para usuario {user_id} con intervalo {validated_config['interval']}")
            
            return {
                "status": "started",
                "config": scheduler_config,
                "next_execution": self._calculate_next_execution(validated_config["interval"], validated_config.get("schedule_time"))
            }
            
        except Exception as e:
            logger.error(f"Error iniciando scheduler: {str(e)}")
            raise
    
    def stop_scheduler(self, user_id: int) -> Dict[str, Any]:
        """Detener el programador automático"""
        try:
            # Actualizar estado del scheduler
            config = self._get_scheduler_config(user_id)
            if config:
                config["status"] = "stopped"
                config["stopped_at"] = datetime.utcnow().isoformat()
                self._save_scheduler_config(user_id, config)
            
            self.is_running = False
            
            logger.info(f"Scheduler detenido para usuario {user_id}")
            
            return {
                "status": "stopped",
                "stopped_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error deteniendo scheduler: {str(e)}")
            raise
    
    def get_scheduler_status(self, user_id: int) -> Dict[str, Any]:
        """Obtener estado actual del scheduler"""
        try:
            config = self._get_scheduler_config(user_id)
            
            if not config:
                return {
                    "status": "not_configured",
                    "is_running": False
                }
            
            # Obtener estadísticas del día
            today_stats = self._get_today_generation_stats(user_id)
            
            # Calcular próxima ejecución
            next_execution = None
            if config["status"] == "active":
                next_execution = self._calculate_next_execution(
                    config["interval"], 
                    config.get("schedule_time")
                )
            
            return {
                "status": config["status"],
                "is_running": self.is_running and config["status"] == "active",
                "config": config,
                "today_stats": today_stats,
                "next_execution": next_execution,
                "current_task": self.current_task
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del scheduler: {str(e)}")
            raise
    
    async def execute_scheduled_generation(self, user_id: int) -> Dict[str, Any]:
        """Ejecutar generación programada"""
        try:
            config = self._get_scheduler_config(user_id)
            if not config or config["status"] != "active":
                return {"status": "skipped", "reason": "Scheduler no activo"}
            
            # Verificar límites diarios
            today_stats = self._get_today_generation_stats(user_id)
            max_daily = config["max_posts_per_day"]
            
            if today_stats["generated_today"] >= max_daily:
                return {
                    "status": "skipped", 
                    "reason": f"Límite diario alcanzado ({max_daily})"
                }
            
            # Obtener keyword disponible
            keyword = self._get_next_available_keyword(user_id)
            if not keyword:
                return {
                    "status": "skipped", 
                    "reason": "No hay keywords disponibles"
                }
            
            # Marcar tarea como en progreso
            self.current_task = {
                "keyword_id": keyword.id,
                "keyword": keyword.keyword,
                "started_at": datetime.utcnow().isoformat(),
                "status": "generating"
            }
            
            # Generar contenido
            content_settings = config.get("content_settings", {})
            generation_result = await self._generate_content_with_settings(
                keyword, user_id, content_settings
            )
            
            # Generar imágenes si está habilitado
            if config.get("generate_images", True) and generation_result["success"]:
                try:
                    images = self.image_generator.generate_images_for_content(
                        generation_result["content_id"], 
                        num_images=content_settings.get("num_images", 2)
                    )
                    generation_result["images_generated"] = len(images)
                except Exception as e:
                    logger.warning(f"Error generando imágenes: {str(e)}")
                    generation_result["images_generated"] = 0
            
            # Publicar automáticamente si está configurado
            if config.get("auto_publish", False) and generation_result["success"]:
                self._auto_publish_content(generation_result["content_id"])
                generation_result["auto_published"] = True
            
            # Actualizar tarea
            self.current_task["status"] = "completed" if generation_result["success"] else "failed"
            self.current_task["completed_at"] = datetime.utcnow().isoformat()
            
            # Log del resultado
            if generation_result["success"]:
                logger.info(f"Contenido generado automáticamente: {generation_result['title']}")
            else:
                logger.error(f"Error en generación automática: {generation_result.get('error')}")
            
            return {
                "status": "completed" if generation_result["success"] else "failed",
                "result": generation_result,
                "keyword_used": keyword.keyword,
                "execution_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en ejecución programada: {str(e)}")
            if self.current_task:
                self.current_task["status"] = "error"
                self.current_task["error"] = str(e)
            raise
    
    def _validate_scheduler_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validar configuración del scheduler"""
        required_fields = ["interval", "max_posts_per_day"]
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Campo requerido faltante: {field}")
        
        # Validar intervalo
        if config["interval"] not in [e.value for e in ScheduleInterval]:
            raise ValueError(f"Intervalo inválido: {config['interval']}")
        
        # Validar límite diario
        max_posts = config["max_posts_per_day"]
        if not isinstance(max_posts, int) or max_posts < 1 or max_posts > 50:
            raise ValueError("max_posts_per_day debe ser un entero entre 1 y 50")
        
        # Validar hora específica si se proporciona
        if "schedule_time" in config and config["schedule_time"]:
            try:
                datetime.strptime(config["schedule_time"], "%H:%M")
            except ValueError:
                raise ValueError("schedule_time debe tener formato HH:MM")
        
        return config
    
    def _calculate_next_execution(self, interval: str, schedule_time: Optional[str] = None) -> str:
        """Calcular próxima ejecución basada en el intervalo"""
        now = datetime.utcnow()
        
        if interval == ScheduleInterval.FIVE_MINUTES:
            next_exec = now + timedelta(minutes=5)
        elif interval == ScheduleInterval.FIFTEEN_MINUTES:
            next_exec = now + timedelta(minutes=15)
        elif interval == ScheduleInterval.THIRTY_MINUTES:
            next_exec = now + timedelta(minutes=30)
        elif interval == ScheduleInterval.HOURLY:
            next_exec = now + timedelta(hours=1)
        elif interval == ScheduleInterval.DAILY:
            if schedule_time:
                # Programar para hora específica del día siguiente
                hour, minute = map(int, schedule_time.split(":"))
                next_exec = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_exec <= now:
                    next_exec += timedelta(days=1)
            else:
                next_exec = now + timedelta(days=1)
        elif interval == ScheduleInterval.TWICE_DAILY:
            # Ejecutar cada 12 horas
            next_exec = now + timedelta(hours=12)
        elif interval == ScheduleInterval.WEEKLY:
            next_exec = now + timedelta(weeks=1)
        else:
            next_exec = now + timedelta(hours=1)  # Default
        
        return next_exec.isoformat()
    
    def _get_today_generation_stats(self, user_id: int) -> Dict[str, Any]:
        """Obtener estadísticas de generación del día actual"""
        today = datetime.utcnow().date()
        
        generated_today = self.db.query(Content).filter(
            and_(
                Content.user_id == user_id,
                Content.created_at >= today,
                Content.created_at < today + timedelta(days=1)
            )
        ).count()
        
        published_today = self.db.query(Content).filter(
            and_(
                Content.user_id == user_id,
                Content.status == ContentStatus.PUBLISHED,
                Content.published_at >= today,
                Content.published_at < today + timedelta(days=1)
            )
        ).count()
        
        return {
            "generated_today": generated_today,
            "published_today": published_today,
            "date": today.isoformat()
        }
    
    def _get_next_available_keyword(self, user_id: int) -> Optional[Keyword]:
        """Obtener la siguiente keyword disponible con mayor prioridad"""
        return self.db.query(Keyword).filter(
            Keyword.status == KeywordStatus.PENDING
        ).order_by(
            Keyword.priority.desc(),
            Keyword.created_at.asc()
        ).first()
    
    async def _generate_content_with_settings(self, keyword: Keyword, user_id: int, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Generar contenido con configuraciones específicas"""
        try:
            # Obtener el usuario
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"Usuario {user_id} no encontrado")
            
            # Crear ContentGenerator con el usuario correcto
            content_generator = ContentGenerator(user)
            
            # Configuración por defecto
            default_settings = {
                "word_count": 800,
                "content_type": "post",
                "writing_style": "profesional",
                "include_meta_description": True,
                "auto_interlinking": True
            }
            
            # Combinar con configuraciones del usuario
            final_settings = {**default_settings, **settings}
            
            # Generar contenido
            result = await content_generator.generate_content(
                keyword_id=keyword.id,
                user_id=user_id,
                word_count=final_settings["word_count"],
                content_type=final_settings["content_type"],
                writing_style=final_settings["writing_style"]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error generando contenido programado: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _auto_publish_content(self, content_id: int) -> bool:
        """Publicar contenido automáticamente"""
        try:
            content = self.db.query(Content).filter(Content.id == content_id).first()
            if content:
                content.status = ContentStatus.PUBLISHED
                content.published_at = datetime.utcnow()
                self.db.commit()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error publicando automáticamente: {str(e)}")
            return False
    
    def _save_scheduler_config(self, user_id: int, config: Dict[str, Any]):
        """Guardar configuración del scheduler (implementar según necesidades)"""
        # Aquí implementarías el guardado en base de datos o cache
        # Por ahora usamos un diccionario en memoria
        if not hasattr(self, '_scheduler_configs'):
            self._scheduler_configs = {}
        self._scheduler_configs[user_id] = config
    
    def _get_scheduler_config(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Obtener configuración del scheduler"""
        if not hasattr(self, '_scheduler_configs'):
            return None
        return self._scheduler_configs.get(user_id)
    
    def get_scheduler_queue(self, user_id: int) -> Dict[str, Any]:
        """Obtener cola de tareas programadas"""
        try:
            config = self._get_scheduler_config(user_id)
            if not config:
                return {"queue": [], "total": 0}
            
            # Obtener keywords disponibles ordenadas por prioridad
            available_keywords = self.db.query(Keyword).filter(
                Keyword.status == KeywordStatus.PENDING
            ).order_by(
                Keyword.priority.desc(),
                Keyword.created_at.asc()
            ).limit(20).all()
            
            queue_items = []
            for i, keyword in enumerate(available_keywords):
                # Calcular tiempo estimado de ejecución
                estimated_execution = self._calculate_estimated_execution_time(i, config["interval"])
                
                queue_items.append({
                    "position": i + 1,
                    "keyword_id": keyword.id,
                    "keyword": keyword.keyword,
                    "priority": keyword.priority,
                    "estimated_execution": estimated_execution,
                    "category": keyword.category
                })
            
            return {
                "queue": queue_items,
                "total": len(queue_items),
                "next_execution": queue_items[0]["estimated_execution"] if queue_items else None
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo cola del scheduler: {str(e)}")
            raise
    
    def _calculate_estimated_execution_time(self, position: int, interval: str) -> str:
        """Calcular tiempo estimado de ejecución para una posición en la cola"""
        now = datetime.utcnow()
        
        # Calcular intervalo en minutos
        interval_minutes = {
            ScheduleInterval.FIVE_MINUTES: 5,
            ScheduleInterval.FIFTEEN_MINUTES: 15,
            ScheduleInterval.THIRTY_MINUTES: 30,
            ScheduleInterval.HOURLY: 60,
            ScheduleInterval.DAILY: 1440,
            ScheduleInterval.TWICE_DAILY: 720,
            ScheduleInterval.WEEKLY: 10080
        }.get(interval, 60)
        
        estimated_time = now + timedelta(minutes=interval_minutes * position)
        return estimated_time.isoformat()
    
    def add_keyword_to_queue(self, user_id: int, keyword_id: int, priority: Optional[int] = None) -> Dict[str, Any]:
        """Agregar keyword específica a la cola"""
        try:
            keyword = self.db.query(Keyword).filter(Keyword.id == keyword_id).first()
            if not keyword:
                raise ValueError(f"Keyword {keyword_id} no encontrada")
            
            if keyword.status != KeywordStatus.PENDING:
                raise ValueError(f"Keyword '{keyword.keyword}' no está disponible")
            
            # Actualizar prioridad si se especifica
            if priority is not None:
                keyword.priority = priority
                self.db.commit()
            
            logger.info(f"Keyword '{keyword.keyword}' agregada a la cola con prioridad {keyword.priority}")
            
            return {
                "status": "added",
                "keyword": keyword.keyword,
                "priority": keyword.priority,
                "added_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error agregando keyword a la cola: {str(e)}")
            raise
    
    def remove_keyword_from_queue(self, user_id: int, keyword_id: int) -> Dict[str, Any]:
        """Remover keyword de la cola (marcar como reservada temporalmente)"""
        try:
            keyword = self.db.query(Keyword).filter(Keyword.id == keyword_id).first()
            if not keyword:
                raise ValueError(f"Keyword {keyword_id} no encontrada")
            
            # Marcar como reservada para excluir de la cola
            keyword.status = KeywordStatus.RESERVED
            self.db.commit()
            
            logger.info(f"Keyword '{keyword.keyword}' removida de la cola")
            
            return {
                "status": "removed",
                "keyword": keyword.keyword,
                "removed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error removiendo keyword de la cola: {str(e)}")
            raise
    
    def get_scheduler_logs(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtener logs del scheduler"""
        try:
            # Obtener contenido generado recientemente por el usuario
            recent_content = self.db.query(Content).filter(
                Content.user_id == user_id
            ).order_by(
                Content.created_at.desc()
            ).limit(limit).all()
            
            logs = []
            for content in recent_content:
                logs.append({
                    "timestamp": content.created_at.isoformat(),
                    "action": "content_generated",
                    "keyword": content.keyword.keyword if content.keyword else "N/A",
                    "title": content.title,
                    "status": content.status.value,
                    "word_count": content.word_count,
                    "published_at": content.published_at.isoformat() if content.published_at else None
                })
            
            return logs
            
        except Exception as e:
            logger.error(f"Error obteniendo logs del scheduler: {str(e)}")
            return []
    
    async def get_statistics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Obtener estadísticas del scheduler"""
        try:
            # Calcular fecha de inicio
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Obtener contenido generado en el período
            content_query = self.db.query(Content).filter(
                and_(
                    Content.user_id == user_id,
                    Content.created_at >= start_date
                )
            )
            
            total_content = content_query.count()
            published_content = content_query.filter(
                Content.status == ContentStatus.PUBLISHED
            ).count()
            
            draft_content = content_query.filter(
                Content.status == ContentStatus.DRAFT
            ).count()
            
            # Estadísticas del scheduler
            config = self._get_scheduler_config(user_id)
            scheduler_active = config and config.get("status") == "active"
            
            # Estadísticas de ejecución (simuladas por ahora)
            total_executions = total_content  # Asumimos que cada contenido es una ejecución
            successful_executions = published_content + draft_content
            failed_executions = max(0, total_executions - successful_executions)
            
            # Estadísticas de hoy
            today_stats = self._get_today_generation_stats(user_id)
            
            return {
                "period_days": days,
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "total_content_generated": total_content,
                "published_content": published_content,
                "draft_content": draft_content,
                "scheduler_active": scheduler_active,
                "today_generated": today_stats.get("generated_today", 0),
                "success_rate": round((successful_executions / total_executions * 100) if total_executions > 0 else 0, 2),
                "avg_content_per_day": round(total_content / days, 2) if days > 0 else 0,
                "last_execution": config.get("last_execution") if config else None,
                "next_execution": self._calculate_next_execution(
                    config.get("interval", "daily"),
                    config.get("schedule_time")
                ) if scheduler_active else None
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del scheduler: {str(e)}")
            # Retornar estadísticas básicas en caso de error
            return {
                "period_days": days,
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_content_generated": 0,
                "published_content": 0,
                "draft_content": 0,
                "scheduler_active": False,
                "today_generated": 0,
                "success_rate": 0,
                "avg_content_per_day": 0,
                "last_execution": None,
                "next_execution": None,
                "error": str(e)
            }
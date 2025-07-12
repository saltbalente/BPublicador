from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from app.models.keyword import Keyword, KeywordStatus
from app.models.content import Content, ContentStatus
from app.models.content_image import ContentImage
from app.models.user import User
from app.utils.logging import get_logger
import json
from collections import defaultdict

logger = get_logger(__name__)

class AnalyticsService:
    """Servicio de analytics para métricas y estadísticas de la plataforma"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_stats(self, user_id: int) -> Dict[str, Any]:
        """Obtener estadísticas principales para el dashboard"""
        try:
            # Estadísticas básicas
            total_keywords = self.db.query(Keyword).count()
            available_keywords = self.db.query(Keyword).filter(
                Keyword.status == KeywordStatus.PENDING
            ).count()
            used_keywords = self.db.query(Keyword).filter(
                Keyword.status == KeywordStatus.COMPLETED
            ).count()
            
            # Contenido del usuario
            user_content = self.db.query(Content).filter(Content.user_id == user_id)
            total_content = user_content.count()
            published_content = user_content.filter(
                Content.status == ContentStatus.PUBLISHED
            ).count()
            draft_content = user_content.filter(
                Content.status == ContentStatus.DRAFT
            ).count()
            
            # Estadísticas del día actual
            today = datetime.utcnow().date()
            today_content = user_content.filter(
                func.date(Content.created_at) == today
            ).count()
            
            # Estadísticas del mes actual
            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_content = user_content.filter(
                Content.created_at >= month_start
            ).count()
            
            # Promedio de palabras
            avg_word_count = self.db.query(func.avg(Content.word_count)).filter(
                Content.user_id == user_id,
                Content.word_count.isnot(None)
            ).scalar() or 0
            
            # Imágenes generadas
            total_images = self.db.query(ContentImage).join(Content).filter(
                Content.user_id == user_id
            ).count()
            
            return {
                "keywords": {
                    "total": total_keywords,
                    "available": available_keywords,
                    "used": used_keywords,
                    "reserved": total_keywords - available_keywords - used_keywords,
                    "usage_percentage": round((used_keywords / total_keywords * 100) if total_keywords > 0 else 0, 2)
                },
                "content": {
                    "total": total_content,
                    "published": published_content,
                    "draft": draft_content,
                    "today": today_content,
                    "this_month": month_content,
                    "avg_word_count": round(avg_word_count, 0),
                    "publish_rate": round((published_content / total_content * 100) if total_content > 0 else 0, 2)
                },
                "images": {
                    "total": total_images,
                    "avg_per_content": round((total_images / total_content) if total_content > 0 else 0, 2)
                },
                "performance": {
                    "daily_average": self._calculate_daily_average(user_id),
                    "productivity_score": self._calculate_productivity_score(user_id)
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del dashboard: {str(e)}")
            raise
    
    def get_keyword_analytics(self, user_id: Optional[int] = None, days: int = 30) -> Dict[str, Any]:
        """Obtener analytics detallados de keywords"""
        try:
            # Filtro de fecha
            date_filter = datetime.utcnow() - timedelta(days=days)
            
            # Query base
            query = self.db.query(Keyword)
            if user_id:
                query = query.join(Content).filter(Content.user_id == user_id)
            
            # Keywords más utilizadas
            most_used_keywords = self.db.query(
                Keyword.keyword,
                Keyword.category,
                func.count(Content.id).label('usage_count')
            ).join(Content).filter(
                Content.created_at >= date_filter
            )
            
            if user_id:
                most_used_keywords = most_used_keywords.filter(Content.user_id == user_id)
            
            most_used_keywords = most_used_keywords.group_by(
                Keyword.id, Keyword.keyword, Keyword.category
            ).order_by(desc('usage_count')).limit(10).all()
            
            # Keywords por categoría
            category_stats = self.db.query(
                Keyword.category,
                func.count(Keyword.id).label('total'),
                func.sum(func.case([(Keyword.status == KeywordStatus.COMPLETED, 1)], else_=0)).label('used'),
                func.sum(func.case([(Keyword.status == KeywordStatus.PENDING, 1)], else_=0)).label('available')
            ).group_by(Keyword.category).all()
            
            # Tendencias de uso por día
            daily_usage = self.db.query(
                func.date(Content.created_at).label('date'),
                func.count(Content.id).label('count')
            ).join(Keyword).filter(
                Content.created_at >= date_filter
            )
            
            if user_id:
                daily_usage = daily_usage.filter(Content.user_id == user_id)
            
            daily_usage = daily_usage.group_by(
                func.date(Content.created_at)
            ).order_by('date').all()
            
            # Keywords con mejor rendimiento (más palabras generadas)
            top_performing_keywords = self.db.query(
                Keyword.keyword,
                func.avg(Content.word_count).label('avg_words'),
                func.count(Content.id).label('content_count')
            ).join(Content).filter(
                Content.created_at >= date_filter,
                Content.word_count.isnot(None)
            )
            
            if user_id:
                top_performing_keywords = top_performing_keywords.filter(Content.user_id == user_id)
            
            top_performing_keywords = top_performing_keywords.group_by(
                Keyword.id, Keyword.keyword
            ).having(
                func.count(Content.id) >= 2  # Al menos 2 contenidos
            ).order_by(desc('avg_words')).limit(10).all()
            
            return {
                "period_days": days,
                "most_used_keywords": [
                    {
                        "keyword": kw.keyword,
                        "category": kw.category,
                        "usage_count": kw.usage_count
                    } for kw in most_used_keywords
                ],
                "category_distribution": [
                    {
                        "category": cat.category or "Sin categoría",
                        "total": cat.total,
                        "used": cat.used or 0,
                        "available": cat.available or 0,
                        "usage_rate": round((cat.used or 0) / cat.total * 100, 2) if cat.total > 0 else 0
                    } for cat in category_stats
                ],
                "daily_usage_trend": [
                    {
                        "date": usage.date.isoformat(),
                        "count": usage.count
                    } for usage in daily_usage
                ],
                "top_performing_keywords": [
                    {
                        "keyword": kw.keyword,
                        "avg_word_count": round(kw.avg_words, 0),
                        "content_count": kw.content_count
                    } for kw in top_performing_keywords
                ]
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de keywords: {str(e)}")
            raise
    
    def get_content_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Obtener analytics detallados de contenido"""
        try:
            date_filter = datetime.utcnow() - timedelta(days=days)
            
            # Contenido por estado
            content_by_status = self.db.query(
                Content.status,
                func.count(Content.id).label('count')
            ).filter(
                Content.user_id == user_id,
                Content.created_at >= date_filter
            ).group_by(Content.status).all()
            
            # Contenido por tipo
            content_by_type = self.db.query(
                Content.content_type,
                func.count(Content.id).label('count'),
                func.avg(Content.word_count).label('avg_words')
            ).filter(
                Content.user_id == user_id,
                Content.created_at >= date_filter
            ).group_by(Content.content_type).all()
            
            # Productividad por día de la semana
            productivity_by_weekday = self.db.query(
                func.extract('dow', Content.created_at).label('weekday'),
                func.count(Content.id).label('count'),
                func.avg(Content.word_count).label('avg_words')
            ).filter(
                Content.user_id == user_id,
                Content.created_at >= date_filter
            ).group_by(
                func.extract('dow', Content.created_at)
            ).order_by('weekday').all()
            
            # Contenido más reciente
            recent_content = self.db.query(Content).filter(
                Content.user_id == user_id
            ).order_by(desc(Content.created_at)).limit(10).all()
            
            # Estadísticas de longitud de contenido
            word_count_stats = self.db.query(
                func.min(Content.word_count).label('min_words'),
                func.max(Content.word_count).label('max_words'),
                func.avg(Content.word_count).label('avg_words'),
                func.count(Content.id).label('total_content')
            ).filter(
                Content.user_id == user_id,
                Content.created_at >= date_filter,
                Content.word_count.isnot(None)
            ).first()
            
            # Distribución de longitud de contenido
            word_count_distribution = self._get_word_count_distribution(user_id, date_filter)
            
            # Tiempo promedio entre creación y publicación
            avg_publish_time = self._calculate_average_publish_time(user_id, date_filter)
            
            weekday_names = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
            
            return {
                "period_days": days,
                "content_by_status": [
                    {
                        "status": status.status.value,
                        "count": status.count
                    } for status in content_by_status
                ],
                "content_by_type": [
                    {
                        "type": type_stat.content_type,
                        "count": type_stat.count,
                        "avg_word_count": round(type_stat.avg_words or 0, 0)
                    } for type_stat in content_by_type
                ],
                "productivity_by_weekday": [
                    {
                        "weekday": weekday_names[int(day.weekday)],
                        "weekday_number": int(day.weekday),
                        "count": day.count,
                        "avg_word_count": round(day.avg_words or 0, 0)
                    } for day in productivity_by_weekday
                ],
                "word_count_stats": {
                    "min": word_count_stats.min_words or 0,
                    "max": word_count_stats.max_words or 0,
                    "average": round(word_count_stats.avg_words or 0, 0),
                    "total_content": word_count_stats.total_content or 0
                },
                "word_count_distribution": word_count_distribution,
                "recent_content": [
                    {
                        "id": content.id,
                        "title": content.title,
                        "keyword": content.keyword.keyword if content.keyword else None,
                        "status": content.status.value,
                        "word_count": content.word_count,
                        "created_at": content.created_at.isoformat(),
                        "published_at": content.published_at.isoformat() if content.published_at else None
                    } for content in recent_content
                ],
                "average_publish_time_hours": avg_publish_time
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de contenido: {str(e)}")
            raise
    
    def get_usage_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Obtener analytics de uso de la plataforma"""
        try:
            date_filter = datetime.utcnow() - timedelta(days=days)
            
            # Actividad diaria
            daily_activity = self.db.query(
                func.date(Content.created_at).label('date'),
                func.count(Content.id).label('content_generated'),
                func.sum(Content.word_count).label('total_words')
            ).filter(
                Content.user_id == user_id,
                Content.created_at >= date_filter
            ).group_by(
                func.date(Content.created_at)
            ).order_by('date').all()
            
            # Horas más productivas
            hourly_productivity = self.db.query(
                func.extract('hour', Content.created_at).label('hour'),
                func.count(Content.id).label('count')
            ).filter(
                Content.user_id == user_id,
                Content.created_at >= date_filter
            ).group_by(
                func.extract('hour', Content.created_at)
            ).order_by('hour').all()
            
            # Racha de días consecutivos
            consecutive_days = self._calculate_consecutive_days(user_id)
            
            # Eficiencia (palabras por contenido)
            efficiency_trend = self.db.query(
                func.date(Content.created_at).label('date'),
                func.avg(Content.word_count).label('avg_words_per_content')
            ).filter(
                Content.user_id == user_id,
                Content.created_at >= date_filter,
                Content.word_count.isnot(None)
            ).group_by(
                func.date(Content.created_at)
            ).order_by('date').all()
            
            # Resumen de totales
            total_stats = self.db.query(
                func.count(Content.id).label('total_content'),
                func.sum(Content.word_count).label('total_words'),
                func.count(func.distinct(func.date(Content.created_at))).label('active_days')
            ).filter(
                Content.user_id == user_id,
                Content.created_at >= date_filter
            ).first()
            
            return {
                "period_days": days,
                "daily_activity": [
                    {
                        "date": activity.date.isoformat(),
                        "content_generated": activity.content_generated,
                        "total_words": activity.total_words or 0
                    } for activity in daily_activity
                ],
                "hourly_productivity": [
                    {
                        "hour": int(hour.hour),
                        "count": hour.count
                    } for hour in hourly_productivity
                ],
                "consecutive_days_streak": consecutive_days,
                "efficiency_trend": [
                    {
                        "date": eff.date.isoformat(),
                        "avg_words_per_content": round(eff.avg_words_per_content or 0, 0)
                    } for eff in efficiency_trend
                ],
                "summary": {
                    "total_content": total_stats.total_content or 0,
                    "total_words": total_stats.total_words or 0,
                    "active_days": total_stats.active_days or 0,
                    "avg_content_per_day": round((total_stats.total_content or 0) / days, 2),
                    "avg_words_per_day": round((total_stats.total_words or 0) / days, 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo analytics de uso: {str(e)}")
            raise
    
    def get_performance_report(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generar reporte de rendimiento para un período específico"""
        try:
            # Contenido generado en el período
            content_in_period = self.db.query(Content).filter(
                Content.user_id == user_id,
                Content.created_at >= start_date,
                Content.created_at <= end_date
            )
            
            total_content = content_in_period.count()
            published_content = content_in_period.filter(
                Content.status == ContentStatus.PUBLISHED
            ).count()
            
            # Palabras totales
            total_words = self.db.query(
                func.sum(Content.word_count)
            ).filter(
                Content.user_id == user_id,
                Content.created_at >= start_date,
                Content.created_at <= end_date,
                Content.word_count.isnot(None)
            ).scalar() or 0
            
            # Keywords utilizadas
            unique_keywords = self.db.query(
                func.count(func.distinct(Content.keyword_id))
            ).filter(
                Content.user_id == user_id,
                Content.created_at >= start_date,
                Content.created_at <= end_date,
                Content.keyword_id.isnot(None)
            ).scalar() or 0
            
            # Imágenes generadas
            images_generated = self.db.query(ContentImage).join(Content).filter(
                Content.user_id == user_id,
                Content.created_at >= start_date,
                Content.created_at <= end_date
            ).count()
            
            # Días activos
            active_days = self.db.query(
                func.count(func.distinct(func.date(Content.created_at)))
            ).filter(
                Content.user_id == user_id,
                Content.created_at >= start_date,
                Content.created_at <= end_date
            ).scalar() or 0
            
            # Calcular métricas
            period_days = (end_date - start_date).days + 1
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_days": period_days,
                    "active_days": active_days
                },
                "content_metrics": {
                    "total_content": total_content,
                    "published_content": published_content,
                    "draft_content": total_content - published_content,
                    "publish_rate": round((published_content / total_content * 100) if total_content > 0 else 0, 2),
                    "avg_content_per_day": round(total_content / period_days, 2),
                    "avg_content_per_active_day": round(total_content / active_days, 2) if active_days > 0 else 0
                },
                "word_metrics": {
                    "total_words": total_words,
                    "avg_words_per_content": round(total_words / total_content, 0) if total_content > 0 else 0,
                    "avg_words_per_day": round(total_words / period_days, 0),
                    "avg_words_per_active_day": round(total_words / active_days, 0) if active_days > 0 else 0
                },
                "keyword_metrics": {
                    "unique_keywords_used": unique_keywords,
                    "avg_keywords_per_day": round(unique_keywords / period_days, 2)
                },
                "image_metrics": {
                    "total_images": images_generated,
                    "avg_images_per_content": round(images_generated / total_content, 2) if total_content > 0 else 0
                },
                "productivity_score": self._calculate_productivity_score_for_period(user_id, start_date, end_date)
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte de rendimiento: {str(e)}")
            raise
    
    def _calculate_daily_average(self, user_id: int, days: int = 30) -> float:
        """Calcular promedio diario de contenido generado"""
        date_filter = datetime.utcnow() - timedelta(days=days)
        
        total_content = self.db.query(Content).filter(
            Content.user_id == user_id,
            Content.created_at >= date_filter
        ).count()
        
        return round(total_content / days, 2)
    
    def _calculate_productivity_score(self, user_id: int) -> int:
        """Calcular score de productividad (0-100)"""
        try:
            # Últimos 30 días
            date_filter = datetime.utcnow() - timedelta(days=30)
            
            # Métricas para el score
            content_count = self.db.query(Content).filter(
                Content.user_id == user_id,
                Content.created_at >= date_filter
            ).count()
            
            published_count = self.db.query(Content).filter(
                Content.user_id == user_id,
                Content.created_at >= date_filter,
                Content.status == ContentStatus.PUBLISHED
            ).count()
            
            avg_words = self.db.query(func.avg(Content.word_count)).filter(
                Content.user_id == user_id,
                Content.created_at >= date_filter,
                Content.word_count.isnot(None)
            ).scalar() or 0
            
            # Calcular score
            score = 0
            
            # Puntos por cantidad de contenido (max 40 puntos)
            score += min(40, content_count * 2)
            
            # Puntos por tasa de publicación (max 30 puntos)
            if content_count > 0:
                publish_rate = published_count / content_count
                score += int(publish_rate * 30)
            
            # Puntos por calidad (palabras promedio) (max 30 puntos)
            if avg_words >= 800:
                score += 30
            elif avg_words >= 600:
                score += 20
            elif avg_words >= 400:
                score += 10
            
            return min(100, score)
            
        except Exception as e:
            logger.error(f"Error calculando score de productividad: {str(e)}")
            return 0
    
    def _get_word_count_distribution(self, user_id: int, date_filter: datetime) -> List[Dict[str, Any]]:
        """Obtener distribución de longitud de contenido"""
        ranges = [
            (0, 300, "Muy corto"),
            (301, 600, "Corto"),
            (601, 1000, "Medio"),
            (1001, 1500, "Largo"),
            (1501, float('inf'), "Muy largo")
        ]
        
        distribution = []
        
        for min_words, max_words, label in ranges:
            if max_words == float('inf'):
                count = self.db.query(Content).filter(
                    Content.user_id == user_id,
                    Content.created_at >= date_filter,
                    Content.word_count >= min_words
                ).count()
            else:
                count = self.db.query(Content).filter(
                    Content.user_id == user_id,
                    Content.created_at >= date_filter,
                    Content.word_count >= min_words,
                    Content.word_count <= max_words
                ).count()
            
            distribution.append({
                "range": label,
                "min_words": min_words,
                "max_words": max_words if max_words != float('inf') else None,
                "count": count
            })
        
        return distribution
    
    def _calculate_average_publish_time(self, user_id: int, date_filter: datetime) -> float:
        """Calcular tiempo promedio entre creación y publicación en horas"""
        published_content = self.db.query(Content).filter(
            Content.user_id == user_id,
            Content.created_at >= date_filter,
            Content.status == ContentStatus.PUBLISHED,
            Content.published_at.isnot(None)
        ).all()
        
        if not published_content:
            return 0.0
        
        total_hours = 0
        for content in published_content:
            time_diff = content.published_at - content.created_at
            total_hours += time_diff.total_seconds() / 3600
        
        return round(total_hours / len(published_content), 2)
    
    def _calculate_consecutive_days(self, user_id: int) -> int:
        """Calcular racha de días consecutivos con actividad"""
        try:
            # Obtener fechas únicas con actividad (últimos 90 días)
            date_filter = datetime.utcnow() - timedelta(days=90)
            
            active_dates = self.db.query(
                func.distinct(func.date(Content.created_at)).label('date')
            ).filter(
                Content.user_id == user_id,
                Content.created_at >= date_filter
            ).order_by(desc('date')).all()
            
            if not active_dates:
                return 0
            
            # Convertir a lista de fechas
            dates = [date.date for date in active_dates]
            
            # Calcular racha consecutiva desde hoy hacia atrás
            consecutive = 0
            current_date = datetime.utcnow().date()
            
            for i in range(len(dates)):
                expected_date = current_date - timedelta(days=i)
                if expected_date in dates:
                    consecutive += 1
                else:
                    break
            
            return consecutive
            
        except Exception as e:
            logger.error(f"Error calculando días consecutivos: {str(e)}")
            return 0
    
    def _calculate_productivity_score_for_period(self, user_id: int, start_date: datetime, end_date: datetime) -> int:
        """Calcular score de productividad para un período específico"""
        try:
            period_days = (end_date - start_date).days + 1
            
            content_count = self.db.query(Content).filter(
                Content.user_id == user_id,
                Content.created_at >= start_date,
                Content.created_at <= end_date
            ).count()
            
            published_count = self.db.query(Content).filter(
                Content.user_id == user_id,
                Content.created_at >= start_date,
                Content.created_at <= end_date,
                Content.status == ContentStatus.PUBLISHED
            ).count()
            
            # Score basado en contenido por día
            daily_content = content_count / period_days
            content_score = min(50, int(daily_content * 25))  # Max 50 puntos
            
            # Score basado en tasa de publicación
            publish_rate = published_count / content_count if content_count > 0 else 0
            publish_score = int(publish_rate * 50)  # Max 50 puntos
            
            return min(100, content_score + publish_score)
            
        except Exception as e:
            logger.error(f"Error calculando score de productividad para período: {str(e)}")
            return 0
    
    def export_analytics_data(self, user_id: int, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Exportar datos de analytics para un período"""
        try:
            # Recopilar todos los datos
            dashboard_stats = self.get_dashboard_stats(user_id)
            keyword_analytics = self.get_keyword_analytics(user_id, (end_date - start_date).days)
            content_analytics = self.get_content_analytics(user_id, (end_date - start_date).days)
            usage_analytics = self.get_usage_analytics(user_id, (end_date - start_date).days)
            performance_report = self.get_performance_report(user_id, start_date, end_date)
            
            return {
                "export_info": {
                    "user_id": user_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "generated_at": datetime.utcnow().isoformat()
                },
                "dashboard_stats": dashboard_stats,
                "keyword_analytics": keyword_analytics,
                "content_analytics": content_analytics,
                "usage_analytics": usage_analytics,
                "performance_report": performance_report
            }
            
        except Exception as e:
            logger.error(f"Error exportando datos de analytics: {str(e)}")
            raise
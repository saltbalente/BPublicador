from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, timedelta
import json
import re
from slugify import slugify

from app.models.landing_page import LandingPage, LandingTemplate, LandingAnalytics, LandingSEOConfig
from app.models.user import User
from app.core.exceptions import ValidationError, NotFoundError

# ============================================================================
# SERVICIO PRINCIPAL PARA LANDING PAGES
# ============================================================================

class LandingPageService:
    """
    Servicio para manejar la lógica de negocio de las landing pages
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========================================================================
    # MÉTODOS PARA LANDING PAGES
    # ========================================================================
    
    def create_landing_page(self, user_id: int, landing_data: Dict[str, Any]) -> LandingPage:
        """
        Crear una nueva landing page
        """
        # Validar que el usuario existe
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("Usuario no encontrado")
        
        # Generar slug único
        base_slug = slugify(landing_data.get("title", "landing-page"))
        slug = self._generate_unique_slug(base_slug)
        
        # Crear la landing page
        landing_page = LandingPage(
            title=landing_data.get("title"),
            slug=slug,
            description=landing_data.get("description"),
            html_content=landing_data.get("html_content"),
            css_content=landing_data.get("css_content"),
            js_content=landing_data.get("js_content"),
            seo_title=landing_data.get("seo_title"),
            seo_description=landing_data.get("seo_description"),
            seo_keywords=landing_data.get("seo_keywords"),
            settings=landing_data.get("settings", {}),
            user_id=user_id,
            template_id=landing_data.get("template_id")
        )
        
        self.db.add(landing_page)
        self.db.commit()
        self.db.refresh(landing_page)
        
        return landing_page
    
    def get_landing_page(self, landing_id: int, user_id: Optional[int] = None) -> LandingPage:
        """
        Obtener una landing page por ID
        """
        query = self.db.query(LandingPage).filter(LandingPage.id == landing_id)
        
        if user_id:
            query = query.filter(LandingPage.user_id == user_id)
        
        landing_page = query.first()
        if not landing_page:
            raise NotFoundError("Landing page no encontrada")
        
        return landing_page
    
    def get_landing_pages_by_user(self, user_id: int, skip: int = 0, limit: int = 20) -> List[LandingPage]:
        """
        Obtener todas las landing pages de un usuario
        """
        return self.db.query(LandingPage).filter(
            LandingPage.user_id == user_id
        ).order_by(desc(LandingPage.created_at)).offset(skip).limit(limit).all()
    
    def update_landing_page(self, landing_id: int, user_id: int, update_data: Dict[str, Any]) -> LandingPage:
        """
        Actualizar una landing page
        """
        landing_page = self.get_landing_page(landing_id, user_id)
        
        # Actualizar campos permitidos
        for field, value in update_data.items():
            if hasattr(landing_page, field) and field not in ['id', 'user_id', 'created_at']:
                setattr(landing_page, field, value)
        
        # Si se actualiza el título, regenerar slug
        if 'title' in update_data:
            base_slug = slugify(update_data['title'])
            if base_slug != landing_page.slug:
                landing_page.slug = self._generate_unique_slug(base_slug, exclude_id=landing_id)
        
        self.db.commit()
        self.db.refresh(landing_page)
        
        return landing_page
    
    def delete_landing_page(self, landing_id: int, user_id: int) -> bool:
        """
        Eliminar una landing page
        """
        landing_page = self.get_landing_page(landing_id, user_id)
        
        self.db.delete(landing_page)
        self.db.commit()
        
        return True
    
    def publish_landing_page(self, landing_id: int, user_id: int) -> LandingPage:
        """
        Publicar una landing page
        """
        landing_page = self.get_landing_page(landing_id, user_id)
        
        landing_page.is_published = True
        landing_page.published_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(landing_page)
        
        return landing_page
    
    def unpublish_landing_page(self, landing_id: int, user_id: int) -> LandingPage:
        """
        Despublicar una landing page
        """
        landing_page = self.get_landing_page(landing_id, user_id)
        
        landing_page.is_published = False
        
        self.db.commit()
        self.db.refresh(landing_page)
        
        return landing_page
    
    # ========================================================================
    # MÉTODOS PARA TEMPLATES
    # ========================================================================
    
    def get_templates(self, category: Optional[str] = None, is_premium: Optional[bool] = None) -> List[LandingTemplate]:
        """
        Obtener templates disponibles
        """
        query = self.db.query(LandingTemplate).filter(LandingTemplate.is_active == True)
        
        if category:
            query = query.filter(LandingTemplate.category == category)
        
        if is_premium is not None:
            query = query.filter(LandingTemplate.is_premium == is_premium)
        
        return query.order_by(asc(LandingTemplate.name)).all()
    
    def get_template(self, template_id: int) -> LandingTemplate:
        """
        Obtener un template por ID
        """
        template = self.db.query(LandingTemplate).filter(
            and_(LandingTemplate.id == template_id, LandingTemplate.is_active == True)
        ).first()
        
        if not template:
            raise NotFoundError("Template no encontrado")
        
        return template
    
    def create_landing_from_template(self, user_id: int, template_id: int, landing_data: Dict[str, Any]) -> LandingPage:
        """
        Crear una landing page basada en un template
        """
        template = self.get_template(template_id)
        
        # Combinar datos del template con datos personalizados
        combined_data = {
            "title": landing_data.get("title", f"Landing basada en {template.name}"),
            "description": landing_data.get("description"),
            "html_content": template.html_template,
            "css_content": template.css_template,
            "js_content": template.js_template,
            "settings": {**template.default_settings or {}, **landing_data.get("settings", {})},
            "template_id": template_id
        }
        
        return self.create_landing_page(user_id, combined_data)
    
    # ========================================================================
    # MÉTODOS PARA SEO
    # ========================================================================
    
    def update_seo_config(self, landing_id: int, user_id: int, seo_data: Dict[str, Any]) -> LandingSEOConfig:
        """
        Actualizar configuración SEO de una landing page
        """
        landing_page = self.get_landing_page(landing_id, user_id)
        
        # Buscar configuración SEO existente o crear nueva
        seo_config = self.db.query(LandingSEOConfig).filter(
            LandingSEOConfig.landing_page_id == landing_id
        ).first()
        
        if not seo_config:
            seo_config = LandingSEOConfig(landing_page_id=landing_id)
            self.db.add(seo_config)
        
        # Actualizar campos SEO
        for field, value in seo_data.items():
            if hasattr(seo_config, field) and field not in ['id', 'landing_page_id', 'created_at']:
                setattr(seo_config, field, value)
        
        self.db.commit()
        self.db.refresh(seo_config)
        
        return seo_config
    
    def analyze_seo_score(self, landing_id: int, user_id: int) -> Dict[str, Any]:
        """
        Analizar el score SEO de una landing page
        """
        landing_page = self.get_landing_page(landing_id, user_id)
        
        score = 0
        recommendations = []
        
        # Verificar título SEO
        if landing_page.seo_title:
            if 30 <= len(landing_page.seo_title) <= 60:
                score += 20
            else:
                recommendations.append("El título SEO debe tener entre 30 y 60 caracteres")
        else:
            recommendations.append("Falta el título SEO")
        
        # Verificar meta description
        if landing_page.seo_description:
            if 120 <= len(landing_page.seo_description) <= 160:
                score += 20
            else:
                recommendations.append("La meta descripción debe tener entre 120 y 160 caracteres")
        else:
            recommendations.append("Falta la meta descripción")
        
        # Verificar keywords
        if landing_page.seo_keywords:
            keywords = [k.strip() for k in landing_page.seo_keywords.split(',')]
            if 3 <= len(keywords) <= 10:
                score += 15
            else:
                recommendations.append("Se recomiendan entre 3 y 10 keywords")
        else:
            recommendations.append("Faltan las keywords")
        
        # Verificar contenido HTML
        if landing_page.html_content:
            # Verificar headings
            if '<h1' in landing_page.html_content:
                score += 15
            else:
                recommendations.append("Falta el heading H1")
            
            # Verificar imágenes con alt
            img_count = landing_page.html_content.count('<img')
            alt_count = landing_page.html_content.count('alt=')
            if img_count > 0 and alt_count >= img_count:
                score += 15
            elif img_count > 0:
                recommendations.append("Algunas imágenes no tienen texto alternativo (alt)")
            
            # Verificar longitud del contenido
            text_content = re.sub(r'<[^>]+>', '', landing_page.html_content)
            word_count = len(text_content.split())
            if word_count >= 300:
                score += 15
            else:
                recommendations.append("El contenido debería tener al menos 300 palabras")
        
        return {
            "score": min(score, 100),
            "recommendations": recommendations,
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    # ========================================================================
    # MÉTODOS PARA ANALYTICS
    # ========================================================================
    
    def record_page_view(self, landing_id: int, visitor_data: Dict[str, Any]) -> bool:
        """
        Registrar una vista de página
        """
        today = datetime.utcnow().date()
        
        # Buscar o crear registro de analytics para hoy
        analytics = self.db.query(LandingAnalytics).filter(
            and_(
                LandingAnalytics.landing_page_id == landing_id,
                LandingAnalytics.date >= today,
                LandingAnalytics.date < today + timedelta(days=1)
            )
        ).first()
        
        if not analytics:
            analytics = LandingAnalytics(
                landing_page_id=landing_id,
                date=datetime.utcnow(),
                traffic_sources={},
                device_types={},
                browser_stats={}
            )
            self.db.add(analytics)
        
        # Incrementar vistas
        analytics.page_views += 1
        
        # Actualizar estadísticas de tráfico
        source = visitor_data.get('source', 'direct')
        device = visitor_data.get('device', 'desktop')
        browser = visitor_data.get('browser', 'unknown')
        
        analytics.traffic_sources[source] = analytics.traffic_sources.get(source, 0) + 1
        analytics.device_types[device] = analytics.device_types.get(device, 0) + 1
        analytics.browser_stats[browser] = analytics.browser_stats.get(browser, 0) + 1
        
        self.db.commit()
        return True
    
    def get_analytics_summary(self, landing_id: int, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Obtener resumen de analytics de una landing page
        """
        landing_page = self.get_landing_page(landing_id, user_id)
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        analytics = self.db.query(LandingAnalytics).filter(
            and_(
                LandingAnalytics.landing_page_id == landing_id,
                LandingAnalytics.date >= start_date
            )
        ).all()
        
        total_views = sum(a.page_views for a in analytics)
        total_visitors = sum(a.unique_visitors for a in analytics)
        avg_bounce_rate = sum(a.bounce_rate for a in analytics) / len(analytics) if analytics else 0
        
        return {
            "total_views": total_views,
            "total_visitors": total_visitors,
            "avg_bounce_rate": round(avg_bounce_rate, 2),
            "period_days": days,
            "daily_data": [
                {
                    "date": a.date.isoformat(),
                    "views": a.page_views,
                    "visitors": a.unique_visitors,
                    "bounce_rate": a.bounce_rate
                }
                for a in analytics
            ]
        }
    
    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================
    
    def _generate_unique_slug(self, base_slug: str, exclude_id: Optional[int] = None) -> str:
        """
        Generar un slug único para una landing page
        """
        slug = base_slug
        counter = 1
        
        while True:
            query = self.db.query(LandingPage).filter(LandingPage.slug == slug)
            if exclude_id:
                query = query.filter(LandingPage.id != exclude_id)
            
            if not query.first():
                return slug
            
            slug = f"{base_slug}-{counter}"
            counter += 1
    
    def get_landing_page_by_slug(self, slug: str) -> LandingPage:
        """
        Obtener una landing page por su slug (para acceso público)
        """
        landing_page = self.db.query(LandingPage).filter(
            and_(
                LandingPage.slug == slug,
                LandingPage.is_published == True,
                LandingPage.is_active == True
            )
        ).first()
        
        if not landing_page:
            raise NotFoundError("Landing page no encontrada")
        
        return landing_page
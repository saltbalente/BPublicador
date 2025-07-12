from datetime import datetime
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.models.content import Content, ContentStatus
from app.models.category import Category
from app.models.tag import Tag
from app.models.keyword import Keyword
from app.models.seo_schema import SEOSchema
from app.utils.logging import get_logger
from app.core.config import settings
import os
import json
from pathlib import Path
from urllib.parse import quote
import re

logger = get_logger(__name__)

class PublicationEngine:
    """Motor de publicación web para generar sitio público"""
    
    def __init__(self, db: Session):
        self.db = db
        self.templates_dir = Path("app/templates")
        self.public_dir = Path("public")
        self.static_dir = Path("static")
        
        # Configurar Jinja2
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Registrar filtros personalizados
        self._register_template_filters()
        
        # Crear directorios si no existen
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Crear directorios necesarios"""
        directories = [
            self.templates_dir,
            self.public_dir,
            self.public_dir / "posts",
            self.public_dir / "categories",
            self.public_dir / "tags",
            self.public_dir / "assets",
            self.public_dir / "assets" / "css",
            self.public_dir / "assets" / "js",
            self.public_dir / "assets" / "images"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _register_template_filters(self):
        """Registrar filtros personalizados para Jinja2"""
        
        def slugify(text):
            """Convertir texto a slug URL-friendly"""
            if not text:
                return ""
            # Convertir a minúsculas y reemplazar espacios/caracteres especiales
            text = re.sub(r'[^\w\s-]', '', text.lower())
            text = re.sub(r'[-\s]+', '-', text)
            return text.strip('-')
        
        def truncate_words(text, length=50):
            """Truncar texto por número de palabras"""
            if not text:
                return ""
            words = text.split()
            if len(words) <= length:
                return text
            return ' '.join(words[:length]) + '...'
        
        def format_date(date, format='%d de %B, %Y'):
            """Formatear fecha"""
            if not date:
                return ""
            # Mapeo de meses en español
            months = {
                'January': 'enero', 'February': 'febrero', 'March': 'marzo',
                'April': 'abril', 'May': 'mayo', 'June': 'junio',
                'July': 'julio', 'August': 'agosto', 'September': 'septiembre',
                'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
            }
            
            formatted = date.strftime(format)
            for en_month, es_month in months.items():
                formatted = formatted.replace(en_month, es_month)
            return formatted
        
        def reading_time(text, wpm=200):
            """Calcular tiempo de lectura estimado"""
            if not text:
                return "0 min"
            word_count = len(text.split())
            minutes = max(1, round(word_count / wpm))
            return f"{minutes} min"
        
        # Registrar los filtros en el entorno Jinja2
        self.jinja_env.filters['slugify'] = slugify
        self.jinja_env.filters['truncate_words'] = truncate_words
        self.jinja_env.filters['format_date'] = format_date
        self.jinja_env.filters['reading_time'] = reading_time
    
    def generate_full_site(self) -> Dict[str, Any]:
        """Generar sitio web completo"""
        try:
            logger.info("Iniciando generación completa del sitio web")
            
            results = {
                "pages_generated": 0,
                "posts_generated": 0,
                "categories_generated": 0,
                "tags_generated": 0,
                "errors": []
            }
            
            # 1. Generar página de inicio
            try:
                self._generate_homepage()
                results["pages_generated"] += 1
            except Exception as e:
                results["errors"].append(f"Error generando homepage: {str(e)}")
            
            # 2. Generar posts individuales
            posts = self.db.query(Content).filter(
                Content.status == ContentStatus.PUBLISHED
            ).order_by(desc(Content.created_at)).all()
            
            for post in posts:
                try:
                    self._generate_post_page(post)
                    results["posts_generated"] += 1
                except Exception as e:
                    results["errors"].append(f"Error generando post {post.id}: {str(e)}")
            
            # 3. Generar páginas de categorías
            categories = self.db.query(Category).all()
            for category in categories:
                try:
                    self._generate_category_page(category)
                    results["categories_generated"] += 1
                except Exception as e:
                    results["errors"].append(f"Error generando categoría {category.id}: {str(e)}")
            
            # 4. Generar páginas de tags
            tags = self.db.query(Tag).all()
            for tag in tags:
                try:
                    self._generate_tag_page(tag)
                    results["tags_generated"] += 1
                except Exception as e:
                    results["errors"].append(f"Error generando tag {tag.id}: {str(e)}")
            
            # 5. Generar páginas especiales
            try:
                self._generate_archive_page()
                results["pages_generated"] += 1
            except Exception as e:
                results["errors"].append(f"Error generando página de archivo: {str(e)}")
            
            try:
                self._generate_search_page()
                results["pages_generated"] += 1
            except Exception as e:
                results["errors"].append(f"Error generando página de búsqueda: {str(e)}")
            
            try:
                self._generate_404_page()
                results["pages_generated"] += 1
            except Exception as e:
                results["errors"].append(f"Error generando página 404: {str(e)}")
            
            # 6. Generar archivos especiales
            try:
                self._generate_sitemap()
                self._generate_rss_feed()
                self._generate_robots_txt()
                results["pages_generated"] += 3
            except Exception as e:
                results["errors"].append(f"Error generando archivos especiales: {str(e)}")
            
            # 7. Copiar assets estáticos
            try:
                self._copy_static_assets()
            except Exception as e:
                results["errors"].append(f"Error copiando assets: {str(e)}")
            
            logger.info(f"Generación completada: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Error en generación completa del sitio: {str(e)}")
            raise
    
    def _generate_homepage(self):
        """Generar página de inicio"""
        # Obtener contenido destacado
        featured_posts = self.db.query(Content).filter(
            Content.status == ContentStatus.PUBLISHED
        ).order_by(desc(Content.created_at)).limit(6).all()
        
        # Obtener categorías populares
        categories = self.db.query(Category).limit(10).all()
        
        # Obtener estadísticas del sitio
        total_posts = self.db.query(Content).filter(
            Content.status == ContentStatus.PUBLISHED
        ).count()
        
        context = {
            "title": "Inicio - Autopublicador Web",
            "meta_description": "Descubre contenido sobre brujería, esoterismo y magia. Artículos, rituales, hechizos y más.",
            "featured_posts": featured_posts,
            "categories": categories,
            "total_posts": total_posts,
            "current_page": "home"
        }
        
        template = self.jinja_env.get_template("homepage.html")
        html_content = template.render(**context)
        
        # Guardar archivo
        output_path = self.public_dir / "index.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_post_page(self, post: Content):
        """Generar página individual de post"""
        # Obtener datos relacionados
        category = post.category
        tags = post.tags
        keyword = post.keyword
        seo_schema = post.seo_schema
        images = post.images
        
        # Posts relacionados (misma categoría)
        related_posts = []
        if category:
            related_posts = self.db.query(Content).filter(
                and_(
                    Content.category_id == category.id,
                    Content.id != post.id,
                    Content.status == ContentStatus.PUBLISHED
                )
            ).limit(3).all()
        
        # Generar Schema.org markup
        schema_markup = self._generate_schema_markup(post, seo_schema)
        
        context = {
            "post": post,
            "title": post.title,
            "meta_description": post.meta_description or post.title,
            "category": category,
            "tags": tags,
            "keyword": keyword,
            "images": images,
            "related_posts": related_posts,
            "schema_markup": schema_markup,
            "current_page": "post"
        }
        
        template = self.jinja_env.get_template("post.html")
        html_content = template.render(**context)
        
        # Crear directorio y guardar archivo
        post_dir = self.public_dir / "posts" / post.slug
        post_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = post_dir / "index.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_category_page(self, category: Category):
        """Generar página de categoría"""
        # Obtener posts de la categoría
        posts = self.db.query(Content).filter(
            and_(
                Content.category_id == category.id,
                Content.status == ContentStatus.PUBLISHED
            )
        ).order_by(desc(Content.created_at)).all()
        
        context = {
            "category": category,
            "title": f"{category.name} - Autopublicador Web",
            "meta_description": f"Artículos sobre {category.name}. {category.description or ''}",
            "posts": posts,
            "current_page": "category"
        }
        
        template = self.jinja_env.get_template("category.html")
        html_content = template.render(**context)
        
        # Crear directorio y guardar archivo
        category_dir = self.public_dir / "categories" / category.slug
        category_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = category_dir / "index.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_tag_page(self, tag: Tag):
        """Generar página de tag"""
        # Obtener posts del tag
        posts = [content for content in tag.content_items 
                if content.status == ContentStatus.PUBLISHED]
        posts.sort(key=lambda x: x.created_at, reverse=True)
        
        context = {
            "tag": tag,
            "title": f"#{tag.name} - Autopublicador Web",
            "meta_description": f"Artículos etiquetados con {tag.name}",
            "posts": posts,
            "current_page": "tag"
        }
        
        template = self.jinja_env.get_template("tag.html")
        html_content = template.render(**context)
        
        # Crear directorio y guardar archivo
        tag_dir = self.public_dir / "tags" / tag.slug
        tag_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = tag_dir / "index.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_schema_markup(self, post: Content, seo_schema: Optional[SEOSchema]) -> str:
        """Generar markup Schema.org para SEO"""
        if not seo_schema:
            return ""
        
        try:
            schema_data = {
                "@context": "https://schema.org",
                "@type": seo_schema.schema_type,
                "headline": post.title,
                "description": post.meta_description or post.title,
                "datePublished": post.created_at.isoformat(),
                "dateModified": post.updated_at.isoformat() if post.updated_at else post.created_at.isoformat(),
                "author": {
                    "@type": "Person",
                    "name": post.user.username if post.user else "Autopublicador Web"
                },
                "publisher": {
                    "@type": "Organization",
                    "name": "Autopublicador Web"
                }
            }
            
            # Agregar datos específicos del schema
            if seo_schema.schema_data:
                schema_data.update(seo_schema.schema_data)
            
            # Agregar imagen si existe
            if post.images:
                featured_image = next((img for img in post.images if img.is_featured), post.images[0])
                schema_data["image"] = {
                    "@type": "ImageObject",
                    "url": featured_image.image_path,
                    "description": featured_image.alt_text or post.title
                }
            
            return json.dumps(schema_data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.warning(f"Error generando schema markup: {str(e)}")
            return ""
    
    def _generate_sitemap(self):
        """Generar sitemap XML"""
        posts = self.db.query(Content).filter(
            Content.status == ContentStatus.PUBLISHED
        ).order_by(desc(Content.updated_at)).all()
        
        categories = self.db.query(Category).all()
        tags = self.db.query(Tag).all()
        
        context = {
            "posts": posts,
            "categories": categories,
            "tags": tags,
            "base_url": "https://tu-dominio.com"  # Configurar en settings
        }
        
        template = self.jinja_env.get_template("sitemap.xml")
        xml_content = template.render(**context)
        
        output_path = self.public_dir / "sitemap.xml"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
    
    def _generate_rss_feed(self):
        """Generar feed RSS"""
        posts = self.db.query(Content).filter(
            Content.status == ContentStatus.PUBLISHED
        ).order_by(desc(Content.created_at)).limit(20).all()
        
        context = {
            "posts": posts,
            "site_title": "Autopublicador Web",
            "site_description": "Contenido sobre brujería, esoterismo y magia",
            "base_url": "https://tu-dominio.com",
            "build_date": datetime.utcnow()
        }
        
        template = self.jinja_env.get_template("rss.xml")
        xml_content = template.render(**context)
        
        output_path = self.public_dir / "rss.xml"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
    
    def _generate_robots_txt(self):
        """Generar robots.txt"""
        robots_content = """User-agent: *
Allow: /

Sitemap: https://tu-dominio.com/sitemap.xml"""
        
        output_path = self.public_dir / "robots.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(robots_content)
    
    def _copy_static_assets(self):
        """Copiar archivos estáticos (CSS, JS, imágenes)"""
        import shutil
        
        # Copiar imágenes de contenido
        source_images = Path("images")
        if source_images.exists():
            dest_images = self.public_dir / "assets" / "images"
            if dest_images.exists():
                shutil.rmtree(dest_images)
            shutil.copytree(source_images, dest_images)
        
        # Copiar archivos estáticos del backend
        source_static = Path("static")
        if source_static.exists():
            dest_static = self.public_dir / "assets"
            for item in source_static.iterdir():
                if item.is_file():
                    shutil.copy2(item, dest_static)
                elif item.is_dir():
                    dest_dir = dest_static / item.name
                    if dest_dir.exists():
                        shutil.rmtree(dest_dir)
                    shutil.copytree(item, dest_dir)
    
    def regenerate_post(self, post_id: int) -> bool:
        """Regenerar página individual de un post"""
        try:
            post = self.db.query(Content).filter(Content.id == post_id).first()
            if not post or post.status != ContentStatus.PUBLISHED:
                return False
            
            self._generate_post_page(post)
            logger.info(f"Post {post_id} regenerado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error regenerando post {post_id}: {str(e)}")
            return False
    
    def _generate_archive_page(self):
        """Generar página de archivo"""
        from collections import defaultdict
        
        # Obtener todos los posts publicados
        posts = self.db.query(Content).filter(
            Content.status == ContentStatus.PUBLISHED
        ).order_by(desc(Content.created_at)).all()
        
        # Organizar posts por año y mes
        posts_by_year = defaultdict(lambda: {"count": 0, "months": defaultdict(list)})
        
        for post in posts:
            year = post.created_at.year
            month = post.created_at.strftime("%Y-%m")
            posts_by_year[year]["count"] += 1
            posts_by_year[year]["months"][month].append(post)
        
        # Estadísticas
        total_posts = len(posts)
        total_categories = self.db.query(Category).count()
        total_tags = self.db.query(Tag).count()
        
        context = {
            "title": "Archivo - Autopublicador Web",
            "meta_description": "Archivo completo de artículos organizados por fecha",
            "posts_by_year": dict(posts_by_year),
            "all_posts": posts,
            "total_posts": total_posts,
            "total_categories": total_categories,
            "total_tags": total_tags,
            "current_page": "archive"
        }
        
        template = self.jinja_env.get_template("archive.html")
        html_content = template.render(**context)
        
        # Crear directorio y guardar archivo
        archive_dir = self.public_dir / "archivo"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = archive_dir / "index.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_search_page(self):
        """Generar página de búsqueda"""
        # Obtener categorías para el formulario
        categories = self.db.query(Category).all()
        
        # Búsquedas populares
        popular_searches = ["rituales", "hechizos", "tarot", "astrología", "meditación"]
        
        context = {
            "title": "Búsqueda - Autopublicador Web",
            "meta_description": "Busca contenido sobre brujería, esoterismo y magia",
            "categories": categories,
            "popular_searches": popular_searches,
            "current_page": "search"
        }
        
        template = self.jinja_env.get_template("search.html")
        html_content = template.render(**context)
        
        # Crear directorio y guardar archivo
        search_dir = self.public_dir / "buscar"
        search_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = search_dir / "index.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _generate_404_page(self):
        """Generar página de error 404"""
        # Obtener contenido para la página 404
        popular_categories = self.db.query(Category).limit(5).all()
        recent_posts = self.db.query(Content).filter(
            Content.status == ContentStatus.PUBLISHED
        ).order_by(desc(Content.created_at)).limit(5).all()
        
        popular_tags = self.db.query(Tag).limit(15).all()
        
        context = {
            "title": "Página no encontrada - Autopublicador Web",
            "meta_description": "La página que buscas no existe",
            "popular_categories": popular_categories,
            "recent_posts": recent_posts,
            "popular_tags": popular_tags,
            "current_page": "404"
        }
        
        template = self.jinja_env.get_template("404.html")
        html_content = template.render(**context)
        
        # Guardar archivo
        output_path = self.public_dir / "404.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def get_site_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sitio generado"""
        try:
            stats = {
                "total_files": 0,
                "total_size_mb": 0,
                "last_generation": None,
                "pages_by_type": {
                    "posts": 0,
                    "categories": 0,
                    "tags": 0,
                    "special": 0
                },
                "content_stats": {
                    "total_posts": self.db.query(Content).filter(Content.status == ContentStatus.PUBLISHED).count(),
                    "total_categories": self.db.query(Category).count(),
                    "total_tags": self.db.query(Tag).count(),
                    "total_keywords": self.db.query(Keyword).count()
                }
            }
            
            if self.public_dir.exists():
                for file_path in self.public_dir.rglob("*"):
                    if file_path.is_file():
                        stats["total_files"] += 1
                        stats["total_size_mb"] += file_path.stat().st_size
                        
                        # Clasificar por tipo
                        if "/posts/" in str(file_path):
                            stats["pages_by_type"]["posts"] += 1
                        elif "/categories/" in str(file_path):
                            stats["pages_by_type"]["categories"] += 1
                        elif "/tags/" in str(file_path):
                            stats["pages_by_type"]["tags"] += 1
                        else:
                            stats["pages_by_type"]["special"] += 1
                
                # Convertir bytes a MB
                stats["total_size_mb"] = round(stats["total_size_mb"] / (1024 * 1024), 2)
                
                # Obtener fecha de última modificación
                index_file = self.public_dir / "index.html"
                if index_file.exists():
                    stats["last_generation"] = datetime.fromtimestamp(
                        index_file.stat().st_mtime
                    ).isoformat()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del sitio: {str(e)}")
            return {}
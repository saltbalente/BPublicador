from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func
from typing import Optional, List
import os
from datetime import datetime, timedelta
from collections import defaultdict

from app.core.database import get_db
from app.models.content import Content
from app.models.category import Category
from app.models.tag import Tag
from app.models.keyword import Keyword
from app.services.publication_engine import PublicationEngine
from app.core.config import settings
from app.api.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter()
# El motor de publicación se instanciará en cada endpoint con la sesión de DB

# Función helper para obtener el tema del sitio
def get_site_theme(db: Session) -> str:
    """Obtener el tema preferido del sitio basado en el último post publicado"""
    try:
        # Obtener el último post publicado para usar su tema
        latest_post = db.query(Content).filter(
            Content.status == "published",
            Content.template_theme.isnot(None)
        ).order_by(Content.created_at.desc()).first()
        
        if latest_post and latest_post.template_theme:
            return latest_post.template_theme
        return "default"
    except:
        return "default"

# Rutas públicas del sitio web

@router.get("/", response_class=HTMLResponse)
async def homepage(request: Request, db: Session = Depends(get_db)):
    """Página principal del sitio público"""
    try:
        publication_engine = PublicationEngine(db)
        
        # Obtener contenido para la homepage
        recent_posts = db.query(Content).filter(
            Content.status == "published"
        ).order_by(Content.created_at.desc()).limit(6).all()
        
        popular_posts = db.query(Content).filter(
            Content.status == "published"
        ).order_by(Content.word_count.desc()).limit(3).all()
        
        categories = db.query(Category).limit(8).all()
        
        # Estadísticas del sitio
        total_posts = db.query(Content).filter(Content.status == "published").count()
        total_categories = db.query(Category).count()
        total_tags = db.query(Tag).count()
        
        context = {
            "request": request,
            "recent_posts": recent_posts,
            "popular_posts": popular_posts,
            "categories": categories,
            "total_posts": total_posts,
            "total_categories": total_categories,
            "total_tags": total_tags,
            "site_title": "Autopublicador Web - Contenido IA",
            "site_description": "Plataforma de generación automática de contenido con IA",
            "template_theme": get_site_theme(db),  # Tema del sitio basado en último post
            "base_url": str(request.base_url).rstrip('/')
        }
        
        return publication_engine.render_template("homepage.html", context)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering homepage: {str(e)}")


@router.get("/posts/{slug}", response_class=HTMLResponse)
async def post_detail(slug: str, request: Request, db: Session = Depends(get_db)):
    """Página de detalle de un post"""
    try:
        publication_engine = PublicationEngine(db)
        
        # Buscar el post por slug
        post = db.query(Content).filter(
            Content.slug == slug,
            Content.status == "published"
        ).first()
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Posts relacionados (misma categoría)
        related_posts = []
        if post.category:
            related_posts = db.query(Content).filter(
                Content.category_id == post.category.id,
                Content.id != post.id,
                Content.status == "published"
            ).limit(3).all()
        
        # Posts populares para sidebar
        popular_posts = db.query(Content).filter(
            Content.status == "published"
        ).order_by(Content.word_count.desc()).limit(5).all()
        
        # Navegación anterior/siguiente
        prev_post = db.query(Content).filter(
            Content.created_at < post.created_at,
            Content.status == "published"
        ).order_by(Content.created_at.desc()).first()
        
        next_post = db.query(Content).filter(
            Content.created_at > post.created_at,
            Content.status == "published"
        ).order_by(Content.created_at.asc()).first()
        
        context = {
            "request": request,
            "post": post,
            "related_posts": related_posts,
            "popular_posts": popular_posts,
            "prev_post": prev_post,
            "next_post": next_post,
            "template_theme": post.template_theme if hasattr(post, 'template_theme') else 'default',
            "base_url": str(request.base_url).rstrip('/'),
            "canonical_url": f"{str(request.base_url).rstrip('/')}/posts/{slug}"
        }
        
        return publication_engine.render_template("post.html", context)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering post: {str(e)}")


@router.get("/categories/{slug}", response_class=HTMLResponse)
async def category_detail(slug: str, request: Request, db: Session = Depends(get_db), page: int = 1):
    """Página de categoría"""
    try:
        publication_engine = PublicationEngine(db)
        
        # Buscar la categoría por slug
        category = db.query(Category).filter(Category.slug == slug).first()
        
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        
        # Paginación
        per_page = 12
        offset = (page - 1) * per_page
        
        # Posts de la categoría
        posts_query = db.query(Content).filter(
            Content.category_id == category.id,
            Content.status == "published"
        )
        
        total_posts = posts_query.count()
        posts = posts_query.order_by(Content.created_at.desc()).offset(offset).limit(per_page).all()
        
        # Calcular paginación
        total_pages = (total_posts + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        # Categorías relacionadas
        related_categories = db.query(Category).filter(
            Category.id != category.id
        ).limit(6).all()
        
        context = {
            "request": request,
            "category": category,
            "posts": posts,
            "related_categories": related_categories,
            "current_page": page,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "prev_page": page - 1 if has_prev else None,
            "next_page": page + 1 if has_next else None,
            "total_posts": total_posts,
            "template_theme": get_site_theme(db),  # Tema del sitio basado en último post
            "base_url": str(request.base_url).rstrip('/'),
            "canonical_url": f"{str(request.base_url).rstrip('/')}/categories/{slug}"
        }
        
        return publication_engine.render_template("category.html", context)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering category: {str(e)}")


@router.get("/tags/{slug}", response_class=HTMLResponse)
async def tag_detail(slug: str, request: Request, db: Session = Depends(get_db), page: int = 1):
    """Página de tag"""
    try:
        publication_engine = PublicationEngine(db)
        
        # Buscar el tag por slug
        tag = db.query(Tag).filter(Tag.slug == slug).first()
        
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")
        
        # Paginación
        per_page = 12
        offset = (page - 1) * per_page
        
        # Posts del tag
        posts = db.query(Content).join(Content.tags).filter(
            Tag.id == tag.id,
            Content.status == "published"
        ).order_by(Content.created_at.desc()).offset(offset).limit(per_page).all()
        
        total_posts = db.query(Content).join(Content.tags).filter(
            Tag.id == tag.id,
            Content.status == "published"
        ).count()
        
        # Calcular paginación
        total_pages = (total_posts + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        # Tags relacionados
        related_tags = db.query(Tag).filter(
            Tag.id != tag.id
        ).limit(10).all()
        
        context = {
            "request": request,
            "tag": tag,
            "posts": posts,
            "related_tags": related_tags,
            "current_page": page,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "prev_page": page - 1 if has_prev else None,
            "next_page": page + 1 if has_next else None,
            "total_posts": total_posts,
            "template_theme": get_site_theme(db),  # Tema del sitio basado en último post
            "base_url": str(request.base_url).rstrip('/'),
            "canonical_url": f"{str(request.base_url).rstrip('/')}/tags/{slug}"
        }
        
        return publication_engine.render_template("tag.html", context)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering tag: {str(e)}")


# Rutas SEO

@router.get("/sitemap.xml", response_class=Response)
async def sitemap(request: Request, db: Session = Depends(get_db)):
    """Sitemap XML para SEO"""
    try:
        publication_engine = PublicationEngine(db)
        
        # Obtener todos los posts publicados
        posts = db.query(Content).filter(
            Content.status == "published"
        ).order_by(Content.updated_at.desc()).all()
        
        # Obtener categorías y tags
        categories = db.query(Category).all()
        tags = db.query(Tag).all()
        
        context = {
            "posts": posts,
            "categories": categories,
            "tags": tags,
            "base_url": str(request.base_url).rstrip('/'),
            "now": datetime.now
        }
        
        xml_content = publication_engine.render_template("sitemap.xml", context)
        
        return Response(
            content=xml_content,
            media_type="application/xml",
            headers={"Content-Type": "application/xml; charset=utf-8"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sitemap: {str(e)}")


@router.get("/rss.xml", response_class=Response)
async def rss_feed(request: Request, db: Session = Depends(get_db)):
    """RSS Feed para sindicación"""
    try:
        publication_engine = PublicationEngine(db)
        
        # Obtener los últimos 50 posts
        posts = db.query(Content).filter(
            Content.status == "published"
        ).order_by(Content.created_at.desc()).limit(50).all()
        
        context = {
            "posts": posts,
            "base_url": str(request.base_url).rstrip('/'),
            "site_title": "Autopublicador Web - Contenido IA",
            "site_description": "Plataforma de generación automática de contenido con IA",
            "now": datetime.now
        }
        
        xml_content = publication_engine.render_template("rss.xml", context)
        
        return Response(
            content=xml_content,
            media_type="application/rss+xml",
            headers={"Content-Type": "application/rss+xml; charset=utf-8"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating RSS feed: {str(e)}")


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt(request: Request, db: Session = Depends(get_db)):
    """Robots.txt para SEO"""
    try:
        publication_engine = PublicationEngine(db)
        
        context = {
            "base_url": str(request.base_url).rstrip('/'),
            "now": datetime.now
        }
        
        robots_content = publication_engine.render_template("robots.txt", context)
        
        return PlainTextResponse(
            content=robots_content,
            headers={"Content-Type": "text/plain; charset=utf-8"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating robots.txt: {str(e)}")


@router.get("/archivo", response_class=HTMLResponse)
async def archive_page(request: Request, db: Session = Depends(get_db), page: int = Query(1, ge=1)):
    """Página de archivo de posts"""
    try:
        publication_engine = PublicationEngine(db)
        
        # Paginación
        per_page = 20
        offset = (page - 1) * per_page
        
        # Obtener todos los posts publicados
        posts_query = db.query(Content).filter(Content.status == "published")
        total_posts = posts_query.count()
        all_posts = posts_query.order_by(Content.created_at.desc()).offset(offset).limit(per_page).all()
        
        # Organizar posts por año y mes
        posts_by_year = defaultdict(lambda: {"count": 0, "months": defaultdict(list)})
        
        for post in posts_query.order_by(Content.created_at.desc()).all():
            year = post.created_at.year
            month = post.created_at.strftime("%Y-%m")
            posts_by_year[year]["count"] += 1
            posts_by_year[year]["months"][month].append(post)
        
        # Estadísticas
        total_categories = db.query(Category).count()
        total_tags = db.query(Tag).count()
        months_count = len(set(post.created_at.strftime("%Y-%m") for post in posts_query.all()))
        
        # Paginación
        total_pages = (total_posts + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        context = {
            "request": request,
            "posts_by_year": dict(posts_by_year),
            "all_posts": all_posts,
            "total_posts": total_posts,
            "total_categories": total_categories,
            "total_tags": total_tags,
            "months_count": months_count,
            "current_page": page,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "prev_page": page - 1 if has_prev else None,
            "next_page": page + 1 if has_next else None,
            "template_theme": get_site_theme(db),  # Tema del sitio basado en último post
            "base_url": str(request.base_url).rstrip('/'),
            "canonical_url": f"{str(request.base_url).rstrip('/')}/archivo"
        }
        
        return publication_engine.render_template("archive.html", context)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering archive: {str(e)}")


@router.get("/buscar", response_class=HTMLResponse)
async def search_page(
    request: Request, 
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Término de búsqueda"),
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    date_from: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    sort: Optional[str] = Query("relevance", description="Ordenar por: relevance, date_desc, date_asc, title"),
    tags: Optional[str] = Query(None, description="Filtrar por tags (separados por comas)"),
    page: int = Query(1, ge=1)
):
    """Página de búsqueda"""
    try:
        publication_engine = PublicationEngine(db)
        
        results = []
        total_results = 0
        
        # Obtener categorías para el formulario
        categories = db.query(Category).all()
        
        if q and q.strip():
            # Construir query de búsqueda
            search_query = db.query(Content).filter(Content.status == "published")
            
            # Búsqueda por texto
            search_terms = q.strip().split()
            text_conditions = []
            
            for term in search_terms:
                term_condition = or_(
                    Content.title.ilike(f"%{term}%"),
                    Content.content.ilike(f"%{term}%"),
                    Content.meta_description.ilike(f"%{term}%")
                )
                text_conditions.append(term_condition)
            
            if text_conditions:
                search_query = search_query.filter(and_(*text_conditions))
            
            # Filtro por categoría
            if category:
                cat_obj = db.query(Category).filter(Category.slug == category).first()
                if cat_obj:
                    search_query = search_query.filter(Content.category_id == cat_obj.id)
            
            # Filtro por fechas
            if date_from:
                try:
                    from_date = datetime.strptime(date_from, "%Y-%m-%d")
                    search_query = search_query.filter(Content.created_at >= from_date)
                except ValueError:
                    pass
            
            if date_to:
                try:
                    to_date = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
                    search_query = search_query.filter(Content.created_at < to_date)
                except ValueError:
                    pass
            
            # Filtro por tags
            if tags:
                tag_names = [tag.strip() for tag in tags.split(',') if tag.strip()]
                if tag_names:
                    search_query = search_query.join(Content.tags).filter(
                        Tag.name.in_(tag_names)
                    )
            
            # Ordenamiento
            if sort == "date_desc":
                search_query = search_query.order_by(Content.created_at.desc())
            elif sort == "date_asc":
                search_query = search_query.order_by(Content.created_at.asc())
            elif sort == "title":
                search_query = search_query.order_by(Content.title.asc())
            else:  # relevance (por defecto)
                search_query = search_query.order_by(Content.created_at.desc())
            
            # Paginación
            per_page = 10
            offset = (page - 1) * per_page
            
            total_results = search_query.count()
            results = search_query.offset(offset).limit(per_page).all()
            
            # Calcular paginación
            total_pages = (total_results + per_page - 1) // per_page
            has_prev = page > 1
            has_next = page < total_pages
        else:
            total_pages = 0
            has_prev = False
            has_next = False
        
        # Búsquedas populares (simuladas)
        popular_searches = ["rituales", "hechizos", "tarot", "astrología", "meditación"]
        
        context = {
            "request": request,
            "query": q,
            "results": results,
            "total_results": total_results,
            "categories": categories,
            "selected_category": category,
            "date_from": date_from,
            "date_to": date_to,
            "sort_by": sort,
            "selected_tags": tags,
            "current_page": page,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "prev_page": page - 1 if has_prev else None,
            "next_page": page + 1 if has_next else None,
            "per_page": 10,
            "popular_searches": popular_searches,
            "template_theme": get_site_theme(db),  # Tema del sitio basado en último post
            "base_url": str(request.base_url).rstrip('/'),
            "canonical_url": f"{str(request.base_url).rstrip('/')}/buscar"
        }
        
        return publication_engine.render_template("search.html", context)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering search: {str(e)}")


@router.get("/404", response_class=HTMLResponse)
async def error_404_page(request: Request, db: Session = Depends(get_db)):
    """Página de error 404"""
    try:
        publication_engine = PublicationEngine(db)
        
        # Obtener contenido para la página 404
        popular_categories = db.query(Category).limit(5).all()
        recent_posts = db.query(Content).filter(
            Content.status == "published"
        ).order_by(Content.created_at.desc()).limit(5).all()
        
        popular_tags = db.query(Tag).limit(15).all()
        
        # Estadísticas
        total_posts = db.query(Content).filter(Content.status == "published").count()
        total_categories = db.query(Category).count()
        total_tags = db.query(Tag).count()
        total_images = 0  # Podrías calcular esto si tienes un modelo de imágenes
        
        context = {
            "request": request,
            "popular_categories": popular_categories,
            "recent_posts": recent_posts,
            "popular_tags": popular_tags,
            "total_posts": total_posts,
            "total_categories": total_categories,
            "total_tags": total_tags,
            "total_images": total_images,
            "template_theme": get_site_theme(db),  # Tema del sitio basado en último post
            "base_url": str(request.base_url).rstrip('/')
        }
        
        return publication_engine.render_template("404.html", context)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering 404 page: {str(e)}")


# Rutas administrativas para el motor de publicación

@router.post("/admin/generate-site")
async def generate_full_site(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generar sitio completo (solo para administradores)"""
    try:
        publication_engine = PublicationEngine(db)
        base_url = str(request.base_url).rstrip('/')
        result = publication_engine.generate_full_site()
        
        return {
            "message": "Sitio generado exitosamente",
            "stats": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating site: {str(e)}")


@router.post("/admin/regenerate-post/{post_id}")
async def regenerate_post(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Regenerar página de un post específico"""
    try:
        publication_engine = PublicationEngine(db)
        post = db.query(Content).filter(Content.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        publication_engine.regenerate_post(post)
        
        return {
            "message": f"Post '{post.title}' regenerado exitosamente",
            "post_url": f"{base_url}/posts/{post.slug}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerating post: {str(e)}")


@router.get("/admin/site-stats")
async def get_site_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener estadísticas del sitio"""
    try:
        publication_engine = PublicationEngine(db)
        stats = publication_engine.get_site_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting site stats: {str(e)}")


@router.get("/admin/publication-status")
async def get_publication_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Obtener estado del motor de publicación"""
    try:
        publication_engine = PublicationEngine(db)
        # Verificar directorios y configuración
        public_dir = publication_engine.public_dir
        templates_dir = publication_engine.templates_dir
        static_dir = publication_engine.static_dir
        
        status = {
            "engine_ready": True,
            "directories": {
                "public_dir_exists": os.path.exists(public_dir),
                "templates_dir_exists": os.path.exists(templates_dir),
                "static_dir_exists": os.path.exists(static_dir),
                "public_dir": str(public_dir),
                "templates_dir": str(templates_dir),
                "static_dir": str(static_dir)
            },
            "templates": {
                "base_html": os.path.exists(templates_dir / "base.html"),
                "homepage_html": os.path.exists(templates_dir / "homepage.html"),
                "post_html": os.path.exists(templates_dir / "post.html"),
                "category_html": os.path.exists(templates_dir / "category.html"),
                "tag_html": os.path.exists(templates_dir / "tag.html"),
                "sitemap_xml": os.path.exists(templates_dir / "sitemap.xml"),
                "rss_xml": os.path.exists(templates_dir / "rss.xml"),
                "robots_txt": os.path.exists(templates_dir / "robots.txt")
            }
        }
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking publication status: {str(e)}")
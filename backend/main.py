from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.v1.router import api_router
from app.api.v1 import auth, keywords, content, keyword_analysis, image_generation, scheduler, analytics, categories, tags, seo_schemas, publication
from app.core.config import settings
from app.core.database import get_db
from app.models.content import Content
# from app.middleware.security import SecurityMiddleware
from sqlalchemy.orm import Session
import time
from datetime import datetime
import os
import html
import logging

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configurar logger específico para actualizaciones de contenido
content_logger = logging.getLogger("content_update")
content_logger.setLevel(logging.DEBUG)

app = FastAPI(
    title="Autopublicador Web API",
    version="1.0.0",
    description="API para generación automática de contenido con IA"
)

# Exception handler para errores de validación de Pydantic
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger = logging.getLogger("validation_error")
    logger.error(f"Error de validación en {request.method} {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": f"Error de validación: {exc.errors()}"}
    )

@app.exception_handler(ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
    logger = logging.getLogger("validation_error")
    logger.error(f"Error de validación Pydantic en {request.method} {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": f"Error de validación Pydantic: {exc.errors()}"}
    )

# Middleware para capturar errores de validación
@app.middleware("http")
async def validation_error_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        import traceback
        logger = logging.getLogger("validation_error")
        logger.error(f"Error en request {request.method} {request.url}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Si es un error de validación de Pydantic
        if "ValidationError" in str(type(e)):
            logger.error(f"Pydantic ValidationError: {e}")
            return JSONResponse(
                status_code=422,
                content={"detail": f"Error de validación: {str(e)}"}
            )
        raise e

# Configurar middleware de seguridad (DEBE IR ANTES QUE CORS)
# app.add_middleware(
#     SecurityMiddleware,
#     max_requests_per_minute=60,
#     max_requests_per_hour=1000,
#     blocked_ips=[],  # Lista de IPs bloqueadas permanentemente
#     allowed_file_types=['jpg', 'jpeg', 'png', 'gif', 'webp', 'txt', 'csv', 'json'],
#     max_content_length=10 * 1024 * 1024,  # 10MB
# )

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar archivos estáticos para el frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
print(f"Frontend path: {frontend_path}")
print(f"Frontend exists: {os.path.exists(frontend_path)}")
if os.path.exists(frontend_path):
    app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend_static")
    print("Frontend static files mounted successfully")

# Configurar archivos estáticos para imágenes subidas
images_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")
os.makedirs(images_path, exist_ok=True)
app.mount("/images", StaticFiles(directory=images_path), name="images")

# Configurar archivos estáticos para el motor de publicación (backend/static)
backend_static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(backend_static_path):
    app.mount("/static", StaticFiles(directory=backend_static_path), name="backend_static")
    print(f"Backend static files mounted from: {backend_static_path}")
else:
    print(f"Backend static directory not found: {backend_static_path}")

# Configurar archivos estáticos para el motor de publicación (app/static)
app_static_path = os.path.join(os.path.dirname(__file__), "app", "static")
if os.path.exists(app_static_path):
    app.mount("/app-static", StaticFiles(directory=app_static_path), name="app_static")
    print(f"App static files mounted from: {app_static_path}")
else:
    print(f"App static directory not found: {app_static_path}")

# Configurar templates
templates_path = os.path.join(os.path.dirname(__file__), "app", "templates")
templates = Jinja2Templates(directory=templates_path)

# Definir filtros personalizados para Jinja2
def truncate_words(text, length=50):
    """Truncar texto por número de palabras"""
    if not text:
        return ""
    words = str(text).split()
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
        return "1"
    word_count = len(str(text).split())
    minutes = max(1, round(word_count / wpm))
    return str(minutes)

# Agregar función now() como global
def now():
    """Función para obtener la fecha actual"""
    return datetime.now()

# Registrar los filtros en el entorno Jinja2
templates.env.filters['truncate_words'] = truncate_words
templates.env.filters['format_date'] = format_date
templates.env.filters['reading_time'] = reading_time

# Registrar funciones globales
templates.env.globals['now'] = now

print(f"Templates configured from: {templates_path}")

# Incluir rutas de la API
app.include_router(api_router, prefix="/api/v1")

# Incluir rutas públicas del sitio web (con prefijo para evitar conflictos)
from app.api.v1.publication import router as publication_router
app.include_router(publication_router, prefix="/site", tags=["sitio-público"])

# Ruta para mostrar todas las categorías
@app.get("/categoria/", response_class=HTMLResponse)
async def categorias_list(request: Request, db: Session = Depends(get_db)):
    """Página que muestra todas las categorías con artículos recientes"""
    from app.models.category import Category
    from app.models.content import Content
    
    try:
        # Obtener todas las categorías
        categories = db.query(Category).all()
        
        # Para cada categoría, obtener 3 artículos recientes
        categories_with_posts = []
        for category in categories:
            recent_posts = db.query(Content).filter(
                Content.category_id == category.id,
                Content.status == "published"
            ).order_by(Content.created_at.desc()).limit(3).all()
            
            categories_with_posts.append({
                "category": category,
                "recent_posts": recent_posts,
                "total_posts": db.query(Content).filter(
                    Content.category_id == category.id,
                    Content.status == "published"
                ).count()
            })
        
        context = {
            "request": request,
            "categories_with_posts": categories_with_posts,
            "categories": categories,  # Agregar categories para base.html
            "base_url": str(request.base_url).rstrip('/'),
            "canonical_url": f"{str(request.base_url).rstrip('/')}/categoria/",
            "page_title": "Todas las Categorías",
            "page_description": "Explora todas nuestras categorías y descubre contenido interesante"
        }
        
        return templates.TemplateResponse("categories.html", context)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cargando categorías: {str(e)}")

# Ruta para categorías en español
@app.get("/categoria/{slug}", response_class=HTMLResponse)
async def categoria_detail(slug: str, request: Request, db: Session = Depends(get_db), page: int = 1):
    """Página de categoría en español"""
    from app.models.category import Category
    from app.models.content import Content
    
    try:
        # Buscar la categoría por slug
        category = db.query(Category).filter(Category.slug == slug).first()
        
        if not category:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        
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
        
        # Crear objeto de paginación compatible con la plantilla
        class Pagination:
            def __init__(self, page, total_pages, has_prev, has_next, total_posts):
                self.page = page
                self.pages = total_pages
                self.has_prev = has_prev
                self.has_next = has_next
                self.prev_num = page - 1 if has_prev else None
                self.next_num = page + 1 if has_next else None
                self.total = total_posts
            
            def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
                """Generar números de página para la paginación"""
                last = self.pages
                for num in range(1, last + 1):
                    if num <= left_edge or \
                       (self.page - left_current - 1 < num < self.page + right_current) or \
                       num > last - right_edge:
                        yield num
        
        pagination = Pagination(page, total_pages, has_prev, has_next, total_posts)
        
        context = {
            "request": request,
            "category": category,
            "posts": posts,
            "categories": related_categories,  # La plantilla espera 'categories'
            "current_page": page,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "prev_page": page - 1 if has_prev else None,
            "next_page": page + 1 if has_next else None,
            "total_posts": total_posts,
            "base_url": str(request.base_url).rstrip('/'),
            "canonical_url": f"{str(request.base_url).rstrip('/')}/categoria/{slug}",
            "pagination": pagination
        }
        
        return templates.TemplateResponse("category.html", context)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error renderizando categoría: {str(e)}")

@app.get("/dashboard")
def dashboard():
    """Servir el dashboard del frontend"""
    dashboard_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    return {"message": "Dashboard no encontrado"}

@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Autopublicador Web - Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                padding: 3rem;
                max-width: 800px;
                width: 90%;
                text-align: center;
            }
            
            .logo {
                font-size: 3rem;
                margin-bottom: 1rem;
            }
            
            h1 {
                color: #333;
                font-size: 2.5rem;
                margin-bottom: 1rem;
                font-weight: 700;
            }
            
            .subtitle {
                color: #666;
                font-size: 1.2rem;
                margin-bottom: 2rem;
                line-height: 1.6;
            }
            
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1.5rem;
                margin: 2rem 0;
            }
            
            .feature {
                background: #f8f9fa;
                padding: 1.5rem;
                border-radius: 15px;
                border: 2px solid transparent;
                transition: all 0.3s ease;
            }
            
            .feature:hover {
                border-color: #667eea;
                transform: translateY(-5px);
            }
            
            .feature-icon {
                font-size: 2rem;
                margin-bottom: 0.5rem;
            }
            
            .feature h3 {
                color: #333;
                margin-bottom: 0.5rem;
                font-size: 1.1rem;
            }
            
            .feature p {
                color: #666;
                font-size: 0.9rem;
            }
            
            .actions {
                display: flex;
                gap: 1rem;
                justify-content: center;
                flex-wrap: wrap;
                margin-top: 2rem;
            }
            
            .btn {
                padding: 12px 24px;
                border: none;
                border-radius: 10px;
                font-size: 1rem;
                font-weight: 600;
                text-decoration: none;
                transition: all 0.3s ease;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            .btn-secondary {
                background: white;
                color: #667eea;
                border: 2px solid #667eea;
            }
            
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            }
            
            .status {
                background: #d4edda;
                color: #155724;
                padding: 1rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                border: 1px solid #c3e6cb;
            }
            
            .version {
                color: #999;
                font-size: 0.9rem;
                margin-top: 2rem;
            }
            
            @media (max-width: 768px) {
                .container {
                    padding: 2rem;
                }
                
                h1 {
                    font-size: 2rem;
                }
                
                .actions {
                    flex-direction: column;
                    align-items: center;
                }
                
                .btn {
                    width: 100%;
                    max-width: 300px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🚀</div>
            <h1>Autopublicador Web</h1>
            <p class="subtitle">
                Plataforma inteligente para la generación automática de contenido SEO optimizado.
                Crea, gestiona y publica contenido de alta calidad de forma automatizada.
            </p>
            
            <div class="status">
                ✅ <strong>Sistema Activo</strong> - API funcionando correctamente
            </div>
            
            <div class="features">
                <div class="feature">
                    <div class="feature-icon">📝</div>
                    <h3>Generación de Contenido</h3>
                    <p>IA avanzada para crear artículos únicos y optimizados para SEO</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">🔍</div>
                    <h3>Investigación de Keywords</h3>
                    <p>Análisis automático de palabras clave y tendencias del mercado</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">📊</div>
                    <h3>Analytics Integrado</h3>
                    <p>Seguimiento del rendimiento y métricas de contenido en tiempo real</p>
                </div>
                <div class="feature">
                    <div class="feature-icon">⚡</div>
                    <h3>Publicación Automática</h3>
                    <p>Programación y distribución automática en múltiples plataformas</p>
                </div>
            </div>
            
            <div class="actions">
                <a href="/dashboard" class="btn btn-primary">
                    🎛️ Dashboard Visual
                </a>
                <a href="/docs" class="btn btn-secondary">
                    📚 Documentación API
                </a>
                <a href="/redoc" class="btn btn-secondary">
                    📖 Documentación ReDoc
                </a>
            </div>
            
            <div class="version">
                Versión 1.0.0 | Autopublicador API
            </div>
        </div>
        
        <script>
            // Agregar animación suave al cargar
            document.addEventListener('DOMContentLoaded', function() {
                const container = document.querySelector('.container');
                container.style.opacity = '0';
                container.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    container.style.transition = 'all 0.6s ease';
                    container.style.opacity = '1';
                    container.style.transform = 'translateY(0)';
                }, 100);
            });
        </script>
    </body>
    </html>
    """
    return html_content

def extract_first_image_from_content(content_html: str) -> str:
    """Extrae la primera imagen del contenido HTML"""
    import re
    
    # Buscar la primera etiqueta img en el contenido
    img_pattern = r'<img[^>]+src=["\']([^"\'>]+)["\'][^>]*>'
    match = re.search(img_pattern, content_html, re.IGNORECASE)
    
    if match:
        return match.group(1)
    return None

@app.get("/inicio/", response_class=HTMLResponse)
async def home_page(request: Request, db: Session = Depends(get_db)):
    """Página de inicio esotérica con artículos recientes"""
    from app.models.category import Category
    from app.api.v1.visual_config import load_config
    
    # Cargar configuración visual
    visual_config = load_config()
    
    # Obtener artículos según la configuración
    recent_articles = db.query(Content).filter(
        Content.status == "published"
    ).order_by(Content.created_at.desc()).limit(visual_config.articlesCount).all()
    
    # Procesar artículos para agregar imagen de respaldo
    for article in recent_articles:
        if not article.featured_image_url:
            # Si no tiene imagen destacada, extraer la primera del contenido
            first_image = extract_first_image_from_content(article.content or "")
            if first_image:
                article.featured_image = first_image
            else:
                article.featured_image = None
        else:
            article.featured_image = article.featured_image_url
    
    # Obtener categorías para el menú de navegación
    categories = db.query(Category).limit(10).all()
    
    return templates.TemplateResponse("home.html", {
        "request": request,
        "articles": recent_articles,
        "categories": categories,
        "base_url": "",
        "current_page": "home",
        "page_title": "Inicio - Autopublicador Web",
        "meta_description": "Descubre contenido esotérico y espiritual. Explora artículos sobre tarot, astrología, meditación y crecimiento personal.",
        "visual_config": visual_config
    })


@app.get("/", response_class=HTMLResponse)
async def landing_page():
    """Página de aterrizaje principal"""
    return RedirectResponse(url="/inicio/", status_code=302)

@app.get("/content/{slug}", response_class=HTMLResponse, response_model=None)
async def get_public_content(slug: str, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Servir contenido público por slug usando el sistema de templates"""
    from app.models.category import Category
    from app.models.tag import Tag
    
    # Buscar contenido por slug que esté publicado
    content_item = db.query(Content).filter(
        Content.slug == slug,
        Content.status == "published"
    ).first()
    
    if not content_item:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    
    # Obtener datos necesarios para el template
    categories = db.query(Category).limit(10).all()
    category = content_item.category
    tags = content_item.tags
    keyword = content_item.keyword
    images = content_item.images
    
    # Obtener el tema del post o usar el tema del sitio
    template_theme = content_item.template_theme or "default"
    
    # Preparar el contexto para el template
    context = {
        "request": request,
        "post": content_item,
        "category": category,
        "categories": categories,
        "tags": tags,
        "keyword": keyword,
        "images": images,
        "template_theme": template_theme,
        "site_name": "Autopublicador Web",
        "base_url": "",
        "current_url": str(request.url),
        "current_page": "post"
    }
    
    # Usar el template de post del sistema existente
    return templates.TemplateResponse("post.html", context)

@app.get("/health")
async def health_check():
    """Endpoint de health check para Docker y monitoreo"""
    try:
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "service": "autopublicador-api"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Endpoints de health check - DEBEN estar al principio para evitar dependencias
@app.get("/ping")
def ping():
    """Endpoint ultra-simple de ping - no depende de nada"""
    return {"status": "ok"}

@app.get("/ready")
def ready():
    """Endpoint para verificar que la app está lista"""
    import time
    return {
        "status": "ready", 
        "service": "autopublicador-api",
        "timestamp": int(time.time())
    }

@app.get("/healthz")
def healthz():
    """Endpoint de health check compatible con Kubernetes/Railway"""
    return {"status": "healthy"}
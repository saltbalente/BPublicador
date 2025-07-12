from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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

app = FastAPI(
    title="Autopublicador Web API",
    version="1.0.0",
    description="API para generación automática de contenido con IA"
)

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
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    print("Static files mounted successfully")

# Configurar archivos estáticos para imágenes subidas
images_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")
os.makedirs(images_path, exist_ok=True)
app.mount("/images", StaticFiles(directory=images_path), name="images")

# Configurar archivos estáticos para el motor de publicación
static_path = os.path.join(os.path.dirname(__file__), "app", "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="publication_static")
    print(f"Publication static files mounted from: {static_path}")
else:
    print(f"Publication static directory not found: {static_path}")

# Incluir rutas de la API
app.include_router(api_router, prefix="/api/v1")

# Incluir rutas públicas del sitio web (con prefijo para evitar conflictos)
from app.api.v1.publication import router as publication_router
app.include_router(publication_router, prefix="/site", tags=["sitio-público"])

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

@app.get("/inicio/", response_class=HTMLResponse)
async def home_page():
    """Página de inicio/home de la web"""
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bienvenido - Mi Blog</title>
        <meta name="description" content="Bienvenido a nuestro blog. Descubre contenido interesante y de calidad.">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            
            .header {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                padding: 1rem 0;
                box-shadow: 0 2px 20px rgba(0,0,0,0.1);
            }
            
            .nav {
                max-width: 1200px;
                margin: 0 auto;
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0 2rem;
            }
            
            .logo {
                font-size: 1.8rem;
                font-weight: 700;
                color: #2c3e50;
                text-decoration: none;
            }
            
            .nav-links {
                display: flex;
                list-style: none;
                gap: 2rem;
            }
            
            .nav-links a {
                color: #2c3e50;
                text-decoration: none;
                font-weight: 500;
                transition: color 0.3s ease;
            }
            
            .nav-links a:hover {
                color: #3498db;
            }
            
            .hero {
                text-align: center;
                padding: 6rem 2rem;
                color: white;
            }
            
            .hero h1 {
                font-size: 3.5rem;
                margin-bottom: 1rem;
                font-weight: 700;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            
            .hero p {
                font-size: 1.3rem;
                margin-bottom: 2rem;
                opacity: 0.9;
                max-width: 600px;
                margin-left: auto;
                margin-right: auto;
            }
            
            .cta-button {
                display: inline-block;
                background: #3498db;
                color: white;
                padding: 1rem 2rem;
                border-radius: 50px;
                text-decoration: none;
                font-weight: 600;
                font-size: 1.1rem;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(52, 152, 219, 0.4);
            }
            
            .cta-button:hover {
                background: #2980b9;
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(52, 152, 219, 0.6);
            }
            
            .features {
                background: white;
                padding: 5rem 2rem;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .features h2 {
                text-align: center;
                font-size: 2.5rem;
                margin-bottom: 3rem;
                color: #2c3e50;
            }
            
            .features-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 2rem;
                margin-top: 3rem;
            }
            
            .feature-card {
                background: #f8f9fa;
                padding: 2rem;
                border-radius: 15px;
                text-align: center;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            
            .feature-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }
            
            .feature-icon {
                font-size: 3rem;
                margin-bottom: 1rem;
            }
            
            .feature-card h3 {
                font-size: 1.5rem;
                margin-bottom: 1rem;
                color: #2c3e50;
            }
            
            .feature-card p {
                color: #666;
                line-height: 1.6;
            }
            
            .footer {
                background: #2c3e50;
                color: white;
                text-align: center;
                padding: 2rem;
            }
            
            .admin-link {
                position: fixed;
                bottom: 2rem;
                right: 2rem;
                background: #e74c3c;
                color: white;
                padding: 1rem;
                border-radius: 50px;
                text-decoration: none;
                font-weight: 600;
                box-shadow: 0 4px 15px rgba(231, 76, 60, 0.4);
                transition: all 0.3s ease;
            }
            
            .admin-link:hover {
                background: #c0392b;
                transform: translateY(-2px);
            }
            
            @media (max-width: 768px) {
                .hero h1 {
                    font-size: 2.5rem;
                }
                
                .hero p {
                    font-size: 1.1rem;
                }
                
                .nav {
                    flex-direction: column;
                    gap: 1rem;
                }
                
                .nav-links {
                    gap: 1rem;
                }
                
                .features-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <header class="header">
            <nav class="nav">
                <a href="/inicio/" class="logo">Mi Blog</a>
                <ul class="nav-links">
                    <li><a href="/inicio/">Inicio</a></li>
                    <li><a href="#sobre-nosotros">Sobre Nosotros</a></li>
                    <li><a href="#contacto">Contacto</a></li>
                </ul>
            </nav>
        </header>
        
        <section class="hero">
            <div class="container">
                <h1>Bienvenido a Mi Blog</h1>
                <p>Descubre contenido de calidad, artículos interesantes y las últimas tendencias en nuestro blog. Un espacio donde compartimos conocimiento y experiencias.</p>
                <a href="#contenido" class="cta-button">Explorar Contenido</a>
            </div>
        </section>
        
        <section class="features" id="contenido">
            <div class="container">
                <h2>¿Qué Encontrarás Aquí?</h2>
                <div class="features-grid">
                    <div class="feature-card">
                        <div class="feature-icon">📝</div>
                        <h3>Artículos de Calidad</h3>
                        <p>Contenido original y bien investigado sobre diversos temas de interés, escrito por expertos en cada área.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🎯</div>
                        <h3>Contenido Especializado</h3>
                        <p>Artículos enfocados en temas específicos con análisis profundo y perspectivas únicas.</p>
                    </div>
                    <div class="feature-card">
                        <div class="feature-icon">🚀</div>
                        <h3>Actualizaciones Regulares</h3>
                        <p>Nuevo contenido publicado regularmente para mantenerte informado sobre las últimas tendencias.</p>
                    </div>
                </div>
            </div>
        </section>
        
        <footer class="footer">
            <div class="container">
                <p>&copy; 2024 Mi Blog. Todos los derechos reservados.</p>
            </div>
        </footer>
        
        <a href="/dashboard" class="admin-link">🔧 Admin</a>
    </body>
    </html>
    """
    
    return html_content

@app.get("/content/{slug}", response_class=HTMLResponse, response_model=None)
async def get_public_content(slug: str, db: Session = Depends(get_db)) -> HTMLResponse:
    """Servir contenido público por slug"""
    # Buscar contenido por slug que esté publicado
    content_item = db.query(Content).filter(
        Content.slug == slug,
        Content.status == "published"
    ).first()
    
    if not content_item:
        raise HTTPException(status_code=404, detail="Contenido no encontrado")
    
    # Formatear fecha para Schema.org
    published_date = content_item.published_at or content_item.created_at
    iso_date = published_date.strftime('%Y-%m-%d')
    formatted_date = published_date.strftime('%d de %B de %Y')
    
    # Información del autor y publisher
    author_name = content_item.user.username if content_item.user else "Autor"
    publisher_name = "Consultas Esotéricas Latam"  # Configurable
    
    # Generar HTML para mostrar el contenido con Schema.org
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{content_item.meta_title or content_item.title}</title>
        <meta name="description" content="{content_item.meta_description or content_item.excerpt or ''}">
        <meta name="keywords" content="{content_item.keyword.keyword if content_item.keyword else ''}">
        
        <!-- Open Graph / Facebook -->
        <meta property="og:type" content="article">
        <meta property="og:url" content="{request.url if 'request' in locals() else ''}">
        <meta property="og:title" content="{content_item.meta_title or content_item.title}">
        <meta property="og:description" content="{content_item.meta_description or content_item.excerpt or ''}">
        
        <!-- Twitter -->
        <meta property="twitter:card" content="summary_large_image">
        <meta property="twitter:title" content="{content_item.meta_title or content_item.title}">
        <meta property="twitter:description" content="{content_item.meta_description or content_item.excerpt or ''}">
        
        <!-- Schema.org JSON-LD -->
        <script type="application/ld+json">
        {{
            "@context": "https://schema.org",
            "@type": "{content_item.schema_type or 'Article'}",
            "headline": "{content_item.title}",
            "description": "{content_item.meta_description or content_item.excerpt or ''}",
            "author": {{
                "@type": "Person",
                "name": "{content_item.author_name or author_name}"
            }},
            "publisher": {{
                "@type": "Organization",
                "name": "{content_item.publisher_name or publisher_name}"
            }},
            "datePublished": "{iso_date}",
            "dateModified": "{content_item.updated_at.strftime('%Y-%m-%d') if content_item.updated_at else iso_date}",
            "mainEntityOfPage": {{
                "@type": "WebPage",
                "@id": "{request.url if 'request' in locals() else ''}"
            }},
            "articleSection": "{content_item.article_section or (content_item.category.name if content_item.category else 'General')}",
            "keywords": "{content_item.keyword.keyword if content_item.keyword else ''}",
            "wordCount": {content_item.word_count or 0}
        }}
        </script>
        
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Georgia', 'Times New Roman', serif;
                line-height: 1.6;
                color: #333;
                background-color: #f8f9fa;
                padding: 2rem 0;
            }}
            
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 3rem;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }}
            
            article {{
                background: white;
                border-radius: 8px;
                overflow: hidden;
            }}
            
            header {{
                text-align: center;
                margin-bottom: 3rem;
                border-bottom: 2px solid #eee;
                padding-bottom: 2rem;
            }}
            
            footer {{
                margin-top: 3rem;
                padding-top: 2rem;
                border-top: 1px solid #eee;
                text-align: center;
                color: #666;
                font-size: 0.9rem;
            }}
            
            footer strong {{
                color: #2c3e50;
                font-weight: 600;
            }}
            
            h1 {{
                font-size: 2.5rem;
                color: #2c3e50;
                margin-bottom: 1rem;
                font-weight: 700;
            }}
            
            .meta {{
                color: #666;
                font-size: 0.9rem;
                margin-bottom: 1rem;
            }}
            
            .excerpt {{
                font-size: 1.2rem;
                color: #555;
                font-style: italic;
                margin-bottom: 2rem;
            }}
            
            .content {{
                 font-size: 1.1rem;
                 line-height: 1.8;
                 text-align: justify;
             }}
             
             .content p {{
                 margin-bottom: 1.5rem;
             }}
             
             .content h2 {{
                 font-size: 1.8rem;
                 color: #2c3e50;
                 margin-top: 2.5rem;
                 margin-bottom: 1.5rem;
                 font-weight: 600;
                 border-bottom: 2px solid #ecf0f1;
                 padding-bottom: 0.5rem;
             }}
             
             .content h2:first-child {{
                 margin-top: 0;
             }}
             
             .content h3 {{
                 font-size: 1.4rem;
                 color: #34495e;
                 margin-top: 2rem;
                 margin-bottom: 1rem;
                 font-weight: 600;
             }}
             
             .content strong {{
                 font-weight: 700;
                 color: #2c3e50;
             }}
             
             .content em {{
                 font-style: italic;
                 color: #555;
             }}
             
             .content blockquote {{
                 border-left: 4px solid #3498db;
                 padding-left: 1.5rem;
                 margin: 2rem 0;
                 font-style: italic;
                 color: #555;
                 background: #f8f9fa;
                 padding: 1.5rem;
                 border-radius: 0 8px 8px 0;
             }}
             
             .content ul, .content ol {{
                 margin: 1.5rem 0;
                 padding-left: 2rem;
             }}
             
             .content li {{
                 margin-bottom: 0.5rem;
                 line-height: 1.6;
             }}
             
             .content ul li {{
                 list-style-type: disc;
             }}
             
             .content ol li {{
                 list-style-type: decimal;
             }}
            
            .category {{
                display: inline-block;
                background: #3498db;
                color: white;
                padding: 0.3rem 0.8rem;
                border-radius: 15px;
                font-size: 0.8rem;
                margin-bottom: 1rem;
            }}
            
            .tags {{
                margin-top: 2rem;
                padding-top: 2rem;
                border-top: 1px solid #eee;
            }}
            
            .tag {{
                display: inline-block;
                background: #ecf0f1;
                color: #2c3e50;
                padding: 0.3rem 0.6rem;
                border-radius: 10px;
                font-size: 0.8rem;
                margin-right: 0.5rem;
                margin-bottom: 0.5rem;
            }}
            
            .back-link {{
                display: inline-block;
                margin-top: 2rem;
                color: #3498db;
                text-decoration: none;
                font-weight: 600;
            }}
            
            .back-link:hover {{
                text-decoration: underline;
            }}
            
            @media (max-width: 768px) {{
                .container {{
                    margin: 0 1rem;
                    padding: 2rem;
                }}
                
                h1 {{
                    font-size: 2rem;
                }}
                
                .content {{
                    font-size: 1rem;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <article itemscope itemtype="https://schema.org/{content_item.schema_type or 'Article'}">
                <header>
                    {f'<div class="category">{content_item.category.name}</div>' if content_item.category else ''}
                    <h1 itemprop="headline">{content_item.title}</h1>
                    <p class="meta">
                        <time datetime="{iso_date}" itemprop="datePublished">{formatted_date}</time>
                        • Por <span itemprop="author" itemscope itemtype="https://schema.org/Person">
                            <span itemprop="name">{content_item.author_name or author_name}</span>
                        </span>
                        {f' | Palabra clave: {content_item.keyword.keyword}' if content_item.keyword else ''}
                    </p>
                    {f'<div class="excerpt" itemprop="description">{content_item.excerpt}</div>' if content_item.excerpt else ''}
                </header>
                
                <section itemprop="articleBody" class="content">
                     {html.unescape(content_item.content) if content_item.content else ''}
                 </section>
                
                {f'''
                <div class="tags">
                    <strong>Etiquetas:</strong>
                    {' '.join([f'<span class="tag" itemprop="keywords">{tag.name}</span>' for tag in content_item.tags])}
                </div>
                ''' if content_item.tags else ''}
                
                <footer>
                    <p itemprop="publisher" itemscope itemtype="https://schema.org/Organization">
                        Publicado por <strong itemprop="name">{content_item.publisher_name or publisher_name}</strong>
                    </p>
                </footer>
            </article>
            
            <a href="/inicio/" class="back-link">← Volver al inicio</a>
        </div>
    </body>
    </html>
    """
    
    return html_content

@app.get("/health")
async def health_check():
    """Endpoint de health check para Docker y monitoreo"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "uptime": time.time()
        }
    )
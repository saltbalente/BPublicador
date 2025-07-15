"""FastAPI application factory with cloud-native architecture."""

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from config import config
from api.core.database import init_db
from api.routes import posts_router, generation_router, admin_router
from api.middleware.error_handler import ErrorHandlerMiddleware
from api.middleware.logging import LoggingMiddleware


# Configure logging
logging.basicConfig(
    level=logging.INFO if config.is_production else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {config.app_name} v{config.app_version}")
    logger.info(f"Platform: {config.platform}")
    logger.info(f"Environment: {config.environment}")
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        if config.is_production:
            raise
    
    # Ensure storage directories
    config.ensure_directories()
    logger.info("Storage directories verified")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=config.app_name,
        version=config.app_version,
        description="Cloud-native content publishing platform",
        docs_url="/docs" if not config.is_production else None,
        redoc_url="/redoc" if not config.is_production else None,
        lifespan=lifespan
    )
    
    # Security middleware
    if config.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure properly in production
        )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    # Include API routes
    app.include_router(posts_router, prefix=config.api_prefix)
    app.include_router(generation_router, prefix=config.api_prefix)
    app.include_router(admin_router, prefix=config.api_prefix)
    
    # Static files with error handling
    try:
        # Web assets
        web_dir = Path(__file__).parent.parent.parent / "web"
        if web_dir.exists():
            app.mount("/static", StaticFiles(directory=web_dir / "assets"), name="static")
        
        # Storage files (with permission handling)
        if config.storage_dir.exists():
            app.mount("/storage", StaticFiles(directory=config.storage_dir), name="storage")
        
        # Templates
        templates_dir = web_dir / "templates"
        if templates_dir.exists():
            templates = Jinja2Templates(directory=templates_dir)
        else:
            templates = None
            
    except Exception as e:
        logger.warning(f"Static files setup failed: {e}")
        templates = None
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint for load balancers."""
        return {
            "status": "healthy",
            "app": config.app_name,
            "version": config.app_version,
            "platform": config.platform,
            "environment": config.environment
        }
    
    # Root endpoint
    @app.get("/")
    async def root(request: Request):
        """Root endpoint - serve main page or API info."""
        if templates:
            try:
                return templates.TemplateResponse(
                    "index.html", 
                    {"request": request, "config": config}
                )
            except Exception as e:
                logger.warning(f"Template rendering failed: {e}")
        
        # Fallback to JSON response
        return {
            "app": config.app_name,
            "version": config.app_version,
            "docs": "/docs" if not config.is_production else "Documentation disabled in production",
            "health": "/health",
            "api": config.api_prefix
        }
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler for unhandled errors."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        if config.is_production:
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error": str(exc),
                    "type": type(exc).__name__
                }
            )
    
    # 404 handler
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: HTTPException):
        """Custom 404 handler."""
        return JSONResponse(
            status_code=404,
            content={
                "detail": "Resource not found",
                "path": str(request.url.path)
            }
        )
    
    logger.info("FastAPI application created successfully")
    return app


# Create app instance
app = create_app()
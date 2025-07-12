import structlog
import logging
from typing import Any, Dict
from app.core.config import settings

def configure_logging():
    """Configurar logging estructurado"""
    
    # Configurar nivel de logging
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configurar structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configurar logging estándar
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
    )

def get_logger(name: str = None) -> structlog.BoundLogger:
    """Obtener logger estructurado"""
    return structlog.get_logger(name)

def log_api_request(method: str, path: str, user_id: int = None, **kwargs):
    """Log de peticiones API"""
    logger = get_logger("api")
    logger.info(
        "API Request",
        method=method,
        path=path,
        user_id=user_id,
        **kwargs
    )

def log_content_generation(content_id: int, keyword: str, provider: str, status: str, **kwargs):
    """Log de generación de contenido"""
    logger = get_logger("content_generation")
    logger.info(
        "Content Generation",
        content_id=content_id,
        keyword=keyword,
        provider=provider,
        status=status,
        **kwargs
    )

def log_error(error: Exception, context: Dict[str, Any] = None):
    """Log de errores con contexto"""
    logger = get_logger("error")
    logger.error(
        "Error occurred",
        error=str(error),
        error_type=type(error).__name__,
        context=context or {},
        exc_info=True
    )
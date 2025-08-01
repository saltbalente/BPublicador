"""
Configuración específica para producción en Vercel
"""
import os
from typing import Optional

class ProductionConfig:
    """Configuración optimizada para Vercel"""
    
    # Configuración de base de datos
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./autopublicador.db")
    
    # Configuración de seguridad
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Configuración de IA
    AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Modelos de IA
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
    
    # Configuración de contenido
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "2000"))
    DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "es")
    DEFAULT_STYLE = os.getenv("DEFAULT_STYLE", "profesional")
    
    # Configuración de imágenes
    IMAGE_GENERATION_ENABLED = os.getenv("IMAGE_GENERATION_ENABLED", "true").lower() == "true"
    IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "openai")
    DALLE_MODEL = os.getenv("DALLE_MODEL", "dall-e-3")
    IMAGE_SIZE = os.getenv("IMAGE_SIZE", "1024x1024")
    
    # Rate limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    REQUESTS_PER_MINUTE = int(os.getenv("REQUESTS_PER_MINUTE", "60"))
    
    # Configuración de entorno
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    @classmethod
    def get_ai_api_key(cls) -> Optional[str]:
        """Obtiene la API key según el proveedor configurado"""
        if cls.AI_PROVIDER == "openai":
            return cls.OPENAI_API_KEY
        elif cls.AI_PROVIDER == "deepseek":
            return cls.DEEPSEEK_API_KEY
        elif cls.AI_PROVIDER == "gemini":
            return cls.GEMINI_API_KEY
        return None
    
    @classmethod
    def validate_config(cls) -> bool:
        """Valida que la configuración esencial esté presente"""
        errors = []
        
        # Verificar SECRET_KEY
        if not cls.SECRET_KEY or cls.SECRET_KEY == "change-this-in-production":
            errors.append("SECRET_KEY no configurada o usando valor por defecto")
        
        # Verificar al menos una API key de IA
        if not any([cls.OPENAI_API_KEY, cls.DEEPSEEK_API_KEY, cls.GEMINI_API_KEY]):
            errors.append("No hay ninguna API key de IA configurada")
        
        # Verificar que el proveedor seleccionado tenga API key
        if not cls.get_ai_api_key():
            errors.append(f"API key no configurada para el proveedor seleccionado: {cls.AI_PROVIDER}")
        
        if errors:
            print("❌ Errores de configuración:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        print("✅ Configuración validada correctamente")
        return True
    
    @classmethod
    def print_config_summary(cls):
        """Imprime un resumen de la configuración actual"""
        print("📋 Resumen de configuración:")
        print(f"   - Entorno: {cls.ENVIRONMENT}")
        print(f"   - Debug: {cls.DEBUG}")
        print(f"   - Proveedor de IA: {cls.AI_PROVIDER}")
        print(f"   - Base de datos: {cls.DATABASE_URL}")
        print(f"   - Generación de imágenes: {'Habilitada' if cls.IMAGE_GENERATION_ENABLED else 'Deshabilitada'}")
        print(f"   - Rate limiting: {'Habilitado' if cls.RATE_LIMIT_ENABLED else 'Deshabilitado'}")
        
        # Mostrar APIs configuradas (sin mostrar las keys completas)
        apis_configured = []
        if cls.OPENAI_API_KEY:
            apis_configured.append("OpenAI")
        if cls.DEEPSEEK_API_KEY:
            apis_configured.append("DeepSeek")
        if cls.GEMINI_API_KEY:
            apis_configured.append("Gemini")
        
        print(f"   - APIs configuradas: {', '.join(apis_configured) if apis_configured else 'Ninguna'}")

# Instancia global de configuración
config = ProductionConfig()

# Validar configuración al importar
if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
    print("🔧 Validando configuración para Vercel...")
    config.validate_config()
    config.print_config_summary()
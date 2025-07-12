import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./autopublicador.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tu-clave-secreta-muy-segura-aqui-cambiar-en-produccion")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Rate Limiting
    REQUESTS_PER_MINUTE: int = int(os.getenv("REQUESTS_PER_MINUTE", "60"))
    
    # Content Generation
    DEFAULT_CONTENT_PROVIDER: str = os.getenv("DEFAULT_CONTENT_PROVIDER", "deepseek")
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "10000"))
    MIN_CONTENT_LENGTH: int = int(os.getenv("MIN_CONTENT_LENGTH", "100"))
    DEFAULT_WORD_COUNT: int = int(os.getenv("DEFAULT_WORD_COUNT", "800"))
    CONTENT_LANGUAGE: str = os.getenv("CONTENT_LANGUAGE", "es")
    WRITING_STYLE: str = os.getenv("WRITING_STYLE", "profesional")
    KEYWORD_DENSITY_TARGET: float = float(os.getenv("KEYWORD_DENSITY_TARGET", "2.5"))
    
    # AI Configuration
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    
    # Image Generation
    ENABLE_IMAGE_GENERATION: bool = os.getenv("ENABLE_IMAGE_GENERATION", "true").lower() == "true"
    
    # OpenAI DALL-E Configuration
    DALLE_MODEL: str = os.getenv("DALLE_MODEL", "dall-e-3")
    
    # Google Gemini Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    GEMINI_IMAGE_MODEL: str = os.getenv("GEMINI_IMAGE_MODEL", "imagen-3.0-generate-001")
    
    # Image Generation Settings
    DEFAULT_IMAGE_PROVIDER: str = os.getenv("DEFAULT_IMAGE_PROVIDER", "gemini")  # gemini, openai
    DEFAULT_IMAGE_SIZE: str = os.getenv("DEFAULT_IMAGE_SIZE", "1024x1024")
    DEFAULT_IMAGE_QUALITY: str = os.getenv("DEFAULT_IMAGE_QUALITY", "standard")
    DEFAULT_IMAGE_STYLE: str = os.getenv("DEFAULT_IMAGE_STYLE", "natural")
    MAX_IMAGES_PER_CONTENT: int = int(os.getenv("MAX_IMAGES_PER_CONTENT", "5"))
    IMAGES_STORAGE_PATH: str = os.getenv("IMAGES_STORAGE_PATH", "./storage/images")
    
    # Gemini Specific Settings
    GEMINI_SAFETY_SETTINGS: str = os.getenv("GEMINI_SAFETY_SETTINGS", "medium")
    GEMINI_ASPECT_RATIO: str = os.getenv("GEMINI_ASPECT_RATIO", "1:1")
    GEMINI_PERSON_GENERATION: str = os.getenv("GEMINI_PERSON_GENERATION", "allow_adult")
    
    # Scheduler
    ENABLE_SCHEDULER: bool = os.getenv("ENABLE_SCHEDULER", "false").lower() == "true"
    DEFAULT_SCHEDULE_INTERVAL: int = int(os.getenv("DEFAULT_SCHEDULE_INTERVAL", "60"))  # minutes
    MAX_DAILY_POSTS: int = int(os.getenv("MAX_DAILY_POSTS", "10"))
    SCHEDULER_TIMEZONE: str = os.getenv("SCHEDULER_TIMEZONE", "UTC")
    
    # Analytics
    ENABLE_ANALYTICS: bool = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
    ANALYTICS_RETENTION_DAYS: int = int(os.getenv("ANALYTICS_RETENTION_DAYS", "365"))
    
    # Keyword Analysis
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.8"))
    MAX_KEYWORDS_BULK_ANALYSIS: int = int(os.getenv("MAX_KEYWORDS_BULK_ANALYSIS", "50"))
    
    # File Upload
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_FILE_TYPES: list = ["txt", "csv", "json"]
    
    # Development
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
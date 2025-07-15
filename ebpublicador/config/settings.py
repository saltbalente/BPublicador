from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
import os

class Settings(BaseSettings):
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Database
    database_url: str = Field(default="sqlite:///./ebpublicador.db", env="DATABASE_URL")
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # AI Services
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    ai_provider_preference: str = Field(default="openai", env="AI_PROVIDER_PREFERENCE")
    
    # CORS
    cors_origins: List[str] = Field(default=["http://localhost:3000", "http://127.0.0.1:3000"], env="CORS_ORIGINS")
    
    # File Upload
    max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    allowed_file_types: List[str] = Field(default=["image/jpeg", "image/png", "image/gif", "image/webp"], env="ALLOWED_FILE_TYPES")
    
    # Storage
    storage_path: str = Field(default="./storage", env="STORAGE_PATH")
    
    # Application
    app_name: str = Field(default="EBPublicador", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    posts_per_page: int = Field(default=10, env="POSTS_PER_PAGE")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "allow"
    }

# Global settings instance
settings = Settings()

# Cloud platform detection
def is_vercel() -> bool:
    return os.getenv("VERCEL") == "1"

def is_railway() -> bool:
    return os.getenv("RAILWAY_ENVIRONMENT") is not None

def is_render() -> bool:
    return os.getenv("RENDER") == "true"

def is_cloud_environment() -> bool:
    return is_vercel() or is_railway() or is_render()

def get_cloud_platform() -> Optional[str]:
    if is_vercel():
        return "vercel"
    elif is_railway():
        return "railway"
    elif is_render():
        return "render"
    return None
"""Configuration management for EBPublicador.

This module provides environment-aware configuration that automatically
detects the deployment platform and adjusts settings accordingly.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class BaseConfig(BaseSettings):
    """Base configuration with common settings."""
    
    # App Info
    app_name: str = "EBPublicador"
    app_version: str = "2.0.0"
    debug: bool = False
    
    # Environment Detection
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Database
    database_url: str = Field(default="sqlite:///./ebpublicador.db", env="DATABASE_URL")
    
    # Security
    secret_key: str = Field(default="dev-secret-key-change-in-production", env="SECRET_KEY")
    
    # API Settings
    api_prefix: str = "/api/v1"
    cors_origins: list = ["*"]
    
    # Storage Paths (Cloud-aware)
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    storage_dir: Path = Field(default_factory=lambda: Path("./storage"))
    uploads_dir: Path = Field(default_factory=lambda: Path("./storage/uploads"))
    generated_dir: Path = Field(default_factory=lambda: Path("./storage/generated"))
    cache_dir: Path = Field(default_factory=lambda: Path("./storage/cache"))
    
    # AI Services
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    
    # Cloud Storage (Optional)
    cloudinary_url: Optional[str] = Field(default=None, env="CLOUDINARY_URL")
    aws_s3_bucket: Optional[str] = Field(default=None, env="AWS_S3_BUCKET")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "allow"
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._detect_platform()
        self._setup_storage_paths()
    
    def _detect_platform(self) -> str:
        """Detect deployment platform automatically."""
        if os.getenv("VERCEL"):
            self.platform = "vercel"
            self.environment = "production"
        elif os.getenv("RAILWAY_ENVIRONMENT"):
            self.platform = "railway"
            self.environment = os.getenv("RAILWAY_ENVIRONMENT", "production")
        elif os.getenv("RENDER"):
            self.platform = "render"
            self.environment = "production"
        elif os.getenv("DOCKER_CONTAINER"):
            self.platform = "docker"
        else:
            self.platform = "local"
        
        return self.platform
    
    def _setup_storage_paths(self) -> None:
        """Setup storage paths based on platform."""
        if self.platform == "vercel":
            # Vercel: Use /tmp for temporary files
            self.storage_dir = Path("/tmp/storage")
            self.uploads_dir = Path("/tmp/storage/uploads")
            self.generated_dir = Path("/tmp/storage/generated")
            self.cache_dir = Path("/tmp/storage/cache")
        elif self.platform in ["railway", "render", "docker"]:
            # Container platforms: Use relative paths
            self.storage_dir = Path("./storage")
            self.uploads_dir = Path("./storage/uploads")
            self.generated_dir = Path("./storage/generated")
            self.cache_dir = Path("./storage/cache")
        else:
            # Local development: Use project relative paths
            base = Path(__file__).parent.parent
            self.storage_dir = base.joinpath("storage")
            self.uploads_dir = base.joinpath("storage", "uploads")
            self.generated_dir = base.joinpath("storage", "generated")
            self.cache_dir = base.joinpath("storage", "cache")
    
    def ensure_directories(self) -> None:
        """Create storage directories with proper error handling."""
        directories = [
            self.storage_dir,
            self.uploads_dir,
            self.generated_dir,
            self.cache_dir
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                # Test write permissions
                test_file = directory.joinpath(".write_test")
                test_file.touch()
                test_file.unlink()
            except (PermissionError, OSError) as e:
                print(f"Warning: Cannot create/write to {directory}: {e}")
                # Fallback to /tmp if possible
                if self.platform != "vercel":
                    fallback = Path("/tmp").joinpath(directory.name)
                    try:
                        fallback.mkdir(parents=True, exist_ok=True)
                        setattr(self, f"{directory.name}_dir", fallback)
                        print(f"Using fallback directory: {fallback}")
                    except Exception:
                        print(f"Fallback also failed for {directory}")
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def database_config(self) -> Dict[str, Any]:
        """Get database configuration based on environment."""
        if self.platform == "vercel":
            # Vercel: Use in-memory SQLite or external DB
            return {
                "url": self.database_url or "sqlite:///:memory:",
                "echo": False,
                "pool_pre_ping": True
            }
        else:
            return {
                "url": self.database_url,
                "echo": self.debug,
                "pool_pre_ping": True
            }


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    debug: bool = True
    environment: str = "development"
    cors_origins: list = ["http://localhost:3000", "http://localhost:8000", "http://localhost:8001"]


class ProductionConfig(BaseConfig):
    """Production configuration."""
    debug: bool = False
    environment: str = "production"
    

class TestingConfig(BaseConfig):
    """Testing configuration."""
    debug: bool = True
    environment: str = "testing"
    database_url: str = "sqlite:///:memory:"


@lru_cache()
def get_config() -> BaseConfig:
    """Get configuration based on environment."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig
    }
    
    config_class = config_map.get(env, DevelopmentConfig)
    config = config_class()
    
    # Ensure directories exist
    config.ensure_directories()
    
    return config


# Global config instance
config = get_config()
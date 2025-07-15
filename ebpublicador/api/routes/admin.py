"""Admin and configuration API routes."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from api.core.database import get_db, get_db_info, optimize_database
from api.models import Post, Theme, Settings, GenerationHistory
from api.services import storage_service, StorageType
from config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# Pydantic models
from pydantic import BaseModel, Field

class ThemeRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    css_content: str = Field(..., min_length=1)
    is_active: bool = False

class ThemeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    css_content: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class SettingsRequest(BaseModel):
    site_title: Optional[str] = Field(None, max_length=200)
    site_description: Optional[str] = Field(None, max_length=500)
    site_url: Optional[str] = Field(None, max_length=200)
    posts_per_page: Optional[int] = Field(None, ge=1, le=100)
    allow_comments: Optional[bool] = None
    default_post_status: Optional[str] = Field(None, pattern="^(draft|published)$")
    seo_enabled: Optional[bool] = None
    analytics_code: Optional[str] = Field(None, max_length=1000)
    social_sharing: Optional[bool] = None
    auto_backup: Optional[bool] = None
    backup_frequency: Optional[str] = Field(None, pattern="^(daily|weekly|monthly)$")
    ai_provider_preference: Optional[str] = Field(None, pattern="^(openai|gemini|fallback)$")
    max_upload_size: Optional[int] = Field(None, ge=1, le=100)  # MB
    allowed_file_types: Optional[List[str]] = None

class SettingsResponse(BaseModel):
    id: int
    site_title: str
    site_description: str
    site_url: str
    posts_per_page: int
    allow_comments: bool
    default_post_status: str
    seo_enabled: bool
    analytics_code: Optional[str]
    social_sharing: bool
    auto_backup: bool
    backup_frequency: str
    ai_provider_preference: str
    max_upload_size: int
    allowed_file_types: List[str]
    created_at: datetime
    updated_at: datetime

class SystemStatsResponse(BaseModel):
    total_posts: int
    published_posts: int
    draft_posts: int
    total_generations: int
    storage_used: Dict[str, Any]
    database_info: Dict[str, Any]
    system_info: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]


# Themes management
@router.get("/themes", response_model=List[ThemeResponse])
async def get_themes(db: Session = Depends(get_db)):
    """Get all themes."""
    try:
        themes = db.query(Theme).order_by(Theme.created_at.desc()).all()
        return [ThemeResponse(
            id=theme.id,
            name=theme.name,
            description=theme.description,
            css_content=theme.css_content,
            is_active=theme.is_active,
            created_at=theme.created_at,
            updated_at=theme.updated_at
        ) for theme in themes]
        
    except Exception as e:
        logger.error(f"Error getting themes: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving themes")


@router.post("/themes", response_model=ThemeResponse)
async def create_theme(
    theme_data: ThemeRequest,
    db: Session = Depends(get_db)
):
    """Create a new theme."""
    try:
        # Check if theme name already exists
        existing_theme = db.query(Theme).filter(Theme.name == theme_data.name).first()
        if existing_theme:
            raise HTTPException(status_code=400, detail="Theme name already exists")
        
        # If this theme is set as active, deactivate others
        if theme_data.is_active:
            db.query(Theme).update({Theme.is_active: False})
        
        # Create new theme
        theme = Theme(
            name=theme_data.name,
            description=theme_data.description,
            css_content=theme_data.css_content,
            is_active=theme_data.is_active
        )
        
        db.add(theme)
        db.commit()
        db.refresh(theme)
        
        logger.info(f"Theme created: {theme.name} (ID: {theme.id})")
        
        return ThemeResponse(
            id=theme.id,
            name=theme.name,
            description=theme.description,
            css_content=theme.css_content,
            is_active=theme.is_active,
            created_at=theme.created_at,
            updated_at=theme.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating theme: {e}")
        raise HTTPException(status_code=500, detail="Error creating theme")


@router.put("/themes/{theme_id}", response_model=ThemeResponse)
async def update_theme(
    theme_id: int,
    theme_data: ThemeRequest,
    db: Session = Depends(get_db)
):
    """Update an existing theme."""
    try:
        theme = db.query(Theme).filter(Theme.id == theme_id).first()
        if not theme:
            raise HTTPException(status_code=404, detail="Theme not found")
        
        # Check if new name conflicts with existing themes (excluding current)
        if theme_data.name != theme.name:
            existing_theme = db.query(Theme).filter(
                Theme.name == theme_data.name,
                Theme.id != theme_id
            ).first()
            if existing_theme:
                raise HTTPException(status_code=400, detail="Theme name already exists")
        
        # If this theme is set as active, deactivate others
        if theme_data.is_active and not theme.is_active:
            db.query(Theme).update({Theme.is_active: False})
        
        # Update theme
        theme.name = theme_data.name
        theme.description = theme_data.description
        theme.css_content = theme_data.css_content
        theme.is_active = theme_data.is_active
        
        db.commit()
        db.refresh(theme)
        
        logger.info(f"Theme updated: {theme.name} (ID: {theme.id})")
        
        return ThemeResponse(
            id=theme.id,
            name=theme.name,
            description=theme.description,
            css_content=theme.css_content,
            is_active=theme.is_active,
            created_at=theme.created_at,
            updated_at=theme.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating theme {theme_id}: {e}")
        raise HTTPException(status_code=500, detail="Error updating theme")


@router.delete("/themes/{theme_id}")
async def delete_theme(
    theme_id: int,
    db: Session = Depends(get_db)
):
    """Delete a theme."""
    try:
        theme = db.query(Theme).filter(Theme.id == theme_id).first()
        if not theme:
            raise HTTPException(status_code=404, detail="Theme not found")
        
        if theme.is_active:
            raise HTTPException(status_code=400, detail="Cannot delete active theme")
        
        db.delete(theme)
        db.commit()
        
        logger.info(f"Theme deleted: {theme.name} (ID: {theme_id})")
        
        return JSONResponse(
            status_code=200,
            content={"message": "Theme deleted successfully"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting theme {theme_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting theme")


@router.post("/themes/{theme_id}/activate")
async def activate_theme(
    theme_id: int,
    db: Session = Depends(get_db)
):
    """Activate a theme (deactivates all others)."""
    try:
        theme = db.query(Theme).filter(Theme.id == theme_id).first()
        if not theme:
            raise HTTPException(status_code=404, detail="Theme not found")
        
        # Deactivate all themes
        db.query(Theme).update({Theme.is_active: False})
        
        # Activate selected theme
        theme.is_active = True
        
        db.commit()
        
        logger.info(f"Theme activated: {theme.name} (ID: {theme_id})")
        
        return JSONResponse(
            status_code=200,
            content={"message": f"Theme '{theme.name}' activated successfully"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error activating theme {theme_id}: {e}")
        raise HTTPException(status_code=500, detail="Error activating theme")


# Settings management
@router.get("/settings", response_model=SettingsResponse)
async def get_settings(db: Session = Depends(get_db)):
    """Get system settings."""
    try:
        settings = db.query(Settings).first()
        
        if not settings:
            # Create default settings if none exist
            settings = Settings(
                site_title="EBPublicador",
                site_description="AI-Powered Content Management System",
                site_url="http://localhost:8000",
                posts_per_page=10,
                allow_comments=True,
                default_post_status="draft",
                seo_enabled=True,
                social_sharing=True,
                auto_backup=False,
                backup_frequency="weekly",
                ai_provider_preference="openai",
                max_upload_size=10,
                allowed_file_types=["jpg", "jpeg", "png", "gif", "webp", "svg", "pdf", "doc", "docx"]
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)
        
        return SettingsResponse(
            id=settings.id,
            site_title=settings.site_title,
            site_description=settings.site_description,
            site_url=settings.site_url,
            posts_per_page=settings.posts_per_page,
            allow_comments=settings.allow_comments,
            default_post_status=settings.default_post_status,
            seo_enabled=settings.seo_enabled,
            analytics_code=settings.analytics_code,
            social_sharing=settings.social_sharing,
            auto_backup=settings.auto_backup,
            backup_frequency=settings.backup_frequency,
            ai_provider_preference=settings.ai_provider_preference,
            max_upload_size=settings.max_upload_size,
            allowed_file_types=settings.allowed_file_types,
            created_at=settings.created_at,
            updated_at=settings.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving settings")


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
    settings_data: SettingsRequest,
    db: Session = Depends(get_db)
):
    """Update system settings."""
    try:
        settings = db.query(Settings).first()
        
        if not settings:
            raise HTTPException(status_code=404, detail="Settings not found")
        
        # Update only provided fields
        update_data = settings_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(settings, field, value)
        
        db.commit()
        db.refresh(settings)
        
        logger.info("System settings updated")
        
        return SettingsResponse(
            id=settings.id,
            site_title=settings.site_title,
            site_description=settings.site_description,
            site_url=settings.site_url,
            posts_per_page=settings.posts_per_page,
            allow_comments=settings.allow_comments,
            default_post_status=settings.default_post_status,
            seo_enabled=settings.seo_enabled,
            analytics_code=settings.analytics_code,
            social_sharing=settings.social_sharing,
            auto_backup=settings.auto_backup,
            backup_frequency=settings.backup_frequency,
            ai_provider_preference=settings.ai_provider_preference,
            max_upload_size=settings.max_upload_size,
            allowed_file_types=settings.allowed_file_types,
            created_at=settings.created_at,
            updated_at=settings.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail="Error updating settings")


# System statistics and monitoring
@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(db: Session = Depends(get_db)):
    """Get comprehensive system statistics."""
    try:
        # Post statistics
        total_posts = db.query(Post).count()
        published_posts = db.query(Post).filter(Post.status == "published").count()
        draft_posts = db.query(Post).filter(Post.status == "draft").count()
        
        # Generation statistics
        total_generations = db.query(GenerationHistory).count()
        
        # Storage statistics
        storage_stats = storage_service.get_storage_stats()
        
        # Database information
        db_info = get_db_info()
        
        # System information
        system_info = {
            "environment": config.environment,
            "debug_mode": config.debug,
            "storage_path": str(config.storage_path),
            "database_url": config.database_url.split("@")[-1] if "@" in config.database_url else config.database_url,
            "upload_max_size": config.upload_max_size_mb,
            "allowed_origins": config.allowed_origins
        }
        
        # Recent activity (last 10 posts and generations)
        recent_posts = db.query(Post).order_by(Post.created_at.desc()).limit(5).all()
        recent_generations = db.query(GenerationHistory).order_by(
            GenerationHistory.created_at.desc()
        ).limit(5).all()
        
        recent_activity = []
        
        for post in recent_posts:
            recent_activity.append({
                "type": "post",
                "action": "created" if post.status == "draft" else "published",
                "title": post.title,
                "timestamp": post.created_at
            })
        
        for gen in recent_generations:
            recent_activity.append({
                "type": "generation",
                "action": "generated",
                "title": f"{gen.content_type}: {gen.topic}",
                "timestamp": gen.created_at
            })
        
        # Sort by timestamp
        recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_activity = recent_activity[:10]
        
        return SystemStatsResponse(
            total_posts=total_posts,
            published_posts=published_posts,
            draft_posts=draft_posts,
            total_generations=total_generations,
            storage_used=storage_stats,
            database_info=db_info,
            system_info=system_info,
            recent_activity=recent_activity
        )
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving system statistics")


@router.post("/backup")
async def create_backup(db: Session = Depends(get_db)):
    """Create a system backup."""
    try:
        from api.core.database import backup_database
        
        # Create database backup
        backup_path = backup_database()
        
        if backup_path:
            logger.info(f"Database backup created: {backup_path}")
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Backup created successfully",
                    "backup_path": str(backup_path),
                    "timestamp": datetime.now().isoformat()
                }
            )
        else:
            raise HTTPException(status_code=500, detail="Backup creation failed")
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(status_code=500, detail="Error creating backup")


@router.post("/optimize")
async def optimize_system(db: Session = Depends(get_db)):
    """Optimize system performance."""
    try:
        # Optimize database
        optimize_database()
        
        # Clean up old files
        cleanup_stats = storage_service.cleanup_old_files(days=30)
        
        logger.info("System optimization completed")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "System optimization completed",
                "cleanup_stats": cleanup_stats,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error optimizing system: {e}")
        raise HTTPException(status_code=500, detail="Error optimizing system")


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check."""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # Database check
        try:
            db.execute(text("SELECT 1"))
            health_status["checks"]["database"] = "healthy"
        except Exception as e:
            health_status["checks"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # Storage check
        try:
            storage_stats = storage_service.get_storage_stats()
            if storage_stats["total_files"] >= 0:
                health_status["checks"]["storage"] = "healthy"
            else:
                health_status["checks"]["storage"] = "unhealthy: storage not accessible"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["checks"]["storage"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # AI services check
        try:
            from api.services import content_service
            if content_service.providers:
                health_status["checks"]["ai_services"] = "healthy"
            else:
                health_status["checks"]["ai_services"] = "degraded: no providers configured"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["checks"]["ai_services"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        
        return JSONResponse(
            status_code=status_code,
            content=health_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@router.post("/upload-theme")
async def upload_theme_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a theme CSS file."""
    try:
        # Validate file type
        if not file.filename.endswith('.css'):
            raise HTTPException(status_code=400, detail="Only CSS files are allowed")
        
        # Read file content
        content = await file.read()
        css_content = content.decode('utf-8')
        
        # Extract theme name from filename
        theme_name = file.filename.replace('.css', '').replace('_', ' ').replace('-', ' ').title()
        
        # Check if theme already exists
        existing_theme = db.query(Theme).filter(Theme.name == theme_name).first()
        if existing_theme:
            theme_name = f"{theme_name} (Uploaded {datetime.now().strftime('%Y%m%d_%H%M%S')})"
        
        # Create theme
        theme = Theme(
            name=theme_name,
            description=f"Uploaded theme from {file.filename}",
            css_content=css_content,
            is_active=False
        )
        
        db.add(theme)
        db.commit()
        db.refresh(theme)
        
        logger.info(f"Theme uploaded: {theme_name} (ID: {theme.id})")
        
        return JSONResponse(
            status_code=201,
            content={
                "message": "Theme uploaded successfully",
                "theme_id": theme.id,
                "theme_name": theme_name
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading theme: {e}")
        raise HTTPException(status_code=500, detail="Error uploading theme")
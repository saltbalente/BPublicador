"""Database configuration and management."""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging
from typing import Generator

from config import config

logger = logging.getLogger(__name__)

# Database configuration based on environment
db_config = config.database_config

# Create engine with appropriate settings
if "sqlite" in db_config["url"]:
    # SQLite configuration
    engine = create_engine(
        db_config["url"],
        echo=db_config["echo"],
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        },
        poolclass=StaticPool if ":memory:" in db_config["url"] else None
    )
else:
    # PostgreSQL or other databases
    engine = create_engine(
        db_config["url"],
        echo=db_config["echo"],
        pool_pre_ping=db_config["pool_pre_ping"],
        pool_recycle=3600,
        pool_size=5,
        max_overflow=10
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database transaction error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def init_db() -> None:
    """Initialize database with error handling."""
    try:
        # Import all models to ensure they're registered
        try:
            from api.models.post import Post
            from api.models.theme import Theme
            from api.models.setting import Setting
            from api.models.generation_history import GenerationHistory
        except ImportError:
            # Models might not exist yet, that's ok
            pass
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Test connection
        from sqlalchemy import text
        with get_db_context() as db:
            db.execute(text("SELECT 1"))
        
        logger.info(f"Database initialized successfully: {db_config['url']}")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        
        # Try fallback for cloud environments
        try:
            from config.settings import is_cloud_environment
            if is_cloud_environment():
                logger.info("Attempting fallback database configuration...")
                # Use in-memory SQLite as last resort
                fallback_engine = create_engine(
                    "sqlite:///:memory:",
                    echo=False,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool
                )
                # Update global variables
                globals()['engine'] = fallback_engine
                globals()['SessionLocal'] = sessionmaker(autocommit=False, autoflush=False, bind=fallback_engine)
                Base.metadata.create_all(bind=fallback_engine)
                logger.info("Fallback in-memory database initialized")
            else:
                raise
        except Exception as fallback_error:
            logger.error(f"Fallback database also failed: {fallback_error}")
            raise


def check_db_health() -> dict:
    """Check database health for monitoring."""
    try:
        with get_db_context() as db:
            result = db.execute("SELECT 1").scalar()
            return {
                "status": "healthy",
                "database_url": db_config["url"].split("@")[-1] if "@" in db_config["url"] else db_config["url"],
                "connection": "ok"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "connection": "failed"
        }


class DatabaseManager:
    """Database manager for advanced operations."""
    
    @staticmethod
    def backup_database(backup_path: str = None) -> bool:
        """Backup database (SQLite only)."""
        if "sqlite" not in db_config["url"] or ":memory:" in db_config["url"]:
            logger.warning("Backup only supported for file-based SQLite databases")
            return False
        
        try:
            import shutil
            from pathlib import Path
            
            # Extract database file path
            db_file = db_config["url"].replace("sqlite:///", "")
            if not backup_path:
                backup_path = f"{db_file}.backup"
            
            shutil.copy2(db_file, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    @staticmethod
    def get_table_info() -> dict:
        """Get information about database tables."""
        try:
            with get_db_context() as db:
                # Get table names
                if "sqlite" in db_config["url"]:
                    tables = db.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                else:
                    tables = db.execute(
                        "SELECT tablename FROM pg_tables WHERE schemaname='public'"
                    ).fetchall()
                
                return {
                    "tables": [table[0] for table in tables],
                    "count": len(tables)
                }
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def optimize_database() -> bool:
        """Optimize database performance."""
        try:
            with get_db_context() as db:
                if "sqlite" in db_config["url"]:
                    db.execute("VACUUM")
                    db.execute("ANALYZE")
                else:
                    db.execute("VACUUM ANALYZE")
                
                logger.info("Database optimized successfully")
                return True
                
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()

def get_db_info() -> dict:
    """Get basic database information for testing."""
    try:
        if "sqlite" in db_config["url"]:
            db_type = "SQLite"
            if ":memory:" in db_config["url"]:
                size = "In-memory"
            else:
                try:
                    import os
                    db_file = db_config["url"].replace("sqlite:///", "")
                    if os.path.exists(db_file):
                        size_bytes = os.path.getsize(db_file)
                        size = f"{size_bytes / 1024:.2f} KB"
                    else:
                        size = "File not found"
                except Exception:
                    size = "Unknown"
        else:
            db_type = "PostgreSQL"
            size = "Remote database"
        
        return {
            "type": db_type,
            "size": size,
            "url": db_config["url"].split("@")[-1] if "@" in db_config["url"] else db_config["url"]
        }
    except Exception as e:
        return {
            "type": "Unknown",
            "size": "Unknown",
            "error": str(e)
        }


def optimize_database() -> bool:
    """Optimize database performance (SQLite only)."""
    try:
        if "sqlite" not in db_config["url"] or ":memory:" in db_config["url"]:
            logger.warning("Database optimization only supported for file-based SQLite databases")
            return False
            
        with get_db_context() as db:
            # Run SQLite optimization commands
            from sqlalchemy import text
            db.execute(text("VACUUM"))
            db.execute(text("ANALYZE"))
            
        logger.info("Database optimization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        return False
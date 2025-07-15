"""Main application entry point for EBPublicador."""

import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.core.app import create_app
from config import config

# Configure logging
storage_path = Path(config.storage_path)
logging.basicConfig(
    level=logging.INFO if not config.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(storage_path / "logs" / "app.log", mode='a')
    ] if (storage_path / "logs").exists() else [logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Create FastAPI application
app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting EBPublicador in {config.environment} mode")
    logger.info(f"Debug mode: {config.debug}")
    logger.info(f"Storage path: {config.storage_path}")
    logger.info(f"Database: {config.database_url.split('@')[-1] if '@' in config.database_url else config.database_url}")
    
    # Development server configuration
    uvicorn_config = {
        "app": "main:app",
        "host": "0.0.0.0",
        "port": 8000,
        "reload": config.debug,
        "log_level": "debug" if config.debug else "info",
        "access_log": True
    }
    
    # Adjust configuration for cloud environments
    if config.environment == "vercel":
        # Vercel handles the server, we just export the app
        pass
    elif config.environment in ["railway", "render"]:
        # Use PORT environment variable if available
        import os
        port = int(os.getenv("PORT", 8000))
        uvicorn_config["port"] = port
        uvicorn_config["reload"] = False  # Disable reload in production
        logger.info(f"Production mode - Port: {port}")
    
    # Start the server (only in local development)
    if config.environment == "local":
        uvicorn.run(**uvicorn_config)
    else:
        logger.info("Application ready for cloud deployment")
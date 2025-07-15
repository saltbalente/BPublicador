"""Error handling middleware for robust error management."""

import logging
import traceback
import time
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from config import config

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors gracefully across all environments."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.debug = config.debug
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle any errors."""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Log successful requests in debug mode
            if self.debug:
                process_time = time.time() - start_time
                logger.debug(
                    f"{request.method} {request.url.path} - "
                    f"Status: {response.status_code} - "
                    f"Time: {process_time:.3f}s"
                )
            
            return response
            
        except HTTPException as exc:
            # Handle FastAPI HTTP exceptions
            return await self._handle_http_exception(request, exc, start_time)
            
        except Exception as exc:
            # Handle unexpected exceptions
            return await self._handle_general_exception(request, exc, start_time)
    
    async def _handle_http_exception(
        self, 
        request: Request, 
        exc: HTTPException, 
        start_time: float
    ) -> JSONResponse:
        """Handle HTTP exceptions (4xx, 5xx)."""
        process_time = time.time() - start_time
        
        # Log the error
        logger.warning(
            f"{request.method} {request.url.path} - "
            f"HTTP {exc.status_code}: {exc.detail} - "
            f"Time: {process_time:.3f}s"
        )
        
        # Prepare error response
        error_response = {
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path),
                "method": request.method,
                "timestamp": time.time()
            }
        }
        
        # Add debug info in development
        if self.debug:
            error_response["error"]["process_time"] = f"{process_time:.3f}s"
            if hasattr(exc, "headers") and exc.headers:
                error_response["error"]["headers"] = exc.headers
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
    
    async def _handle_general_exception(
        self, 
        request: Request, 
        exc: Exception, 
        start_time: float
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        process_time = time.time() - start_time
        
        # Log the full error with traceback
        logger.error(
            f"{request.method} {request.url.path} - "
            f"Unhandled exception: {type(exc).__name__}: {str(exc)} - "
            f"Time: {process_time:.3f}s",
            exc_info=True
        )
        
        # Determine status code based on exception type
        status_code = self._get_status_code_for_exception(exc)
        
        # Prepare error response
        error_response = {
            "error": {
                "code": status_code,
                "message": "Internal server error",
                "path": str(request.url.path),
                "method": request.method,
                "timestamp": time.time()
            }
        }
        
        # Add debug info in development
        if self.debug:
            error_response["error"].update({
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "process_time": f"{process_time:.3f}s",
                "traceback": traceback.format_exc().split("\n")
            })
        
        return JSONResponse(
            status_code=status_code,
            content=error_response
        )
    
    def _get_status_code_for_exception(self, exc: Exception) -> int:
        """Determine appropriate HTTP status code for exception."""
        exception_status_map = {
            "ValidationError": 422,
            "ValueError": 400,
            "KeyError": 400,
            "FileNotFoundError": 404,
            "PermissionError": 403,
            "TimeoutError": 408,
            "ConnectionError": 503,
            "DatabaseError": 503,
            "SQLAlchemyError": 503,
        }
        
        exception_name = type(exc).__name__
        
        # Check for specific exception types
        for exc_type, status_code in exception_status_map.items():
            if exc_type in exception_name:
                return status_code
        
        # Default to 500 for unknown exceptions
        return 500


class CloudErrorHandler:
    """Specialized error handling for cloud environments."""
    
    @staticmethod
    def handle_permission_error(exc: PermissionError, request: Request) -> JSONResponse:
        """Handle permission errors common in cloud deployments."""
        logger.warning(f"Permission error on {request.url.path}: {exc}")
        
        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "code": 403,
                    "message": "Permission denied - using fallback storage",
                    "path": str(request.url.path),
                    "suggestion": "File operation failed, but application continues with alternative storage"
                }
            }
        )
    
    @staticmethod
    def handle_storage_error(exc: Exception, request: Request) -> JSONResponse:
        """Handle storage-related errors."""
        logger.warning(f"Storage error on {request.url.path}: {exc}")
        
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": 503,
                    "message": "Storage temporarily unavailable",
                    "path": str(request.url.path),
                    "suggestion": "Please try again later or use alternative upload method"
                }
            }
        )
    
    @staticmethod
    def handle_ai_service_error(exc: Exception, request: Request) -> JSONResponse:
        """Handle AI service errors."""
        logger.warning(f"AI service error on {request.url.path}: {exc}")
        
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": 503,
                    "message": "AI service temporarily unavailable",
                    "path": str(request.url.path),
                    "suggestion": "Please try again later or use manual content creation"
                }
            }
        )
    
    @staticmethod
    def handle_database_error(exc: Exception, request: Request) -> JSONResponse:
        """Handle database connection errors."""
        logger.error(f"Database error on {request.url.path}: {exc}")
        
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": 503,
                    "message": "Database temporarily unavailable",
                    "path": str(request.url.path),
                    "suggestion": "Please try again in a few moments"
                }
            }
        )


# Global error handler instance
cloud_error_handler = CloudErrorHandler()
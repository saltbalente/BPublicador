"""Logging middleware for comprehensive request/response tracking."""

import logging
import time
import json
import uuid
from typing import Callable, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from config import config

# Configure logger
logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive request/response logging."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.debug = config.debug
        self.log_requests = True
        self.log_responses = True
        self.log_body = config.debug  # Only log body in debug mode
        
        # Paths to exclude from logging (to reduce noise)
        self.exclude_paths = {
            "/health",
            "/favicon.ico",
            "/robots.txt",
            "/sitemap.xml"
        }
        
        # Sensitive headers to mask
        self.sensitive_headers = {
            "authorization",
            "x-api-key",
            "cookie",
            "set-cookie",
            "x-auth-token"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with comprehensive logging."""
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Log incoming request
        if self.log_requests:
            await self._log_request(request, request_id)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add processing time to response headers
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            response.headers["X-Request-ID"] = request_id
            
            # Log response
            if self.log_responses:
                await self._log_response(request, response, request_id, process_time)
            
            return response
            
        except Exception as exc:
            # Log exception
            process_time = time.time() - start_time
            await self._log_exception(request, exc, request_id, process_time)
            raise
    
    async def _log_request(self, request: Request, request_id: str) -> None:
        """Log incoming request details."""
        try:
            # Basic request info
            log_data = {
                "type": "request",
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent", "unknown"),
                "timestamp": time.time()
            }
            
            # Add headers (masked sensitive ones)
            if self.debug:
                log_data["headers"] = self._mask_sensitive_headers(dict(request.headers))
            
            # Add body for POST/PUT requests in debug mode
            if self.log_body and request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await self._get_request_body(request)
                    if body:
                        log_data["body_size"] = len(body)
                        # Only log first 500 chars of body to avoid huge logs
                        if len(body) <= 500:
                            log_data["body_preview"] = body[:500]
                        else:
                            log_data["body_preview"] = body[:500] + "..."
                except Exception:
                    log_data["body_error"] = "Could not read request body"
            
            logger.info(f"Request: {json.dumps(log_data, default=str)}")
            
        except Exception as e:
            logger.error(f"Error logging request {request_id}: {e}")
    
    async def _log_response(
        self, 
        request: Request, 
        response: Response, 
        request_id: str, 
        process_time: float
    ) -> None:
        """Log response details."""
        try:
            log_data = {
                "type": "response",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": f"{process_time:.3f}s",
                "response_size": len(getattr(response, "body", b"")),
                "timestamp": time.time()
            }
            
            # Add response headers in debug mode
            if self.debug:
                log_data["headers"] = self._mask_sensitive_headers(dict(response.headers))
            
            # Determine log level based on status code
            if response.status_code >= 500:
                logger.error(f"Response: {json.dumps(log_data, default=str)}")
            elif response.status_code >= 400:
                logger.warning(f"Response: {json.dumps(log_data, default=str)}")
            else:
                logger.info(f"Response: {json.dumps(log_data, default=str)}")
                
        except Exception as e:
            logger.error(f"Error logging response {request_id}: {e}")
    
    async def _log_exception(
        self, 
        request: Request, 
        exc: Exception, 
        request_id: str, 
        process_time: float
    ) -> None:
        """Log exception details."""
        try:
            log_data = {
                "type": "exception",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "process_time": f"{process_time:.3f}s",
                "timestamp": time.time()
            }
            
            logger.error(f"Exception: {json.dumps(log_data, default=str)}", exc_info=True)
            
        except Exception as e:
            logger.error(f"Error logging exception {request_id}: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers."""
        # Check common headers for real IP (useful behind proxies)
        ip_headers = [
            "x-forwarded-for",
            "x-real-ip",
            "cf-connecting-ip",  # Cloudflare
            "x-client-ip",
            "x-forwarded",
            "forwarded-for",
            "forwarded"
        ]
        
        for header in ip_headers:
            if header in request.headers:
                # Take first IP if multiple (comma-separated)
                ip = request.headers[header].split(",")[0].strip()
                if ip:
                    return ip
        
        # Fallback to client host
        return getattr(request.client, "host", "unknown")
    
    def _mask_sensitive_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Mask sensitive header values."""
        masked_headers = {}
        
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                # Mask sensitive values
                if len(value) > 8:
                    masked_headers[key] = value[:4] + "*" * (len(value) - 8) + value[-4:]
                else:
                    masked_headers[key] = "*" * len(value)
            else:
                masked_headers[key] = value
        
        return masked_headers
    
    async def _get_request_body(self, request: Request) -> str:
        """Safely extract request body."""
        try:
            # Check if body was already read
            if hasattr(request.state, "body"):
                return request.state.body
            
            # Read body
            body = await request.body()
            
            # Store in request state for later use
            request.state.body = body.decode("utf-8", errors="ignore")
            
            return request.state.body
            
        except Exception:
            return "[Could not read body]"


class PerformanceLogger:
    """Logger for performance metrics."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.performance")
        self.slow_request_threshold = 2.0  # seconds
    
    def log_slow_request(
        self, 
        request: Request, 
        process_time: float, 
        request_id: str
    ) -> None:
        """Log slow requests for performance monitoring."""
        if process_time > self.slow_request_threshold:
            self.logger.warning(
                f"Slow request detected: {request.method} {request.url.path} - "
                f"Time: {process_time:.3f}s - ID: {request_id}"
            )
    
    def log_memory_usage(self, request_id: str) -> None:
        """Log memory usage (if available)."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            self.logger.debug(
                f"Memory usage - RSS: {memory_info.rss / 1024 / 1024:.2f}MB - "
                f"VMS: {memory_info.vms / 1024 / 1024:.2f}MB - ID: {request_id}"
            )
        except ImportError:
            # psutil not available, skip memory logging
            pass
        except Exception as e:
            self.logger.debug(f"Could not log memory usage: {e}")


# Global performance logger instance
performance_logger = PerformanceLogger()
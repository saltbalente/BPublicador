import re
import time
import hashlib
import secrets
from typing import Dict, List, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
import html
try:
    import bleach
except ImportError:
    bleach = None
from urllib.parse import unquote

# Configurar logging de seguridad
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)

# Crear handler para archivo de logs de seguridad
handler = logging.FileHandler("logs/security.log")
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
handler.setFormatter(formatter)
security_logger.addHandler(handler)

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        max_requests_per_minute: int = 60,
        max_requests_per_hour: int = 1000,
        blocked_ips: Optional[List[str]] = None,
        allowed_file_types: Optional[List[str]] = None,
        max_content_length: int = 10 * 1024 * 1024,  # 10MB
    ):
        super().__init__(app)
        self.max_requests_per_minute = max_requests_per_minute
        self.max_requests_per_hour = max_requests_per_hour
        self.blocked_ips = set(blocked_ips or [])
        self.allowed_file_types = allowed_file_types or [
            'jpg', 'jpeg', 'png', 'gif', 'webp', 'txt', 'csv', 'json'
        ]
        self.max_content_length = max_content_length
        
        # Rate limiting storage
        self.request_counts_minute: Dict[str, deque] = defaultdict(deque)
        self.request_counts_hour: Dict[str, deque] = defaultdict(deque)
        
        # Suspicious activity tracking
        self.suspicious_ips: Dict[str, int] = defaultdict(int)
        self.blocked_until: Dict[str, datetime] = {}
        
        # SQL injection patterns
        self.sql_injection_patterns = [
            r"('|(\-\-)|(;)|(\||\|)|(\*|\*))",
            r"((\%27)|(\'))((\%6F|o|\%4F))(\%72|r|\%52)",
            r"((\%27)|(\'))((\%75|u|\%55))(\%6E|n|\%4E)(\%69|i|\%49)(\%6F|o|\%4F)(\%6E|n|\%4E)",
            r"((\%27)|(\'))((\%73|s|\%53))(\%65|e|\%45)(\%6C|l|\%4C)(\%65|e|\%45)(\%63|c|\%43)(\%74|t|\%54)",
            r"exec(\s|\+)+(s|x)p\w+",
            r"union\s+select",
            r"drop\s+table",
            r"insert\s+into",
            r"delete\s+from",
            r"update\s+set",
            r"create\s+table",
            r"alter\s+table",
            r"truncate\s+table"
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>",
            r"<object[^>]*>.*?</object>",
            r"<embed[^>]*>.*?</embed>",
            r"<link[^>]*>.*?</link>",
            r"<meta[^>]*>.*?</meta>",
            r"vbscript:",
            r"expression\s*\(",
            r"@import",
            r"<\w+[^>]*\s+on\w+\s*="
        ]
        
        # Path traversal patterns
        self.path_traversal_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
            r"%2e%2e%5c",
            r"\.\.\%2f",
            r"\.\.\%5c"
        ]

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        
        try:
            # 1. Verificar IP bloqueada
            if await self._is_ip_blocked(client_ip):
                security_logger.warning(f"Blocked IP attempted access: {client_ip}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Access denied"}
                )
            
            # 2. Rate limiting
            if await self._check_rate_limit(client_ip):
                security_logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"}
                )
            
            # 3. Validar tamaño del contenido
            if await self._check_content_length(request):
                security_logger.warning(f"Content too large from IP: {client_ip}")
                return JSONResponse(
                    status_code=413,
                    content={"detail": "Content too large"}
                )
            
            # 4. Detectar ataques de inyección
            if await self._detect_injection_attacks(request):
                await self._log_suspicious_activity(client_ip, "injection_attempt")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid request"}
                )
            
            # 5. Sanitizar entrada
            await self._sanitize_request(request)
            
            # Procesar la solicitud
            response = await call_next(request)
            
            # 6. Agregar headers de seguridad
            response = await self._add_security_headers(response)
            
            # Log de solicitud exitosa
            process_time = time.time() - start_time
            security_logger.info(
                f"Request processed - IP: {client_ip}, "
                f"Method: {request.method}, Path: {request.url.path}, "
                f"Time: {process_time:.3f}s"
            )
            
            return response
            
        except Exception as e:
            security_logger.error(f"Security middleware error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )

    def _get_client_ip(self, request: Request) -> str:
        """Obtener la IP real del cliente considerando proxies"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

    async def _is_ip_blocked(self, ip: str) -> bool:
        """Verificar si la IP está bloqueada"""
        # Verificar lista de IPs bloqueadas permanentemente
        if ip in self.blocked_ips:
            return True
        
        # Verificar bloqueo temporal
        if ip in self.blocked_until:
            if datetime.now() < self.blocked_until[ip]:
                return True
            else:
                del self.blocked_until[ip]
        
        return False

    async def _check_rate_limit(self, ip: str) -> bool:
        """Verificar límites de velocidad"""
        now = datetime.now()
        
        # Limpiar solicitudes antiguas
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        # Filtrar solicitudes del último minuto
        while (self.request_counts_minute[ip] and 
               self.request_counts_minute[ip][0] < minute_ago):
            self.request_counts_minute[ip].popleft()
        
        # Filtrar solicitudes de la última hora
        while (self.request_counts_hour[ip] and 
               self.request_counts_hour[ip][0] < hour_ago):
            self.request_counts_hour[ip].popleft()
        
        # Verificar límites
        if len(self.request_counts_minute[ip]) >= self.max_requests_per_minute:
            return True
        
        if len(self.request_counts_hour[ip]) >= self.max_requests_per_hour:
            return True
        
        # Agregar solicitud actual
        self.request_counts_minute[ip].append(now)
        self.request_counts_hour[ip].append(now)
        
        return False

    async def _check_content_length(self, request: Request) -> bool:
        """Verificar tamaño del contenido"""
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_content_length:
            return True
        return False

    async def _detect_injection_attacks(self, request: Request) -> bool:
        """Detectar intentos de inyección SQL, XSS y path traversal"""
        # Obtener datos para analizar
        url_path = str(request.url.path).lower()
        query_params = str(request.url.query).lower() if request.url.query else ""
        
        # Analizar headers
        headers_str = " ".join([f"{k}:{v}" for k, v in request.headers.items()]).lower()
        
        # Combinar todos los datos
        data_to_check = f"{url_path} {query_params} {headers_str}"
        
        # Decodificar URL encoding
        data_to_check = unquote(data_to_check)
        
        # Verificar patrones de inyección SQL
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, data_to_check, re.IGNORECASE):
                security_logger.warning(f"SQL injection attempt detected: {pattern}")
                return True
        
        # Verificar patrones XSS
        for pattern in self.xss_patterns:
            if re.search(pattern, data_to_check, re.IGNORECASE):
                security_logger.warning(f"XSS attempt detected: {pattern}")
                return True
        
        # Verificar path traversal
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, data_to_check, re.IGNORECASE):
                security_logger.warning(f"Path traversal attempt detected: {pattern}")
                return True
        
        return False

    async def _sanitize_request(self, request: Request):
        """Sanitizar datos de entrada"""
        # Esta función puede expandirse para sanitizar específicamente
        # los datos del request body si es necesario
        pass

    async def _add_security_headers(self, response: Response) -> Response:
        """Agregar headers de seguridad"""
        # Prevenir XSS
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Prevenir clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevenir MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Política de referrer
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Strict Transport Security (solo en HTTPS)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        
        return response

    async def _log_suspicious_activity(self, ip: str, activity_type: str):
        """Registrar actividad sospechosa y bloquear IP si es necesario"""
        self.suspicious_ips[ip] += 1
        
        security_logger.warning(
            f"Suspicious activity detected - IP: {ip}, "
            f"Type: {activity_type}, Count: {self.suspicious_ips[ip]}"
        )
        
        # Bloquear IP temporalmente después de 5 intentos sospechosos
        if self.suspicious_ips[ip] >= 5:
            self.blocked_until[ip] = datetime.now() + timedelta(hours=1)
            security_logger.error(f"IP blocked for 1 hour: {ip}")


class InputSanitizer:
    """Clase para sanitizar entrada de usuario"""
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Sanitizar HTML para prevenir XSS"""
        if not text:
            return text
        
        if bleach is None:
            # Fallback simple si bleach no está disponible
            return html.escape(text)
        
        # Permitir solo tags seguros
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        allowed_attributes = {}
        
        return bleach.clean(text, tags=allowed_tags, attributes=allowed_attributes, strip=True)
    
    @staticmethod
    def sanitize_sql_input(text: str) -> str:
        """Sanitizar entrada para prevenir inyección SQL"""
        if not text:
            return text
        
        # Escapar caracteres peligrosos
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
        
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        return text.strip()
    
    @staticmethod
    def validate_file_upload(filename: str, allowed_types: List[str]) -> bool:
        """Validar archivo subido"""
        if not filename:
            return False
        
        # Verificar extensión
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        if extension not in allowed_types:
            return False
        
        # Verificar caracteres peligrosos en el nombre
        dangerous_patterns = ['../', '..\\', '<', '>', '|', '&', ';']
        for pattern in dangerous_patterns:
            if pattern in filename:
                return False
        
        return True
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generar token CSRF"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple:
        """Hash seguro de contraseña"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Usar PBKDF2 con SHA-256
        hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return hashed.hex(), salt
    
    @staticmethod
    def verify_password(password: str, hashed: str, salt: str) -> bool:
        """Verificar contraseña"""
        new_hash, _ = InputSanitizer.hash_password(password, salt)
        return new_hash == hashed
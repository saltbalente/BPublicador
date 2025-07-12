from typing import List, Dict
from datetime import timedelta

class SecurityConfig:
    """Configuración centralizada de seguridad"""
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE = 60
    MAX_REQUESTS_PER_HOUR = 1000
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_DURATION = timedelta(minutes=15)
    
    # Content Security
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_FILE_TYPES = [
        'jpg', 'jpeg', 'png', 'gif', 'webp', 
        'txt', 'csv', 'json', 'pdf'
    ]
    
    # Blocked IPs (ejemplo - en producción cargar desde base de datos)
    BLOCKED_IPS: List[str] = [
        # Agregar IPs maliciosas conocidas
    ]
    
    # Trusted IPs (opcional - para whitelist)
    TRUSTED_IPS: List[str] = [
        '127.0.0.1',
        'localhost'
    ]
    
    # Headers de seguridad
    SECURITY_HEADERS = {
        'X-XSS-Protection': '1; mode=block',
        'X-Frame-Options': 'DENY',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
    }
    
    # Patrones de ataques comunes
    SQL_INJECTION_PATTERNS = [
        r"('|(\-\-)|(;)|(\||\|)|(\*|\*))",
        r"((\%27)|(\'))(\%6F|o|\%4F)(\%72|r|\%52)",
        r"union\s+select",
        r"drop\s+table",
        r"insert\s+into",
        r"delete\s+from",
        r"update\s+set",
        r"create\s+table",
        r"alter\s+table",
        r"truncate\s+table"
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>.*?</embed>",
        r"vbscript:",
        r"expression\s*\(",
        r"@import"
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e%5c"
    ]
    
    # Configuración de logging de seguridad
    SECURITY_LOG_FILE = "logs/security.log"
    SECURITY_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configuración de alertas
    ALERT_THRESHOLD_SUSPICIOUS_ACTIVITY = 5
    ALERT_THRESHOLD_FAILED_LOGINS = 3
    
    @classmethod
    def get_blocked_ips(cls) -> List[str]:
        """Obtener lista de IPs bloqueadas (puede extenderse para cargar desde DB)"""
        return cls.BLOCKED_IPS
    
    @classmethod
    def add_blocked_ip(cls, ip: str) -> None:
        """Agregar IP a la lista de bloqueadas"""
        if ip not in cls.BLOCKED_IPS:
            cls.BLOCKED_IPS.append(ip)
    
    @classmethod
    def is_trusted_ip(cls, ip: str) -> bool:
        """Verificar si una IP es de confianza"""
        return ip in cls.TRUSTED_IPS
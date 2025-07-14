from fastapi import HTTPException
from typing import Optional, Any, Dict

class ValidationError(HTTPException):
    """Excepción para errores de validación"""
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)

class NotFoundError(HTTPException):
    """Excepción para recursos no encontrados"""
    def __init__(self, detail: str = "Recurso no encontrado", status_code: int = 404):
        super().__init__(status_code=status_code, detail=detail)

class AuthenticationError(HTTPException):
    """Excepción para errores de autenticación"""
    def __init__(self, detail: str = "No autorizado", status_code: int = 401):
        super().__init__(status_code=status_code, detail=detail)

class PermissionError(HTTPException):
    """Excepción para errores de permisos"""
    def __init__(self, detail: str = "Sin permisos suficientes", status_code: int = 403):
        super().__init__(status_code=status_code, detail=detail)

class BusinessLogicError(HTTPException):
    """Excepción para errores de lógica de negocio"""
    def __init__(self, detail: str, status_code: int = 422):
        super().__init__(status_code=status_code, detail=detail)

class ExternalServiceError(HTTPException):
    """Excepción para errores de servicios externos"""
    def __init__(self, detail: str = "Error en servicio externo", status_code: int = 502):
        super().__init__(status_code=status_code, detail=detail)

class RateLimitError(HTTPException):
    """Excepción para límites de tasa excedidos"""
    def __init__(self, detail: str = "Límite de tasa excedido", status_code: int = 429):
        super().__init__(status_code=status_code, detail=detail)
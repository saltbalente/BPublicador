from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.core.security_config import SecurityConfig
from app.api.dependencies import get_current_active_user
from app.schemas.user import User
import os
import json
from collections import defaultdict

router = APIRouter()

# Simulación de almacenamiento en memoria para demo
# En producción, esto debería estar en una base de datos
security_stats = {
    "blocked_requests": 0,
    "suspicious_activities": 0,
    "rate_limited_requests": 0,
    "last_reset": datetime.now()
}

recent_attacks = []
blocked_ips_temp = set()

@router.get("/status", response_model=None)
async def get_security_status(current_user: User = Depends(get_current_active_user)):
    """Obtener estado general de seguridad"""
    try:
        # Leer logs de seguridad recientes
        security_log_path = SecurityConfig.SECURITY_LOG_FILE
        recent_logs = []
        
        if os.path.exists(security_log_path):
            with open(security_log_path, 'r') as f:
                lines = f.readlines()
                # Obtener las últimas 50 líneas
                recent_logs = lines[-50:] if len(lines) > 50 else lines
        
        # Analizar logs para estadísticas
        attack_types = defaultdict(int)
        hourly_stats = defaultdict(int)
        
        for log_line in recent_logs:
            if "injection attempt" in log_line.lower():
                attack_types["SQL Injection"] += 1
            elif "xss attempt" in log_line.lower():
                attack_types["XSS"] += 1
            elif "path traversal" in log_line.lower():
                attack_types["Path Traversal"] += 1
            elif "rate limit" in log_line.lower():
                attack_types["Rate Limiting"] += 1
            elif "blocked ip" in log_line.lower():
                attack_types["IP Blocking"] += 1
            
            # Extraer hora para estadísticas por hora
            try:
                timestamp_str = log_line.split(' - ')[0]
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                hourly_stats[hour_key] += 1
            except:
                pass
        
        return {
            "status": "active",
            "security_middleware": "enabled",
            "total_blocked_requests": security_stats["blocked_requests"],
            "total_suspicious_activities": security_stats["suspicious_activities"],
            "total_rate_limited": security_stats["rate_limited_requests"],
            "attack_types_detected": dict(attack_types),
            "hourly_statistics": dict(hourly_stats),
            "blocked_ips_count": len(SecurityConfig.get_blocked_ips()) + len(blocked_ips_temp),
            "recent_attacks": recent_attacks[-10:],  # Últimos 10 ataques
            "last_reset": security_stats["last_reset"].isoformat(),
            "security_config": {
                "max_requests_per_minute": SecurityConfig.MAX_REQUESTS_PER_MINUTE,
                "max_requests_per_hour": SecurityConfig.MAX_REQUESTS_PER_HOUR,
                "max_content_length": SecurityConfig.MAX_CONTENT_LENGTH,
                "allowed_file_types": SecurityConfig.ALLOWED_FILE_TYPES
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estado de seguridad: {str(e)}"
        )

@router.get("/logs", response_model=None)
async def get_security_logs(
    lines: int = 100,
    current_user: User = Depends(get_current_active_user)
):
    """Obtener logs de seguridad recientes"""
    try:
        security_log_path = SecurityConfig.SECURITY_LOG_FILE
        
        if not os.path.exists(security_log_path):
            return {"logs": [], "message": "No hay logs de seguridad disponibles"}
        
        with open(security_log_path, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        # Formatear logs para mejor legibilidad
        formatted_logs = []
        for line in recent_lines:
            try:
                parts = line.strip().split(' - ')
                if len(parts) >= 4:
                    formatted_logs.append({
                        "timestamp": parts[0],
                        "logger": parts[1],
                        "level": parts[2],
                        "message": ' - '.join(parts[3:])
                    })
                else:
                    formatted_logs.append({
                        "timestamp": "",
                        "logger": "unknown",
                        "level": "INFO",
                        "message": line.strip()
                    })
            except:
                formatted_logs.append({
                    "timestamp": "",
                    "logger": "unknown",
                    "level": "INFO",
                    "message": line.strip()
                })
        
        return {
            "logs": formatted_logs,
            "total_lines": len(all_lines),
            "showing_lines": len(formatted_logs)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al leer logs de seguridad: {str(e)}"
        )

@router.post("/block-ip", response_model=None)
async def block_ip(
    ip_address: str,
    reason: str = "Manual block",
    current_user: User = Depends(get_current_active_user)
):
    """Bloquear una IP específica"""
    try:
        # Validar formato de IP (básico)
        if not ip_address or len(ip_address.split('.')) != 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de IP inválido"
            )
        
        # Agregar a lista de IPs bloqueadas
        SecurityConfig.add_blocked_ip(ip_address)
        blocked_ips_temp.add(ip_address)
        
        # Registrar la acción
        security_stats["blocked_requests"] += 1
        
        return {
            "message": f"IP {ip_address} bloqueada exitosamente",
            "ip": ip_address,
            "reason": reason,
            "blocked_by": current_user.email,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al bloquear IP: {str(e)}"
        )

@router.delete("/unblock-ip", response_model=None)
async def unblock_ip(
    ip_address: str,
    current_user: User = Depends(get_current_active_user)
):
    """Desbloquear una IP específica"""
    try:
        # Remover de listas de IPs bloqueadas
        if ip_address in SecurityConfig.BLOCKED_IPS:
            SecurityConfig.BLOCKED_IPS.remove(ip_address)
        
        if ip_address in blocked_ips_temp:
            blocked_ips_temp.remove(ip_address)
        
        return {
            "message": f"IP {ip_address} desbloqueada exitosamente",
            "ip": ip_address,
            "unblocked_by": current_user.email,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al desbloquear IP: {str(e)}"
        )

@router.get("/blocked-ips", response_model=None)
async def get_blocked_ips(current_user: User = Depends(get_current_active_user)):
    """Obtener lista de IPs bloqueadas"""
    try:
        permanent_blocked = SecurityConfig.get_blocked_ips()
        temporary_blocked = list(blocked_ips_temp)
        
        return {
            "permanent_blocked": permanent_blocked,
            "temporary_blocked": temporary_blocked,
            "total_blocked": len(permanent_blocked) + len(temporary_blocked)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener IPs bloqueadas: {str(e)}"
        )

@router.post("/reset-stats", response_model=None)
async def reset_security_stats(current_user: User = Depends(get_current_active_user)):
    """Resetear estadísticas de seguridad"""
    try:
        global security_stats, recent_attacks
        
        security_stats = {
            "blocked_requests": 0,
            "suspicious_activities": 0,
            "rate_limited_requests": 0,
            "last_reset": datetime.now()
        }
        
        recent_attacks = []
        
        return {
            "message": "Estadísticas de seguridad reseteadas exitosamente",
            "reset_by": current_user.email,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al resetear estadísticas: {str(e)}"
        )

@router.get("/recommendations", response_model=None)
async def get_security_recommendations(current_user: User = Depends(get_current_active_user)):
    """Obtener recomendaciones de seguridad"""
    recommendations = [
        {
            "category": "Configuración",
            "priority": "high",
            "title": "Configurar HTTPS",
            "description": "Asegurar que la aplicación use HTTPS en producción",
            "implemented": False
        },
        {
            "category": "Autenticación",
            "priority": "high",
            "title": "Implementar 2FA",
            "description": "Agregar autenticación de dos factores para usuarios admin",
            "implemented": False
        },
        {
            "category": "Monitoreo",
            "priority": "medium",
            "title": "Alertas automáticas",
            "description": "Configurar alertas por email para actividades sospechosas",
            "implemented": False
        },
        {
            "category": "Base de datos",
            "priority": "high",
            "title": "Backup automático",
            "description": "Implementar backups automáticos de la base de datos",
            "implemented": False
        },
        {
            "category": "Middleware",
            "priority": "high",
            "title": "Middleware de seguridad",
            "description": "Middleware de seguridad implementado y activo",
            "implemented": True
        },
        {
            "category": "Validación",
            "priority": "high",
            "title": "Sanitización de entrada",
            "description": "Sanitización automática de datos de entrada implementada",
            "implemented": True
        }
    ]
    
    return {
        "recommendations": recommendations,
        "total": len(recommendations),
        "implemented": len([r for r in recommendations if r["implemented"]]),
        "pending": len([r for r in recommendations if not r["implemented"]])
    }

# Función auxiliar para registrar ataques (usada por el middleware)
def log_attack(attack_type: str, ip: str, details: str):
    """Registrar un ataque detectado"""
    global recent_attacks, security_stats
    
    attack_info = {
        "type": attack_type,
        "ip": ip,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    
    recent_attacks.append(attack_info)
    security_stats["suspicious_activities"] += 1
    
    # Mantener solo los últimos 100 ataques
    if len(recent_attacks) > 100:
        recent_attacks = recent_attacks[-100:]
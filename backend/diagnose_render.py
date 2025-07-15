#!/usr/bin/env python3
"""
Script de diagnóstico para problemas de Render
Este script ayuda a identificar problemas de configuración
"""

import os
import sys
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def diagnose_environment():
    """Diagnostica las variables de entorno"""
    logger.info("🔍 DIAGNÓSTICO DE VARIABLES DE ENTORNO")
    logger.info("=" * 50)
    
    # Variables críticas para Render
    critical_vars = [
        'PORT',
        'DATABASE_URL',
        'SECRET_KEY',
        'ENVIRONMENT',
        'DEBUG',
        'PYTHON_VERSION'
    ]
    
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            # Ocultar valores sensibles
            if var in ['SECRET_KEY', 'DATABASE_URL']:
                display_value = f"{value[:10]}..." if len(value) > 10 else "***"
            else:
                display_value = value
            logger.info(f"✅ {var}: {display_value}")
        else:
            logger.warning(f"❌ {var}: NO DEFINIDA")
    
    logger.info("=" * 50)

def diagnose_database_url():
    """Diagnostica específicamente la URL de la base de datos"""
    logger.info("🔍 DIAGNÓSTICO DE DATABASE_URL")
    logger.info("=" * 50)
    
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        logger.error("❌ DATABASE_URL no está definida")
        return False
    
    # Verificar si contiene el placeholder problemático
    if '${{' in db_url:
        logger.error(f"❌ DATABASE_URL contiene placeholder sin resolver: {db_url}")
        return False
    
    # Verificar formato básico
    if db_url.startswith(('postgresql://', 'postgres://')):
        logger.info("✅ DATABASE_URL tiene formato PostgreSQL válido")
        return True
    elif db_url.startswith('sqlite://'):
        logger.info("✅ DATABASE_URL tiene formato SQLite válido")
        return True
    else:
        logger.warning(f"⚠️ DATABASE_URL tiene formato desconocido: {db_url[:20]}...")
        return False

def diagnose_port():
    """Diagnostica la configuración del puerto"""
    logger.info("🔍 DIAGNÓSTICO DE PUERTO")
    logger.info("=" * 50)
    
    port = os.getenv('PORT', '10000')
    
    try:
        port_int = int(port)
        if 1024 <= port_int <= 65535:
            logger.info(f"✅ Puerto válido: {port_int}")
            return True
        else:
            logger.warning(f"⚠️ Puerto fuera de rango válido: {port_int}")
            return False
    except ValueError:
        logger.error(f"❌ Puerto no es un número válido: {port}")
        return False

def main():
    """Función principal de diagnóstico"""
    logger.info(f"🚀 INICIANDO DIAGNÓSTICO - {datetime.utcnow().isoformat()}")
    logger.info("=" * 60)
    
    # Ejecutar diagnósticos
    diagnose_environment()
    db_ok = diagnose_database_url()
    port_ok = diagnose_port()
    
    # Resumen final
    logger.info("📊 RESUMEN DEL DIAGNÓSTICO")
    logger.info("=" * 50)
    
    if db_ok and port_ok:
        logger.info("✅ Configuración parece correcta")
        logger.info("💡 Si aún hay problemas, revisar logs de Uvicorn")
        return 0
    else:
        logger.error("❌ Se encontraron problemas de configuración")
        logger.error("💡 Revisar las variables de entorno en Render Dashboard")
        return 1

if __name__ == "__main__":
    sys.exit(main())
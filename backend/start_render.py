#!/usr/bin/env python3
"""
Script de inicio robusto para Render
Este script maneja la inicialización de la aplicación con tolerancia a errores
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def diagnose_environment():
    """Ejecuta diagnóstico de variables de entorno"""
    try:
        logger.info("🔍 Ejecutando diagnóstico de entorno...")
        result = subprocess.run(
            [sys.executable, 'diagnose_render.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.stdout:
            logger.info("📊 Resultado del diagnóstico:")
            for line in result.stdout.strip().split('\n'):
                logger.info(f"  {line}")
        
        return result.returncode == 0
        
    except Exception as e:
        logger.warning(f"⚠️ No se pudo ejecutar diagnóstico: {e}")
        return True  # No es crítico

def check_database_url():
    """Verifica la URL de la base de datos"""
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        logger.error("❌ DATABASE_URL no está definida")
        return False
    
    # Verificar si contiene el placeholder problemático
    if '${{' in db_url:
        logger.error(f"❌ DATABASE_URL contiene placeholder sin resolver: {db_url}")
        logger.error("💡 Esto indica un problema en la configuración de render.yaml")
        return False
    
    logger.info(f"✅ DATABASE_URL configurada correctamente")
    return True

def run_migrations(fail_ok=True):
    """Ejecuta las migraciones de Alembic con manejo de errores"""
    # Verificar DATABASE_URL antes de ejecutar migraciones
    if not check_database_url():
        if fail_ok:
            logger.warning("⚠️ Saltando migraciones debido a problema con DATABASE_URL")
            return True
        return False
    
    try:
        logger.info("🔄 Ejecutando migraciones de base de datos...")
        result = subprocess.run(
            ['alembic', 'upgrade', 'head'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )
        
        if result.returncode == 0:
            logger.info("✅ Migraciones ejecutadas correctamente")
            return True
        else:
            logger.error(f"❌ Error en migraciones: {result.stderr}")
            if fail_ok:
                logger.warning("⚠️ Continuando sin migraciones (fail_ok=True)")
                return True
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Timeout en migraciones")
        if fail_ok:
            logger.warning("⚠️ Continuando sin migraciones (timeout)")
            return True
        return False
    except Exception as e:
        logger.error(f"❌ Error inesperado en migraciones: {e}")
        if fail_ok:
            logger.warning("⚠️ Continuando sin migraciones (error)")
            return True
        return False

def start_uvicorn():
    """Inicia Uvicorn con configuración optimizada para Render"""
    try:
        # Obtener puerto de la variable de entorno
        port = os.getenv('PORT', '10000')
        logger.info(f"📡 Puerto configurado: {port}")
        
        # Verificar si hay problemas con DATABASE_URL
        db_url = os.getenv('DATABASE_URL')
        use_simple = False
        
        if not db_url or '${{' in str(db_url):
            logger.warning("⚠️ Problema con DATABASE_URL, usando versión simple")
            use_simple = True
        
        if use_simple:
            # Usar main_simple.py que no depende de base de datos
            logger.info("🚀 Iniciando con main_simple.py (sin base de datos)...")
            cmd = [
                'uvicorn',
                'main_simple:app',
                '--host', '0.0.0.0',
                '--port', port,
                '--workers', '1',
                '--access-log'
            ]
        else:
            # Usar main.py completo
            logger.info("🚀 Iniciando con main.py (completo)...")
            cmd = [
                'uvicorn',
                'main:app',
                '--host', '0.0.0.0',
                '--port', port,
                '--workers', '1',
                '--access-log'
            ]
        
        logger.info(f"🔧 Ejecutando comando: {' '.join(cmd)}")
        
        # Ejecutar Uvicorn
        result = subprocess.run(cmd, check=True)
        
        if result.returncode == 0:
            logger.info("✅ Aplicación iniciada correctamente")
            return True
        else:
            logger.error(f"❌ Error al iniciar aplicación: código {result.returncode}")
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error al ejecutar Uvicorn: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return False

def main():
    """Función principal de inicio"""
    logger.info("🚀 Iniciando Autopublicador Web en Render")
    logger.info("=" * 50)
    
    # Ejecutar diagnóstico
    diagnose_environment()
    
    # Ejecutar migraciones (opcional)
    if not run_migrations(fail_ok=True):
        logger.error("❌ Fallo crítico en migraciones")
        sys.exit(1)
    
    # Iniciar servidor
    if not start_uvicorn():
        logger.error("❌ Fallo al iniciar servidor")
        sys.exit(1)
    
    logger.info("✅ Aplicación iniciada correctamente")

if __name__ == "__main__":
    main()
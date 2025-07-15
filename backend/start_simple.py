#!/usr/bin/env python3
"""
Script de inicio simplificado para Render
Este script inicia la aplicación sin dependencias de base de datos
"""

import os
import sys
import subprocess
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Función principal de inicio"""
    try:
        logger.info("🚀 Iniciando Autopublicador Web (Versión Simple)")
        
        # Obtener puerto de la variable de entorno
        port = os.getenv('PORT', '10000')
        logger.info(f"📡 Puerto configurado: {port}")
        
        # Configurar comando de Uvicorn
        cmd = [
            'uvicorn',
            'main_simple:app',
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
        else:
            logger.error(f"❌ Error al iniciar aplicación: código {result.returncode}")
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error al ejecutar comando: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
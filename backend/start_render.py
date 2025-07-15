#!/usr/bin/env python3
"""
Script de inicio optimizado para Render
"""

import os
import sys
import subprocess
import time

def run_command(cmd, description, fail_ok=False):
    """Ejecuta un comando con manejo de errores"""
    print(f"🚀 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} falló: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        if not fail_ok:
            print(f"⚠️ Continuando a pesar del error...")
        return False

def main():
    print("🎯 Iniciando aplicación en Render...")
    
    # Verificar variables de entorno críticas
    port = os.getenv('PORT', '10000')
    print(f"📡 Puerto configurado: {port}")
    
    # Ejecutar migraciones (opcional)
    run_command("alembic upgrade head", "Ejecutando migraciones de base de datos", fail_ok=True)
    
    # Iniciar uvicorn con la versión simplificada
    uvicorn_cmd = f"uvicorn main_simple:app --host 0.0.0.0 --port {port} --workers 1 --access-log"
    print(f"🚀 Iniciando servidor: {uvicorn_cmd}")
    
    try:
        # Ejecutar uvicorn directamente sin capturar output para que Render vea los logs
        subprocess.run(uvicorn_cmd, shell=True, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"❌ Error al iniciar servidor: {e}")
        print("🔄 Intentando con main.py original...")
        try:
            fallback_cmd = f"uvicorn main:app --host 0.0.0.0 --port {port} --workers 1"
            subprocess.run(fallback_cmd, shell=True, check=True)
        except Exception as e2:
            print(f"❌ Error también con main.py original: {e2}")
            sys.exit(1)

if __name__ == "__main__":
    main()
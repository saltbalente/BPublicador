#!/usr/bin/env python3
"""
Script específico para resolver problemas de DATABASE_URL en Render.
Este script maneja el caso donde Render no resuelve correctamente las variables de fromDatabase.
"""

import os
import sys
import time
import subprocess

def check_render_environment():
    """
    Verificar si estamos ejecutando en Render y diagnosticar problemas.
    """
    print("🔍 Verificando entorno de Render...")
    
    # Verificar variables de entorno de Render
    render_vars = {
        'RENDER': os.getenv('RENDER'),
        'RENDER_SERVICE_ID': os.getenv('RENDER_SERVICE_ID'),
        'RENDER_SERVICE_NAME': os.getenv('RENDER_SERVICE_NAME'),
        'DATABASE_URL': os.getenv('DATABASE_URL')
    }
    
    print("📊 Variables de entorno detectadas:")
    for key, value in render_vars.items():
        if value:
            if key == 'DATABASE_URL':
                print(f"   {key}: {value[:50]}..." if len(str(value)) > 50 else f"   {key}: {value}")
            else:
                print(f"   {key}: {value}")
        else:
            print(f"   {key}: No configurada")
    
    return render_vars

def fix_database_url():
    """
    Intentar corregir el problema de DATABASE_URL.
    """
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL no está configurada")
        return False
    
    if '${{' in database_url or '${' in database_url:
        print(f"❌ DATABASE_URL contiene variables sin resolver: {database_url}")
        print("💡 Esto indica un problema en la configuración de render.yaml")
        
        # Intentar obtener variables de base de datos directamente
        db_vars = {
            'POSTGRES_HOST': os.getenv('POSTGRES_HOST'),
            'POSTGRES_PORT': os.getenv('POSTGRES_PORT', '5432'),
            'POSTGRES_USER': os.getenv('POSTGRES_USER'),
            'POSTGRES_PASSWORD': os.getenv('POSTGRES_PASSWORD'),
            'POSTGRES_DB': os.getenv('POSTGRES_DB')
        }
        
        print("🔍 Buscando variables de PostgreSQL alternativas:")
        for key, value in db_vars.items():
            if value:
                print(f"   {key}: {'***' if 'PASSWORD' in key else value}")
            else:
                print(f"   {key}: No encontrada")
        
        # Si tenemos todas las variables, construir la URL
        if all(db_vars.values()):
            constructed_url = f"postgresql://{db_vars['POSTGRES_USER']}:{db_vars['POSTGRES_PASSWORD']}@{db_vars['POSTGRES_HOST']}:{db_vars['POSTGRES_PORT']}/{db_vars['POSTGRES_DB']}"
            print(f"✅ URL de base de datos construida manualmente")
            os.environ['DATABASE_URL'] = constructed_url
            return True
        else:
            print("❌ No se pueden obtener todas las variables necesarias")
            return False
    
    print(f"✅ DATABASE_URL parece estar correctamente configurada")
    return True

def wait_for_render_services(max_wait=300):
    """
    Esperar a que los servicios de Render estén completamente inicializados.
    """
    print("⏳ Esperando a que los servicios de Render estén listos...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        if fix_database_url():
            print("✅ Servicios de Render listos")
            return True
        
        print(f"⏳ Esperando... ({int(time.time() - start_time)}s/{max_wait}s)")
        time.sleep(10)
    
    print(f"❌ Timeout después de {max_wait} segundos")
    return False

if __name__ == "__main__":
    print("🚀 Iniciando diagnóstico de Render...")
    
    # Verificar entorno
    render_vars = check_render_environment()
    
    # Si estamos en Render, intentar corregir problemas
    if render_vars.get('RENDER') or render_vars.get('RENDER_SERVICE_ID'):
        print("✅ Ejecutando en Render")
        if wait_for_render_services():
            print("✅ Configuración de base de datos lista")
            sys.exit(0)
        else:
            print("❌ No se pudo configurar la base de datos")
            sys.exit(1)
    else:
        print("ℹ️  No se detectó entorno de Render, continuando...")
        if fix_database_url():
            sys.exit(0)
        else:
            sys.exit(1)
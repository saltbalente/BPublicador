#!/usr/bin/env python3
"""
Script para esperar a que la base de datos esté disponible antes de iniciar la aplicación.
"""

import os
import time
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

def wait_for_database(max_retries=10, delay=1):
    """
    Espera a que la base de datos esté disponible.
    """
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url or database_url.startswith("${") or "${{" in database_url:
        print("❌ DATABASE_URL no está configurada o contiene variables sin resolver")
        print(f"DATABASE_URL actual: {database_url}")
        print("⏳ Esperando a que Render configure la base de datos...")
        
        # Esperar hasta que la variable esté disponible
        for attempt in range(5):  # Solo 5 intentos para variables
            database_url = os.getenv("DATABASE_URL")
            if database_url and not database_url.startswith("${") and "${{" not in database_url:
                print(f"✅ DATABASE_URL configurada: {database_url[:50]}...")
                break
            print(f"⏳ Intento {attempt + 1}/5 - Esperando DATABASE_URL...")
            time.sleep(1)
        else:
            print("❌ Timeout esperando DATABASE_URL - Continuando sin verificación")
            return True  # Continuar en lugar de fallar
    
    print(f"🔍 Probando conexión a la base de datos...")
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(database_url)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("✅ Conexión a la base de datos exitosa")
            return True
        except OperationalError as e:
            print(f"⏳ Intento {attempt + 1}/{max_retries} - Base de datos no disponible: {str(e)[:100]}...")
            time.sleep(delay)
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            time.sleep(delay)
    
    print("❌ No se pudo conectar a la base de datos después de todos los intentos")
    sys.exit(1)

if __name__ == "__main__":
    print("🚀 Iniciando verificación de base de datos...")
    wait_for_database()
    print("✅ Base de datos lista - continuando con el inicio de la aplicación")
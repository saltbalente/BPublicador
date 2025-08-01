#!/usr/bin/env python3
"""
Script de inicialización para Vercel
Configura la base de datos y datos iniciales en el primer despliegue
"""

import os
import sys
import sqlite3
from pathlib import Path

# Agregar el directorio backend al path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def init_database():
    """Inicializa la base de datos para Vercel (PostgreSQL o SQLite)"""
    try:
        # Verificar si estamos usando PostgreSQL
        database_url = os.getenv("DATABASE_URL", "sqlite:///./autopublicador.db")
        
        if database_url.startswith(("postgresql://", "postgres://")):
            print("🐘 Detectado PostgreSQL, ejecutando migración...")
            return init_postgresql()
        else:
            print("📁 Usando SQLite para desarrollo...")
            return init_sqlite()
    
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        return False

def init_postgresql():
    """Inicializa PostgreSQL usando SQLAlchemy"""
    try:
        # Ejecutar script de migración
        import subprocess
        result = subprocess.run([
            sys.executable, 
            str(backend_dir / "migrate_to_postgresql.py")
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ PostgreSQL inicializado correctamente")
            return True
        else:
            print(f"❌ Error en migración PostgreSQL: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando migración PostgreSQL: {e}")
        return False

def init_sqlite():
    """Inicializa la base de datos SQLite para desarrollo local"""
    try:
        # Crear directorio de base de datos si no existe
        db_path = backend_dir / "autopublicador.db"
        
        # Conectar a SQLite
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Crear tabla de usuarios si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_superuser BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear tabla de contenido si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(500) NOT NULL,
                content TEXT NOT NULL,
                keywords TEXT,
                meta_description VARCHAR(500),
                status VARCHAR(50) DEFAULT 'draft',
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Crear tabla de keywords si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword VARCHAR(255) NOT NULL,
                search_volume INTEGER DEFAULT 0,
                competition VARCHAR(50) DEFAULT 'medium',
                difficulty INTEGER DEFAULT 50,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Crear tabla de landing pages si no existe
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS landing_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(500) NOT NULL,
                content TEXT NOT NULL,
                theme VARCHAR(100) DEFAULT 'modern',
                status VARCHAR(50) DEFAULT 'active',
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Verificar si ya existe el usuario admin
        cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@autopublicador.com",))
        if not cursor.fetchone():
            # Crear usuario admin por defecto
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            hashed_password = pwd_context.hash("admin123")
            
            cursor.execute("""
                INSERT INTO users (email, hashed_password, is_active, is_superuser)
                VALUES (?, ?, 1, 1)
            """, ("admin@autopublicador.com", hashed_password))
            
            print("✅ Usuario admin creado: admin@autopublicador.com / admin123")
        
        conn.commit()
        conn.close()
        
        print("✅ Base de datos inicializada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        return False

def create_directories():
    """Crea directorios necesarios"""
    try:
        # Crear directorio de imágenes
        images_dir = backend_dir / "storage" / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear directorio de templates
        templates_dir = backend_dir / "app" / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear directorio de static
        static_dir = backend_dir / "static"
        static_dir.mkdir(parents=True, exist_ok=True)
        
        print("✅ Directorios creados correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error creando directorios: {e}")
        return False

def initialize_for_vercel():
    """Función principal de inicialización para Vercel"""
    print("🚀 Inicializando Autopublicador para Vercel...")
    
    # Crear directorios
    create_directories()
    
    # Inicializar base de datos
    init_database()
    
    print("✅ Inicialización completada")

if __name__ == "__main__":
    initialize_for_vercel()
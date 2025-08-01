#!/usr/bin/env python3
"""
Script de migración para PostgreSQL en producción
Ejecuta las migraciones necesarias y configura la base de datos
"""

import os
import sys
from pathlib import Path

# Agregar el directorio backend al path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def check_postgresql_connection():
    """Verifica la conexión a PostgreSQL"""
    try:
        from sqlalchemy import create_engine, text
        from app.core.config import settings
        
        print("🔍 Verificando conexión a PostgreSQL...")
        
        # Verificar que DATABASE_URL esté configurada
        if not settings.DATABASE_URL or settings.DATABASE_URL.startswith("sqlite"):
            print("❌ DATABASE_URL no está configurada para PostgreSQL")
            print(f"   Actual: {settings.DATABASE_URL}")
            return False
        
        # Crear engine y probar conexión
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Conectado a PostgreSQL: {version[:50]}...")
            
        return True
        
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        return False

def run_migrations():
    """Ejecuta las migraciones de Alembic"""
    try:
        print("🔄 Ejecutando migraciones de base de datos...")
        
        # Importar después de verificar la conexión
        from alembic.config import Config
        from alembic import command
        
        # Configurar Alembic
        alembic_cfg = Config("alembic.ini")
        
        # Ejecutar migraciones
        command.upgrade(alembic_cfg, "head")
        
        print("✅ Migraciones ejecutadas correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error ejecutando migraciones: {e}")
        return False

def create_tables_manually():
    """Crea las tablas manualmente si Alembic falla"""
    try:
        print("🔧 Creando tablas manualmente...")
        
        from sqlalchemy import create_engine
        from app.core.config import settings
        from app.core.database import Base
        
        # Importar todos los modelos para que estén registrados
        from app.models import User, Content, Keyword, LandingPage, SchedulerConfig
        
        engine = create_engine(settings.DATABASE_URL)
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        
        print("✅ Tablas creadas correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False

def create_admin_user():
    """Crea el usuario administrador por defecto"""
    try:
        print("👤 Verificando usuario administrador...")
        
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.core.config import settings
        from app.models.user import User
        from app.core.security import get_password_hash
        
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        with SessionLocal() as db:
            # Verificar si ya existe el usuario admin
            admin_user = db.query(User).filter(User.email == "admin@autopublicador.com").first()
            
            if not admin_user:
                # Crear usuario admin
                hashed_password = get_password_hash("admin123")
                admin_user = User(
                    email="admin@autopublicador.com",
                    hashed_password=hashed_password,
                    is_active=True,
                    is_superuser=True
                )
                db.add(admin_user)
                db.commit()
                
                print("✅ Usuario administrador creado:")
                print("   📧 Email: admin@autopublicador.com")
                print("   🔑 Password: admin123")
            else:
                print("✅ Usuario administrador ya existe")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando usuario administrador: {e}")
        return False

def verify_scheduler_table():
    """Verifica que la tabla scheduler_configs exista"""
    try:
        print("📅 Verificando tabla del scheduler...")
        
        from sqlalchemy import create_engine, inspect
        from app.core.config import settings
        
        engine = create_engine(settings.DATABASE_URL)
        inspector = inspect(engine)
        
        tables = inspector.get_table_names()
        
        if "scheduler_configs" in tables:
            print("✅ Tabla scheduler_configs existe")
        else:
            print("⚠️ Tabla scheduler_configs no existe, creándola...")
            
            # Crear tabla manualmente
            from app.models.scheduler_config import SchedulerConfig
            from app.core.database import Base
            
            SchedulerConfig.__table__.create(bind=engine, checkfirst=True)
            print("✅ Tabla scheduler_configs creada")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando tabla del scheduler: {e}")
        return False

def main():
    """Función principal de migración"""
    print("🚀 Iniciando migración a PostgreSQL...")
    print("=" * 50)
    
    # Paso 1: Verificar conexión
    if not check_postgresql_connection():
        print("\n❌ No se puede conectar a PostgreSQL")
        print("💡 Asegúrate de que DATABASE_URL esté configurada correctamente")
        return False
    
    # Paso 2: Intentar migraciones con Alembic
    migration_success = run_migrations()
    
    # Paso 3: Si Alembic falla, crear tablas manualmente
    if not migration_success:
        print("\n⚠️ Alembic falló, creando tablas manualmente...")
        if not create_tables_manually():
            return False
    
    # Paso 4: Verificar tabla del scheduler
    if not verify_scheduler_table():
        return False
    
    # Paso 5: Crear usuario administrador
    if not create_admin_user():
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ¡Migración completada exitosamente!")
    print("\n📋 Resumen:")
    print("   ✅ Conexión a PostgreSQL verificada")
    print("   ✅ Tablas de base de datos creadas")
    print("   ✅ Tabla del scheduler configurada")
    print("   ✅ Usuario administrador disponible")
    print("\n🌐 Tu aplicación está lista para producción en Vercel!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
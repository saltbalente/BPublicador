#!/usr/bin/env python3
"""
Script de inicialización de la base de datos
Crea las tablas necesarias y datos iniciales para la plataforma
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from passlib.context import CryptContext
from datetime import datetime

from app.core.database import async_engine, get_async_db
from app.models import Base, User, Keyword, Content
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


async def create_tables():
    """Crear todas las tablas de la base de datos"""
    print("🔧 Creando tablas de la base de datos...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tablas creadas exitosamente")


async def create_admin_user(db: AsyncSession):
    """Crear usuario administrador por defecto"""
    print("👤 Creando usuario administrador...")
    
    # Verificar si ya existe un admin
    result = await db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": "admin@autopublicador.com"}
    )
    existing_user = result.fetchone()
    
    if existing_user:
        print("⚠️  Usuario administrador ya existe")
        return
    
    admin_user = User(
        email="admin@autopublicador.com",
        username="admin",
        hashed_password=hash_password("admin123"),
        is_active=True,
        is_admin=True,
        daily_limit=100,
        created_at=datetime.utcnow()
    )
    
    db.add(admin_user)
    await db.commit()
    print("✅ Usuario administrador creado:")
    print("   📧 Email: admin@autopublicador.com")
    print("   🔑 Password: admin123")
    print("   ⚠️  CAMBIAR PASSWORD EN PRODUCCIÓN")


async def create_sample_keywords(db: AsyncSession):
    """Crear keywords de ejemplo para brujería y esoterismo"""
    print("🔮 Creando keywords de ejemplo...")
    
    sample_keywords = [
        # Tarot
        {"keyword": "tarot del amor gratis", "category": "tarot", "priority": 5, "search_volume": 8900},
        {"keyword": "como leer las cartas del tarot", "category": "tarot", "priority": 4, "search_volume": 5400},
        {"keyword": "significado cartas tarot", "category": "tarot", "priority": 4, "search_volume": 6700},
        {"keyword": "tarot si o no", "category": "tarot", "priority": 3, "search_volume": 4200},
        {"keyword": "tirada de tarot celta", "category": "tarot", "priority": 3, "search_volume": 2800},
        
        # Hechizos
        {"keyword": "hechizos de amor efectivos", "category": "hechizos", "priority": 5, "search_volume": 7200},
        {"keyword": "hechizos para el dinero", "category": "hechizos", "priority": 4, "search_volume": 5800},
        {"keyword": "hechizos de protección", "category": "hechizos", "priority": 4, "search_volume": 4100},
        {"keyword": "como hacer un hechizo", "category": "hechizos", "priority": 3, "search_volume": 3600},
        {"keyword": "hechizos con velas", "category": "hechizos", "priority": 3, "search_volume": 2900},
        
        # Rituales
        {"keyword": "rituales de luna llena", "category": "rituales", "priority": 4, "search_volume": 4800},
        {"keyword": "ritual de limpieza energética", "category": "rituales", "priority": 4, "search_volume": 3200},
        {"keyword": "rituales de abundancia", "category": "rituales", "priority": 3, "search_volume": 2700},
        {"keyword": "ritual para atraer el amor", "category": "rituales", "priority": 3, "search_volume": 2400},
        {"keyword": "rituales de año nuevo", "category": "rituales", "priority": 2, "search_volume": 1800},
        
        # Astrología
        {"keyword": "horoscopo diario", "category": "astrologia", "priority": 5, "search_volume": 12000},
        {"keyword": "compatibilidad de signos", "category": "astrologia", "priority": 4, "search_volume": 6800},
        {"keyword": "carta astral gratis", "category": "astrologia", "priority": 4, "search_volume": 5200},
        {"keyword": "significado de los signos", "category": "astrologia", "priority": 3, "search_volume": 3900},
        {"keyword": "luna nueva en cada signo", "category": "astrologia", "priority": 3, "search_volume": 2100},
        
        # Cristales
        {"keyword": "propiedades de los cristales", "category": "cristales", "priority": 4, "search_volume": 4600},
        {"keyword": "como limpiar cristales", "category": "cristales", "priority": 3, "search_volume": 3100},
        {"keyword": "cristales para el amor", "category": "cristales", "priority": 3, "search_volume": 2800},
        {"keyword": "cuarzo rosa propiedades", "category": "cristales", "priority": 3, "search_volume": 2400},
        {"keyword": "amatista significado", "category": "cristales", "priority": 2, "search_volume": 1900},
        
        # Numerología
        {"keyword": "numerologia del nombre", "category": "numerologia", "priority": 4, "search_volume": 3800},
        {"keyword": "numero de la suerte", "category": "numerologia", "priority": 3, "search_volume": 2900},
        {"keyword": "significado de los numeros", "category": "numerologia", "priority": 3, "search_volume": 2600},
        {"keyword": "numerologia pareja", "category": "numerologia", "priority": 2, "search_volume": 1700},
        {"keyword": "numero del destino", "category": "numerologia", "priority": 2, "search_volume": 1400},
        
        # Chakras
        {"keyword": "como abrir los chakras", "category": "chakras", "priority": 4, "search_volume": 3400},
        {"keyword": "chakras bloqueados sintomas", "category": "chakras", "priority": 3, "search_volume": 2200},
        {"keyword": "meditacion para chakras", "category": "chakras", "priority": 3, "search_volume": 1900},
        {"keyword": "colores de los chakras", "category": "chakras", "priority": 2, "search_volume": 1600},
        {"keyword": "chakra del corazon", "category": "chakras", "priority": 2, "search_volume": 1300},
    ]
    
    # Verificar si ya existen keywords
    result = await db.execute(text("SELECT COUNT(*) as count FROM keywords"))
    count = result.fetchone().count
    
    if count > 0:
        print(f"⚠️  Ya existen {count} keywords en la base de datos")
        return
    
    # Crear keywords
    for kw_data in sample_keywords:
        # Convertir priority de número a enum
        priority_map = {5: "high", 4: "high", 3: "medium", 2: "low", 1: "low"}
        priority_enum = priority_map.get(kw_data["priority"], "medium")
        
        keyword = Keyword(
            keyword=kw_data["keyword"],
            category=kw_data["category"],
            priority=priority_enum,
            search_volume=kw_data["search_volume"],
            status="pending",
            created_at=datetime.utcnow()
        )
        db.add(keyword)
    
    await db.commit()
    print(f"✅ {len(sample_keywords)} keywords de ejemplo creadas")


async def create_sample_content(db: AsyncSession):
    """Crear contenido de ejemplo"""
    print("📝 Creando contenido de ejemplo...")
    
    # Verificar si ya existe contenido
    result = await db.execute(text("SELECT COUNT(*) as count FROM content"))
    count = result.fetchone().count
    
    if count > 0:
        print(f"⚠️  Ya existe {count} contenido en la base de datos")
        return
    
    # Obtener el primer usuario y keyword
    user_result = await db.execute(text("SELECT id FROM users LIMIT 1"))
    user_id = user_result.fetchone().id
    
    keyword_result = await db.execute(text("SELECT id FROM keywords LIMIT 1"))
    keyword_id = keyword_result.fetchone().id
    
    title = "Guía Completa del Tarot del Amor: Descubre tu Destino Romántico"
    slug = title.lower().replace(" ", "-").replace(":", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    
    sample_content = Content(
        title=title,
        slug=slug,
        content="""# Guía Completa del Tarot del Amor: Descubre tu Destino Romántico

El tarot del amor es una de las consultas más populares en el mundo esotérico. Miles de personas buscan respuestas sobre su vida sentimental a través de las cartas del tarot.

## ¿Qué es el Tarot del Amor?

El tarot del amor es una tirada específica de cartas diseñada para obtener información sobre temas románticos y sentimentales. Esta práctica milenaria nos ayuda a comprender mejor nuestras relaciones actuales y futuras.

## Tipos de Tiradas de Amor

### 1. Tirada de 3 Cartas
- **Pasado**: Influencias previas en tu vida amorosa
- **Presente**: Situación actual de tu corazón
- **Futuro**: Lo que te depara el destino en el amor

### 2. Tirada de la Cruz Celta del Amor
Una tirada más compleja que analiza todos los aspectos de tu vida sentimental.

## Cartas Más Importantes en el Amor

- **Los Enamorados**: Decisiones importantes en el amor
- **La Emperatriz**: Fertilidad y abundancia emocional
- **El Sol**: Felicidad y éxito en las relaciones

## Consejos para una Lectura Efectiva

1. **Mantén una mente abierta**: Las cartas reflejan energías, no destinos fijos
2. **Haz preguntas específicas**: Evita preguntas vagas como "¿encontraré el amor?"
3. **Confía en tu intuición**: Tu primer instinto suele ser el correcto

## Conclusión

El tarot del amor es una herramienta poderosa para el autoconocimiento y la reflexión sobre nuestras relaciones. Recuerda que las cartas nos guían, pero las decisiones siempre son nuestras.
""",
        meta_description="Descubre todo sobre el tarot del amor: tipos de tiradas, cartas importantes y consejos para lecturas efectivas. Guía completa para principiantes.",
        content_type="post",
        word_count=350,
        status="published",
        keyword_id=keyword_id,
        user_id=user_id,
        created_at=datetime.utcnow(),
        published_at=datetime.utcnow()
    )
    
    db.add(sample_content)
    await db.commit()
    print("✅ Contenido de ejemplo creado")


async def init_db():
    """Función principal de inicialización"""
    print("🚀 Iniciando configuración de la base de datos...")
    print(f"📊 Base de datos: {settings.DATABASE_URL}")
    
    try:
        # Crear tablas
        await create_tables()
        
        # Obtener sesión de base de datos
        async for db in get_async_db():
            # Crear datos iniciales
            await create_admin_user(db)
            await create_sample_keywords(db)
            await create_sample_content(db)
            break
        
        print("\n🎉 ¡Inicialización completada exitosamente!")
        print("\n📋 Resumen:")
        print("   ✅ Tablas creadas")
        print("   ✅ Usuario administrador creado")
        print("   ✅ Keywords de ejemplo agregadas")
        print("   ✅ Contenido de ejemplo creado")
        print("\n🌐 Puedes acceder a:")
        print(f"   🖥️  Frontend: http://localhost:3000")
        print(f"   🔌 API: http://localhost:8000")
        print(f"   📚 Docs: http://localhost:8000/docs")
        print("\n🔐 Credenciales de administrador:")
        print("   📧 Email: admin@autopublicador.com")
        print("   🔑 Password: admin123")
        
    except Exception as e:
        print(f"❌ Error durante la inicialización: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_db())
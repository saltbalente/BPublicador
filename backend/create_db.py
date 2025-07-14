#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.user import User
from app.models.keyword import Keyword
from app.models.content import Content
from app.models.category import Category
from app.models.tag import Tag
from app.models.seo_schema import SEOSchema
from app.models.content_image import ContentImage
from app.models.image_config import ImageConfig
from app.services.auth import get_password_hash
from datetime import datetime

# Database URL
DATABASE_URL = "sqlite:///./autopublicador.db"

def create_database():
    print("Creando base de datos...")
    
    # Create engine
    engine = create_engine(DATABASE_URL, echo=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas exitosamente.")
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@autopublicador.com",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        print("Usuario admin creado.")
        
        # Create sample category
        category_name = "Tarot y Esoterismo"
        category_slug = category_name.lower().replace(" ", "-").replace("y", "y")
        category = Category(
            name=category_name,
            slug=category_slug,
            description="Contenido relacionado con tarot, astrología y temas esotéricos"
        )
        db.add(category)
        db.commit()
        print("Categoría creada.")
        
        # Create sample tags
        tag_data = [
            {"name": "tarot", "description": "Lecturas de tarot"},
            {"name": "amor", "description": "Temas de amor y relaciones"},
            {"name": "futuro", "description": "Predicciones del futuro"}
        ]
        tags = []
        for tag_info in tag_data:
            tag_slug = tag_info["name"].lower().replace(" ", "-")
            tag = Tag(
                name=tag_info["name"],
                slug=tag_slug,
                description=tag_info["description"]
            )
            tags.append(tag)
            db.add(tag)
        db.commit()
        print("Tags creados.")
        
        # Create sample keywords
        keywords = [
            Keyword(
                keyword="tarot del amor",
                status="pending",
                priority="high",
                search_volume=5000,
                difficulty=0.6,
                category="Tarot",
                notes="Keyword principal para contenido de tarot del amor"
            ),
            Keyword(
                keyword="lectura de cartas",
                status="pending",
                priority="medium",
                search_volume=3000,
                difficulty=0.5,
                category="Tarot",
                notes="Keyword secundaria para lecturas"
            )
        ]
        for keyword in keywords:
            db.add(keyword)
        db.commit()
        print("Keywords creadas.")
        
        # Create sample content
        title = "Guía Completa del Tarot del Amor: Descubre tu Destino Romántico"
        slug = title.lower().replace(" ", "-").replace(":", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        
        content = Content(
            title=title,
            slug=slug,
            content="""# Guía Completa del Tarot del Amor: Descubre tu Destino Romántico

El tarot del amor es una de las consultas más populares en el mundo esotérico. A través de las cartas, podemos obtener insights profundos sobre nuestras relaciones actuales, futuras y los desafíos que podemos enfrentar en el amor.

## ¿Qué es el Tarot del Amor?

El tarot del amor es una especialización dentro de la lectura de cartas que se enfoca específicamente en temas románticos y de relaciones. Las cartas nos ayudan a entender:

- El estado actual de nuestras relaciones
- Posibles desarrollos futuros en el amor
- Obstáculos y oportunidades en el romance
- Consejos para mejorar nuestras conexiones emocionales

## Cartas Principales en el Tarot del Amor

### Los Enamorados
Esta carta representa la unión, las decisiones importantes en el amor y la armonía en las relaciones.

### La Emperatriz
Símboliza la feminidad, la fertilidad y el amor maternal.

### El Emperador
Representa la masculinidad, la protección y la estabilidad en las relaciones.

## Cómo Realizar una Lectura de Tarot del Amor

1. **Preparación**: Encuentra un espacio tranquilo y concentra tu mente en tu pregunta sobre el amor.
2. **Formulación de la pregunta**: Sé específico sobre lo que quieres saber.
3. **Selección de cartas**: Baraja las cartas mientras piensas en tu pregunta.
4. **Interpretación**: Analiza las cartas en el contexto de tu situación amorosa.

## Tiradas Populares para el Amor

### Tirada de 3 Cartas
- Carta 1: Pasado amoroso
- Carta 2: Presente en el amor
- Carta 3: Futuro romántico

### Tirada de la Cruz Celta del Amor
Una tirada más compleja que explora múltiples aspectos de tu vida amorosa.

## Consejos para Principiantes

- Mantén una mente abierta durante la lectura
- No tomes las predicciones como absolutas
- Usa el tarot como una herramienta de reflexión
- Practica regularmente para mejorar tu intuición

## Conclusión

El tarot del amor puede ser una herramienta poderosa para entender mejor nuestras relaciones y emociones. Recuerda que las cartas ofrecen orientación, pero las decisiones finales siempre están en tus manos.

¿Estás listo para descubrir lo que el tarot tiene que decir sobre tu vida amorosa?""",
            excerpt="Descubre los secretos del tarot del amor y aprende a interpretar las cartas para obtener insights sobre tu vida romántica y relaciones futuras.",
            status="published",
            user_id=admin_user.id,
            category_id=category.id,
            keyword_id=keywords[0].id,
            meta_title="Tarot del Amor: Guía Completa para Descubrir tu Destino Romántico",
            meta_description="Aprende todo sobre el tarot del amor con nuestra guía completa. Descubre cómo interpretar las cartas y conocer tu futuro romántico.",
            focus_keyword="tarot del amor",
            published_at=datetime.utcnow()
        )
        db.add(content)
        db.commit()
        print("Contenido de ejemplo creado.")
        
        # Create SEO Schema
        seo_schema = SEOSchema(
            name="Artículo de Tarot",
            schema_type="Article",
            properties={
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": title,
                "description": "Guía completa sobre el tarot del amor",
                "author": {
                    "@type": "Person",
                    "name": "Admin"
                },
                "datePublished": datetime.utcnow().isoformat(),
                "mainEntityOfPage": {
                    "@type": "WebPage",
                    "@id": f"https://autopublicador.com/{slug}"
                }
            }
        )
        db.add(seo_schema)
        db.commit()
        print("Schema SEO creado.")
        
        # Create Image Config
        image_config = ImageConfig(
            name="Configuración por defecto",
            max_width=1200,
            max_height=800,
            quality=85,
            format="JPEG",
            watermark_enabled=True,
            watermark_text="Autopublicador",
            watermark_position="bottom-right",
            watermark_opacity=0.7
        )
        db.add(image_config)
        db.commit()
        print("Configuración de imagen creada.")
        
        print("\n¡Base de datos creada exitosamente con datos de ejemplo!")
        print("Credenciales de admin:")
        print("  Usuario: admin")
        print("  Email: admin@autopublicador.com")
        print("  Contraseña: admin123")
        
    except Exception as e:
        print(f"Error al crear datos de ejemplo: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_database()
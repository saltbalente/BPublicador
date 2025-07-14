#!/usr/bin/env python3
"""
Script para crear temas esotéricos predefinidos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import engine
from app.models.theme import Theme

def create_esoteric_themes():
    """Crear los dos temas esotéricos"""
    
    # CSS para el tema Místico Lunar
    mystic_lunar_css = """
/* Tema Místico Lunar */
:root {
    --primary-color: #2d1b69;
    --secondary-color: #4a148c;
    --accent-color: #7b1fa2;
    --text-color: #e8eaf6;
    --bg-color: #0a0a0a;
    --card-bg: rgba(45, 27, 105, 0.3);
    --gradient-primary: linear-gradient(135deg, #2d1b69 0%, #4a148c 50%, #7b1fa2 100%);
    --gradient-secondary: linear-gradient(45deg, #1a237e 0%, #283593 100%);
    --shadow-mystical: 0 8px 32px rgba(123, 31, 162, 0.3);
    --border-mystical: 1px solid rgba(232, 234, 246, 0.2);
}

body {
    background: var(--bg-color);
    background-image: 
        radial-gradient(circle at 20% 80%, rgba(123, 31, 162, 0.3) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(45, 27, 105, 0.3) 0%, transparent 50%),
        radial-gradient(circle at 40% 40%, rgba(74, 20, 140, 0.2) 0%, transparent 50%);
    color: var(--text-color);
    font-family: 'Cinzel', 'Georgia', serif;
    line-height: 1.6;
    overflow-x: hidden;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Header místico */
header {
    background: var(--gradient-primary);
    padding: 2rem 0;
    position: relative;
    overflow: hidden;
}

header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="stars" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="10" cy="10" r="1" fill="%23e8eaf6" opacity="0.3"/></pattern></defs><rect width="100" height="100" fill="url(%23stars)"/></svg>') repeat;
    opacity: 0.5;
}

h1, h2, h3 {
    position: relative;
    z-index: 2;
    text-align: center;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    margin-bottom: 1rem;
}

h1 {
    font-size: 3.5rem;
    background: linear-gradient(45deg, #e8eaf6, #c5cae9, #9c27b0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: mysticalGlow 3s ease-in-out infinite alternate;
}

@keyframes mysticalGlow {
    0% { filter: brightness(1) drop-shadow(0 0 5px rgba(156, 39, 176, 0.5)); }
    100% { filter: brightness(1.2) drop-shadow(0 0 20px rgba(156, 39, 176, 0.8)); }
}

/* Secciones con efecto cristal */
section {
    background: var(--card-bg);
    backdrop-filter: blur(10px);
    border: var(--border-mystical);
    border-radius: 20px;
    padding: 2rem;
    margin: 2rem 0;
    box-shadow: var(--shadow-mystical);
    position: relative;
    overflow: hidden;
}

section::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(232, 234, 246, 0.1), transparent);
    animation: shimmer 3s infinite;
}

@keyframes shimmer {
    0% { left: -100%; }
    100% { left: 100%; }
}

/* Botones místicos */
.btn, button {
    background: var(--gradient-secondary);
    color: var(--text-color);
    border: none;
    padding: 12px 30px;
    border-radius: 25px;
    font-family: inherit;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(123, 31, 162, 0.3);
    position: relative;
    overflow: hidden;
}

.btn:hover, button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(123, 31, 162, 0.5);
    background: var(--gradient-primary);
}

/* Formularios místicos */
input, textarea {
    background: rgba(45, 27, 105, 0.2);
    border: var(--border-mystical);
    border-radius: 10px;
    padding: 12px 16px;
    color: var(--text-color);
    font-family: inherit;
    width: 100%;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
}

input:focus, textarea:focus {
    outline: none;
    border-color: var(--accent-color);
    box-shadow: 0 0 20px rgba(123, 31, 162, 0.3);
    background: rgba(45, 27, 105, 0.4);
}

/* Efectos de partículas */
.mystical-particles {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: -1;
}

/* Responsive */
@media (max-width: 768px) {
    h1 { font-size: 2.5rem; }
    section { padding: 1.5rem; margin: 1rem 0; }
    .container { padding: 0 15px; }
}
"""

    # CSS para el tema Alquimia Dorada
    golden_alchemy_css = """
/* Tema Alquimia Dorada */
:root {
    --primary-color: #bf9000;
    --secondary-color: #ff8f00;
    --accent-color: #ffc107;
    --text-color: #2e2e2e;
    --bg-color: #1a1a1a;
    --card-bg: rgba(191, 144, 0, 0.1);
    --gradient-primary: linear-gradient(135deg, #bf9000 0%, #ff8f00 50%, #ffc107 100%);
    --gradient-secondary: linear-gradient(45deg, #8d6e63 0%, #a1887f 100%);
    --shadow-alchemical: 0 8px 32px rgba(255, 193, 7, 0.3);
    --border-alchemical: 1px solid rgba(255, 193, 7, 0.3);
}

body {
    background: var(--bg-color);
    background-image: 
        radial-gradient(circle at 25% 25%, rgba(191, 144, 0, 0.2) 0%, transparent 50%),
        radial-gradient(circle at 75% 75%, rgba(255, 143, 0, 0.2) 0%, transparent 50%),
        linear-gradient(45deg, rgba(255, 193, 7, 0.05) 0%, transparent 100%);
    color: var(--text-color);
    font-family: 'Crimson Text', 'Times New Roman', serif;
    line-height: 1.7;
    position: relative;
}

body::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="alchemy" x="0" y="0" width="50" height="50" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="2" fill="%23ffc107" opacity="0.1"/><path d="M15,25 L35,25 M25,15 L25,35 M20,20 L30,30 M30,20 L20,30" stroke="%23bf9000" stroke-width="0.5" opacity="0.2"/></pattern></defs><rect width="100" height="100" fill="url(%23alchemy)"/></svg>') repeat;
    z-index: -2;
    opacity: 0.3;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
    position: relative;
}

/* Header alquímico */
header {
    background: var(--gradient-primary);
    padding: 3rem 0;
    position: relative;
    overflow: hidden;
    border-bottom: 3px solid var(--accent-color);
}

header::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"><defs><pattern id="hexagon" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse"><polygon points="20,5 35,15 35,25 20,35 5,25 5,15" fill="none" stroke="%23000" stroke-width="0.5" opacity="0.2"/></pattern></defs><rect width="200" height="200" fill="url(%23hexagon)"/></svg>') repeat;
    opacity: 0.3;
}

h1, h2, h3 {
    position: relative;
    z-index: 2;
    text-align: center;
    color: #1a1a1a;
    text-shadow: 2px 2px 4px rgba(255, 193, 7, 0.3);
    margin-bottom: 1.5rem;
}

h1 {
    font-size: 4rem;
    font-weight: 700;
    background: linear-gradient(45deg, #8d6e63, #bf9000, #ff8f00);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: alchemicalPulse 4s ease-in-out infinite;
    position: relative;
}

h1::before {
    content: '⚗️';
    position: absolute;
    left: -60px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 2rem;
    animation: rotate 10s linear infinite;
}

h1::after {
    content: '🔮';
    position: absolute;
    right: -60px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 2rem;
    animation: rotate 10s linear infinite reverse;
}

@keyframes alchemicalPulse {
    0%, 100% { filter: brightness(1) drop-shadow(0 0 10px rgba(191, 144, 0, 0.5)); }
    50% { filter: brightness(1.3) drop-shadow(0 0 30px rgba(255, 193, 7, 0.8)); }
}

@keyframes rotate {
    from { transform: translateY(-50%) rotate(0deg); }
    to { transform: translateY(-50%) rotate(360deg); }
}

/* Secciones con pergamino */
section {
    background: linear-gradient(145deg, rgba(255, 248, 225, 0.95), rgba(255, 243, 205, 0.9));
    border: 2px solid var(--accent-color);
    border-radius: 15px;
    padding: 2.5rem;
    margin: 2.5rem 0;
    box-shadow: var(--shadow-alchemical), inset 0 1px 0 rgba(255, 255, 255, 0.2);
    position: relative;
    color: var(--text-color);
}

section::before {
    content: '';
    position: absolute;
    top: 10px;
    left: 10px;
    right: 10px;
    bottom: 10px;
    border: 1px solid rgba(191, 144, 0, 0.3);
    border-radius: 10px;
    pointer-events: none;
}

/* Botones alquímicos */
.btn, button {
    background: var(--gradient-secondary);
    color: #fff;
    border: 2px solid var(--accent-color);
    padding: 15px 35px;
    border-radius: 30px;
    font-family: inherit;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.4s ease;
    box-shadow: 0 6px 20px rgba(191, 144, 0, 0.3);
    position: relative;
    overflow: hidden;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.btn::before, button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    transition: left 0.5s;
}

.btn:hover::before, button:hover::before {
    left: 100%;
}

.btn:hover, button:hover {
    transform: translateY(-3px) scale(1.05);
    box-shadow: 0 10px 30px rgba(255, 193, 7, 0.5);
    background: var(--gradient-primary);
    border-color: var(--primary-color);
}

/* Formularios de pergamino */
input, textarea {
    background: rgba(255, 248, 225, 0.8);
    border: 2px solid var(--border-alchemical);
    border-radius: 8px;
    padding: 15px 20px;
    color: var(--text-color);
    font-family: inherit;
    width: 100%;
    margin-bottom: 1.5rem;
    transition: all 0.3s ease;
    box-shadow: inset 0 2px 5px rgba(0,0,0,0.1);
}

input:focus, textarea:focus {
    outline: none;
    border-color: var(--accent-color);
    box-shadow: 0 0 20px rgba(255, 193, 7, 0.3), inset 0 2px 5px rgba(0,0,0,0.1);
    background: rgba(255, 248, 225, 1);
    transform: scale(1.02);
}

/* Efectos de transmutación */
.transmutation-effect {
    position: relative;
    overflow: hidden;
}

.transmutation-effect::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle, rgba(255, 193, 7, 0.1) 0%, transparent 70%);
    animation: transmute 6s ease-in-out infinite;
    pointer-events: none;
}

@keyframes transmute {
    0%, 100% { opacity: 0; transform: scale(0.8); }
    50% { opacity: 1; transform: scale(1.2); }
}

/* Responsive */
@media (max-width: 768px) {
    h1 { font-size: 2.8rem; }
    h1::before, h1::after { display: none; }
    section { padding: 2rem; margin: 1.5rem 0; }
    .container { padding: 0 15px; }
}
"""

    # Crear sesión de base de datos
    db = Session(engine)
    
    try:
        # Verificar si los temas ya existen
        existing_mystic = db.query(Theme).filter(Theme.name == "mystic_lunar").first()
        existing_alchemy = db.query(Theme).filter(Theme.name == "golden_alchemy").first()
        
        themes_created = []
        
        # Crear tema Místico Lunar si no existe
        if not existing_mystic:
            mystic_theme = Theme(
                name="mystic_lunar",
                display_name="Místico Lunar",
                description="Un tema esotérico inspirado en la magia lunar y los misterios cósmicos. Colores púrpuras y violetas con efectos místicos.",
                category="esoteric",
                css_content=mystic_lunar_css,
                theme_variables={
                    "primary_color": "#2d1b69",
                    "secondary_color": "#4a148c",
                    "accent_color": "#7b1fa2",
                    "text_color": "#e8eaf6",
                    "bg_color": "#0a0a0a",
                    "font_family": "Cinzel, Georgia, serif"
                },
                settings={
                    "supports_dark_mode": True,
                    "has_animations": True,
                    "particle_effects": True,
                    "mystical_elements": ["stars", "shimmer", "glow"]
                },
                is_active=True,
                is_default=False
            )
            db.add(mystic_theme)
            themes_created.append("Místico Lunar")
        
        # Crear tema Alquimia Dorada si no existe
        if not existing_alchemy:
            alchemy_theme = Theme(
                name="golden_alchemy",
                display_name="Alquimia Dorada",
                description="Un tema esotérico inspirado en la alquimia medieval y los secretos dorados. Colores dorados y cobrizos con símbolos alquímicos.",
                category="esoteric",
                css_content=golden_alchemy_css,
                theme_variables={
                    "primary_color": "#bf9000",
                    "secondary_color": "#ff8f00",
                    "accent_color": "#ffc107",
                    "text_color": "#2e2e2e",
                    "bg_color": "#1a1a1a",
                    "font_family": "Crimson Text, Times New Roman, serif"
                },
                settings={
                    "supports_dark_mode": False,
                    "has_animations": True,
                    "particle_effects": True,
                    "alchemical_elements": ["hexagons", "transmutation", "golden_ratio"]
                },
                is_active=True,
                is_default=False
            )
            db.add(alchemy_theme)
            themes_created.append("Alquimia Dorada")
        
        # Confirmar cambios
        db.commit()
        
        if themes_created:
            print(f"✅ Temas esotéricos creados exitosamente: {', '.join(themes_created)}")
        else:
            print("ℹ️ Los temas esotéricos ya existen en la base de datos")
        
        # Mostrar todos los temas
        all_themes = db.query(Theme).all()
        print(f"\n📋 Total de temas en la base de datos: {len(all_themes)}")
        for theme in all_themes:
            print(f"   - {theme.display_name} ({theme.category})")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear temas: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_esoteric_themes()
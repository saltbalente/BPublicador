from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import json
import re
from datetime import datetime

from app.models.user import User
from app.models.landing_page import LandingPage
from app.services.landing_service import LandingPageService
from app.core.config import settings
from app.core.exceptions import ValidationError

# Importar servicios de IA existentes
try:
    import openai
except ImportError:
    openai = None

try:
    import requests
except ImportError:
    requests = None

class LandingPageGenerator:
    """
    Generador de landing pages optimizadas con IA
    Integra OpenAI, Gemini y DeepSeek para crear landing pages ultra-optimizadas
    """
    
    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.landing_service = LandingPageService(db)
        
        # Configurar APIs de IA
        self.openai_api_key = user.api_key_openai or getattr(settings, 'OPENAI_API_KEY', None)
        self.deepseek_api_key = user.api_key_deepseek or getattr(settings, 'DEEPSEEK_API_KEY', None)
        self.gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
    
    async def generate_landing_page(self, 
                                  keywords: str, 
                                  phone_number: str, 
                                  ai_provider: str = "openai",
                                  theme_category: str = "general") -> Dict[str, Any]:
        """
        Genera una landing page completa optimizada para SEO
        
        Args:
            keywords: Palabras clave principales
            phone_number: Número de teléfono para WhatsApp
            ai_provider: Proveedor de IA (openai, deepseek, gemini)
            theme_category: Categoría temática (esotérica, salud, negocios, etc.)
        
        Returns:
            Dict con el HTML generado y metadatos
        """
        
        # Validar entrada
        if not keywords or not phone_number:
            raise ValidationError("Keywords y número de teléfono son requeridos")
        
        # Generar contenido con IA
        content_data = await self._generate_content_with_ai(
            keywords=keywords,
            phone_number=phone_number,
            ai_provider=ai_provider,
            theme_category=theme_category
        )
        
        # Generar HTML optimizado
        html_content = self._build_optimized_html(
            content_data=content_data,
            keywords=keywords,
            phone_number=phone_number,
            theme_category=theme_category
        )
        
        # Generar CSS optimizado
        css_content = self._generate_optimized_css(theme_category)
        
        # Generar JavaScript mínimo
        js_content = self._generate_minimal_js(phone_number)
        
        # Crear landing page en la base de datos
        landing_data = {
            "title": content_data["title"],
            "description": content_data["meta_description"],
            "html_content": html_content,
            "css_content": css_content,
            "js_content": js_content,
            "seo_title": content_data["seo_title"],
            "seo_description": content_data["meta_description"],
            "seo_keywords": keywords,
            "settings": {
                "ai_provider": ai_provider,
                "theme_category": theme_category,
                "phone_number": phone_number,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
        landing_page = self.landing_service.create_landing_page(
            user_id=self.user.id,
            landing_data=landing_data
        )
        
        return {
            "success": True,
            "landing_page_id": landing_page.id,
            "slug": landing_page.slug,
            "html_content": html_content,
            "css_content": css_content,
            "js_content": js_content,
            "seo_data": {
                "title": content_data["seo_title"],
                "description": content_data["meta_description"],
                "keywords": keywords
            },
            "preview_url": f"/landing/{landing_page.slug}"
        }
    
    async def _generate_content_with_ai(self, 
                                      keywords: str, 
                                      phone_number: str,
                                      ai_provider: str,
                                      theme_category: str) -> Dict[str, Any]:
        """
        Genera el contenido usando el proveedor de IA especificado
        """
        
        prompt = self._build_content_prompt(keywords, theme_category)
        
        if ai_provider == "openai" and self.openai_api_key:
            return await self._generate_with_openai(prompt, keywords)
        elif ai_provider == "deepseek" and self.deepseek_api_key:
            return await self._generate_with_deepseek(prompt, keywords)
        elif ai_provider == "gemini" and self.gemini_api_key:
            return await self._generate_with_gemini(prompt, keywords)
        else:
            # Fallback a contenido predeterminado
            return self._generate_fallback_content(keywords, theme_category)
    
    def _build_content_prompt(self, keywords: str, theme_category: str) -> str:
        """
        Construye el prompt optimizado para generar contenido de landing page
        """
        
        theme_context = {
            "esotérica": "servicios esotéricos, tarot, astrología, rituales y consultas espirituales",
            "salud": "servicios de salud, bienestar, terapias naturales y consultas médicas",
            "negocios": "servicios empresariales, consultoría, marketing y desarrollo de negocios",
            "general": "servicios profesionales y consultoría especializada"
        }
        
        context = theme_context.get(theme_category, theme_context["general"])
        
        return f"""
Crea contenido para una landing page ultra-optimizada para SEO sobre: {keywords}

Contexto temático: {context}

Requiere generar:
1. Título principal atractivo (H1) con la keyword
2. Pregunta que genere interés
3. Texto introductorio persuasivo (150-200 palabras)
4. Lista de 4-5 beneficios o servicios
5. Sección "Quién soy" profesional
6. Lista de habilidades/especialidades
7. 3 testimonios realistas
8. Llamadas a la acción persuasivas
9. Meta título SEO (50-60 caracteres)
10. Meta descripción SEO (150-160 caracteres)

Requisitos:
- Contenido que parezca escrito por humano profesional
- Uso natural de las keywords sin sobreoptimización
- Tono profesional pero cercano
- Enfoque en beneficios y resultados
- Estructura optimizada para conversión

Formato de respuesta en JSON:
{{
  "title": "Título H1 con keyword",
  "hook_question": "Pregunta que genere interés",
  "intro_text": "Texto introductorio persuasivo",
  "benefits": ["Beneficio 1", "Beneficio 2", "Beneficio 3", "Beneficio 4"],
  "about_me": "Texto sobre quién soy",
  "skills": ["Habilidad 1", "Habilidad 2", "Habilidad 3", "Habilidad 4"],
  "testimonials": [
    {{"name": "Nombre", "text": "Testimonio", "rating": 5}},
    {{"name": "Nombre", "text": "Testimonio", "rating": 5}},
    {{"name": "Nombre", "text": "Testimonio", "rating": 5}}
  ],
  "cta_primary": "Texto CTA principal",
  "cta_secondary": "Texto CTA secundario",
  "seo_title": "Título SEO optimizado",
  "meta_description": "Meta descripción SEO"
}}
"""
    
    async def _generate_with_openai(self, prompt: str, keywords: str) -> Dict[str, Any]:
        """
        Genera contenido usando OpenAI GPT
        """
        if not openai or not self.openai_api_key:
            return self._generate_fallback_content(keywords, "general")
        
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto copywriter y especialista en SEO que crea landing pages de alta conversión."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            print(f"Error con OpenAI: {e}")
            return self._generate_fallback_content(keywords, "general")
    
    async def _generate_with_deepseek(self, prompt: str, keywords: str) -> Dict[str, Any]:
        """
        Genera contenido usando DeepSeek
        """
        if not requests or not self.deepseek_api_key:
            return self._generate_fallback_content(keywords, "general")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Eres un experto copywriter y especialista en SEO que crea landing pages de alta conversión."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 2000,
                "temperature": 0.7
            }
            
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return json.loads(content)
            else:
                print(f"Error DeepSeek: {response.status_code}")
                return self._generate_fallback_content(keywords, "general")
                
        except Exception as e:
            print(f"Error con DeepSeek: {e}")
            return self._generate_fallback_content(keywords, "general")
    
    async def _generate_with_gemini(self, prompt: str, keywords: str) -> Dict[str, Any]:
        """
        Genera contenido usando Google Gemini
        """
        # Implementación placeholder para Gemini
        # Se puede implementar cuando esté disponible la API
        return self._generate_fallback_content(keywords, "general")
    
    def _generate_fallback_content(self, keywords: str, theme_category: str) -> Dict[str, Any]:
        """
        Genera contenido de respaldo cuando las APIs de IA no están disponibles
        """
        
        return {
            "title": f"Servicios Profesionales de {keywords.title()}",
            "hook_question": f"¿Buscas los mejores servicios de {keywords}?",
            "intro_text": f"Descubre cómo nuestros servicios especializados en {keywords} pueden transformar tu experiencia. Con años de experiencia y un enfoque personalizado, te ofrecemos soluciones efectivas y resultados garantizados que superarán tus expectativas.",
            "benefits": [
                "Atención personalizada y profesional",
                "Resultados comprobados y efectivos",
                "Experiencia y conocimiento especializado",
                "Disponibilidad y flexibilidad horaria"
            ],
            "about_me": f"Soy un profesional especializado en {keywords} con amplia experiencia ayudando a personas como tú a alcanzar sus objetivos. Mi enfoque se basa en la excelencia, la dedicación y el compromiso con cada cliente.",
            "skills": [
                f"Especialista certificado en {keywords}",
                "Más de 5 años de experiencia",
                "Metodología probada y efectiva",
                "Atención personalizada 24/7"
            ],
            "testimonials": [
                {"name": "María González", "text": "Excelente servicio, superó todas mis expectativas. Muy profesional y efectivo.", "rating": 5},
                {"name": "Carlos Rodríguez", "text": "Recomiendo totalmente estos servicios. Resultados increíbles en poco tiempo.", "rating": 5},
                {"name": "Ana Martínez", "text": "Profesionalismo y calidad excepcional. Definitivamente volveré a contactar.", "rating": 5}
            ],
            "cta_primary": "¡Contáctame Ahora por WhatsApp!",
            "cta_secondary": "Consulta Gratuita",
            "seo_title": f"Servicios Profesionales de {keywords.title()} | Experto Certificado",
            "meta_description": f"Servicios especializados en {keywords}. Atención personalizada, resultados garantizados. ¡Contacta ahora para una consulta gratuita!"
        }
    
    def _build_optimized_html(self, 
                            content_data: Dict[str, Any], 
                            keywords: str, 
                            phone_number: str,
                            theme_category: str) -> str:
        """
        Construye el HTML optimizado para SEO y velocidad
        """
        
        # Limpiar número de teléfono para WhatsApp
        clean_phone = re.sub(r'[^0-9+]', '', phone_number)
        whatsapp_url = f"https://wa.me/{clean_phone.replace('+', '')}"
        
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{content_data['seo_title']}</title>
    <meta name="description" content="{content_data['meta_description']}">
    <meta name="keywords" content="{keywords}">
    <meta name="robots" content="index, follow">
    <meta name="author" content="Especialista en {keywords}">
    
    <!-- Open Graph -->
    <meta property="og:title" content="{content_data['seo_title']}">
    <meta property="og:description" content="{content_data['meta_description']}">
    <meta property="og:type" content="website">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{content_data['seo_title']}">
    <meta name="twitter:description" content="{content_data['meta_description']}">
    
    <!-- Structured Data -->
    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "Service",
        "name": "{content_data['title']}",
        "description": "{content_data['meta_description']}",
        "provider": {{
            "@type": "Person",
            "name": "Especialista en {keywords}"
        }}
    }}
    </script>
    
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <nav>
            <div class="container">
                <h1 class="logo">Especialista en {keywords.title()}</h1>
                <a href="{whatsapp_url}" class="cta-button" target="_blank">Contactar</a>
            </div>
        </nav>
    </header>
    
    <main>
        <!-- Hero Section -->
        <section class="hero">
            <div class="container">
                <h1>{content_data['title']}</h1>
                <h2 class="hook">{content_data['hook_question']}</h2>
                <p class="intro">{content_data['intro_text']}</p>
                <a href="{whatsapp_url}" class="cta-primary" target="_blank">{content_data['cta_primary']}</a>
            </div>
        </section>
        
        <!-- Benefits Section -->
        <section class="benefits">
            <div class="container">
                <h2>¿Por Qué Elegir Nuestros Servicios?</h2>
                <div class="benefits-grid">
"""
        
        # Agregar beneficios
        for i, benefit in enumerate(content_data['benefits'], 1):
            html += f"""
                    <div class="benefit-item">
                        <div class="benefit-icon">✓</div>
                        <h3>Beneficio {i}</h3>
                        <p>{benefit}</p>
                    </div>
"""
        
        html += f"""
                </div>
            </div>
        </section>
        
        <!-- CTA Section -->
        <section class="cta-section">
            <div class="container">
                <h2>Servicios Relacionados con {keywords.title()}</h2>
                <p>Obtén una consulta personalizada y descubre cómo podemos ayudarte.</p>
                <a href="{whatsapp_url}" class="cta-secondary" target="_blank">{content_data['cta_secondary']}</a>
            </div>
        </section>
        
        <!-- About Section -->
        <section class="about">
            <div class="container">
                <h2>Quién Soy</h2>
                <p>{content_data['about_me']}</p>
            </div>
        </section>
        
        <!-- Skills Section -->
        <section class="skills">
            <div class="container">
                <h2>Mis Habilidades</h2>
                <div class="skills-grid">
"""
        
        # Agregar habilidades
        for skill in content_data['skills']:
            html += f"""
                    <div class="skill-item">
                        <div class="skill-icon">⭐</div>
                        <p>{skill}</p>
                    </div>
"""
        
        html += f"""
                </div>
            </div>
        </section>
        
        <!-- Testimonials Section -->
        <section class="testimonials">
            <div class="container">
                <h2>Testimonios</h2>
                <div class="testimonials-grid">
"""
        
        # Agregar testimonios
        for testimonial in content_data['testimonials']:
            stars = "⭐" * testimonial['rating']
            html += f"""
                    <div class="testimonial-item">
                        <div class="stars">{stars}</div>
                        <p>"{testimonial['text']}"</p>
                        <cite>- {testimonial['name']}</cite>
                    </div>
"""
        
        html += f"""
                </div>
            </div>
        </section>
    </main>
    
    <footer>
        <div class="container">
            <p>&copy; 2024 Especialista en {keywords.title()}. Todos los derechos reservados.</p>
            <p>Contacto: <a href="{whatsapp_url}" target="_blank">{phone_number}</a></p>
        </div>
    </footer>
    
    <!-- WhatsApp Fixed Button -->
    <a href="{whatsapp_url}" class="whatsapp-fixed" target="_blank" aria-label="Contactar por WhatsApp">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893A11.821 11.821 0 0020.885 3.488"/>
        </svg>
    </a>
    
    <script src="script.js"></script>
</body>
</html>
"""
        
        return html
    
    def _generate_optimized_css(self, theme_category: str) -> str:
        """
        Genera CSS optimizado y ultraligero
        """
        
        # Colores según categoría temática
        color_schemes = {
            "esotérica": {
                "primary": "#6B46C1",
                "secondary": "#9333EA",
                "accent": "#F59E0B",
                "text": "#1F2937",
                "bg": "#F9FAFB"
            },
            "salud": {
                "primary": "#059669",
                "secondary": "#10B981",
                "accent": "#3B82F6",
                "text": "#1F2937",
                "bg": "#F0FDF4"
            },
            "negocios": {
                "primary": "#1E40AF",
                "secondary": "#3B82F6",
                "accent": "#F59E0B",
                "text": "#1F2937",
                "bg": "#F8FAFC"
            },
            "general": {
                "primary": "#4F46E5",
                "secondary": "#6366F1",
                "accent": "#10B981",
                "text": "#1F2937",
                "bg": "#FFFFFF"
            }
        }
        
        colors = color_schemes.get(theme_category, color_schemes["general"])
        
        return f"""
/* Reset y base */
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: {colors['text']};
    background-color: {colors['bg']};
}}

.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}}

/* Header */
header {{
    background: white;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    position: sticky;
    top: 0;
    z-index: 100;
}}

nav .container {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 20px;
}}

.logo {{
    font-size: 1.5rem;
    font-weight: bold;
    color: {colors['primary']};
}}

/* Buttons */
.cta-button, .cta-primary, .cta-secondary {{
    display: inline-block;
    padding: 12px 24px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
    text-align: center;
    transition: all 0.3s ease;
    border: none;
    cursor: pointer;
}}

.cta-button {{
    background: {colors['primary']};
    color: white;
}}

.cta-primary {{
    background: {colors['primary']};
    color: white;
    font-size: 1.1rem;
    padding: 16px 32px;
    margin-top: 2rem;
}}

.cta-secondary {{
    background: {colors['secondary']};
    color: white;
}}

.cta-button:hover, .cta-primary:hover, .cta-secondary:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}}

/* Hero Section */
.hero {{
    background: linear-gradient(135deg, {colors['primary']}, {colors['secondary']});
    color: white;
    padding: 4rem 0;
    text-align: center;
}}

.hero h1 {{
    font-size: 3rem;
    margin-bottom: 1rem;
    font-weight: 700;
}}

.hero .hook {{
    font-size: 1.5rem;
    margin-bottom: 1.5rem;
    opacity: 0.9;
}}

.hero .intro {{
    font-size: 1.1rem;
    max-width: 600px;
    margin: 0 auto 2rem;
    opacity: 0.9;
}}

/* Sections */
section {{
    padding: 4rem 0;
}}

section h2 {{
    font-size: 2.5rem;
    text-align: center;
    margin-bottom: 3rem;
    color: {colors['primary']};
}}

/* Benefits Grid */
.benefits-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
}}

.benefit-item {{
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    text-align: center;
    transition: transform 0.3s ease;
}}

.benefit-item:hover {{
    transform: translateY(-5px);
}}

.benefit-icon {{
    font-size: 2rem;
    color: {colors['accent']};
    margin-bottom: 1rem;
}}

.benefit-item h3 {{
    color: {colors['primary']};
    margin-bottom: 1rem;
}}

/* CTA Section */
.cta-section {{
    background: {colors['bg']};
    text-align: center;
}}

/* Skills Grid */
.skills-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
}}

.skill-item {{
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    text-align: center;
}}

.skill-icon {{
    font-size: 1.5rem;
    color: {colors['accent']};
    margin-bottom: 0.5rem;
}}

/* Testimonials */
.testimonials {{
    background: {colors['bg']};
}}

.testimonials-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}}

.testimonial-item {{
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}}

.stars {{
    color: {colors['accent']};
    font-size: 1.2rem;
    margin-bottom: 1rem;
}}

.testimonial-item cite {{
    display: block;
    margin-top: 1rem;
    font-style: normal;
    font-weight: 600;
    color: {colors['primary']};
}}

/* Footer */
footer {{
    background: {colors['text']};
    color: white;
    text-align: center;
    padding: 2rem 0;
}}

footer a {{
    color: {colors['accent']};
    text-decoration: none;
}}

/* WhatsApp Fixed Button */
.whatsapp-fixed {{
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: #25D366;
    color: white;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 20px rgba(37, 211, 102, 0.4);
    z-index: 1000;
    transition: all 0.3s ease;
    text-decoration: none;
}}

.whatsapp-fixed:hover {{
    transform: scale(1.1);
    box-shadow: 0 6px 25px rgba(37, 211, 102, 0.6);
}}

/* Responsive */
@media (max-width: 768px) {{
    .hero h1 {{
        font-size: 2rem;
    }}
    
    .hero .hook {{
        font-size: 1.2rem;
    }}
    
    section h2 {{
        font-size: 2rem;
    }}
    
    .container {{
        padding: 0 15px;
    }}
    
    nav .container {{
        flex-direction: column;
        gap: 1rem;
    }}
}}
"""
    
    def _generate_minimal_js(self, phone_number: str) -> str:
        """
        Genera JavaScript mínimo para funcionalidad básica
        """
        
        clean_phone = re.sub(r'[^0-9+]', '', phone_number)
        
        return f"""
// Funcionalidad mínima para la landing page

// Smooth scroll para enlaces internos
document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
    anchor.addEventListener('click', function (e) {{
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {{
            target.scrollIntoView({{
                behavior: 'smooth',
                block: 'start'
            }});
        }}
    }});
}});

// Tracking de clics en botones de WhatsApp
document.querySelectorAll('a[href*="wa.me"]').forEach(button => {{
    button.addEventListener('click', function() {{
        // Analytics tracking si está disponible
        if (typeof gtag !== 'undefined') {{
            gtag('event', 'whatsapp_click', {{
                'event_category': 'engagement',
                'event_label': 'whatsapp_contact'
            }});
        }}
        
        console.log('WhatsApp contact clicked');
    }});
}});

// Lazy loading para imágenes (si las hay)
if ('IntersectionObserver' in window) {{
    const imageObserver = new IntersectionObserver((entries, observer) => {{
        entries.forEach(entry => {{
            if (entry.isIntersecting) {{
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }}
        }});
    }});
    
    document.querySelectorAll('img[data-src]').forEach(img => {{
        imageObserver.observe(img);
    }});
}}

// Animaciones simples al hacer scroll
const observerOptions = {{
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
}};

const observer = new IntersectionObserver((entries) => {{
    entries.forEach(entry => {{
        if (entry.isIntersecting) {{
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }}
    }});
}}, observerOptions);

// Aplicar animaciones a elementos
document.querySelectorAll('.benefit-item, .skill-item, .testimonial-item').forEach(el => {{
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
}});

// Mensaje de bienvenida en consola
console.log('Landing page cargada correctamente ✅');
console.log('Contacto: {clean_phone}');
"""
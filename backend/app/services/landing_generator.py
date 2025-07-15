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
                                  theme_category: str = "general",
                                  additional_services: Optional[List[str]] = None,
                                  cta_count: int = 2,
                                  paragraph_count: int = 3,
                                  writing_style: str = "persuasiva",
                                  landing_length: str = "mediana",
                                  include_sliders: bool = True,
                                  include_separators: bool = True,
                                  separator_style: str = "waves",
                                  responsive_menu: bool = True,
                                  testimonial_length: str = "medianos") -> Dict[str, Any]:
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
        
        print(f"🤖 Iniciando generación de landing page con IA")
        print(f"📝 Keywords: {keywords}")
        print(f"🔧 AI Provider: {ai_provider.upper()}")
        print(f"🎨 Theme: {theme_category}")
        
        # Validar entrada
        if not keywords or not phone_number:
            raise ValidationError("Keywords y número de teléfono son requeridos")
        
        # Generar contenido con IA
        print(f"🧠 Generando contenido con {ai_provider.upper()}...")
        content_data = await self._generate_content_with_ai(
            keywords=keywords,
            phone_number=phone_number,
            ai_provider=ai_provider,
            theme_category=theme_category,
            additional_services=additional_services,
            cta_count=cta_count,
            paragraph_count=paragraph_count,
            writing_style=writing_style,
            landing_length=landing_length,
            include_sliders=include_sliders,
            include_separators=include_separators,
            separator_style=separator_style,
            responsive_menu=responsive_menu,
            testimonial_length=testimonial_length
        )
        print(f"✅ Contenido generado exitosamente con IA")
        
        # Generar HTML optimizado
        print(f"🏗️ Construyendo HTML optimizado...")
        html_content = self._build_optimized_html(
            content_data=content_data,
            keywords=keywords,
            phone_number=phone_number,
            theme_category=theme_category
        )
        
        # Generar CSS optimizado
        print(f"🎨 Generando CSS optimizado para tema: {theme_category}")
        css_content = self._generate_optimized_css(theme_category)
        
        # Generar JavaScript mínimo
        print(f"⚡ Generando JavaScript funcional...")
        js_content = self._generate_minimal_js(phone_number)
        
        # Crear landing page en la base de datos
        print(f"💾 Guardando landing page en base de datos...")
        
        # Truncar seo_description a 160 caracteres máximo
        original_description = content_data["meta_description"]
        seo_description = self._truncate_seo_description(original_description)
        if len(original_description) > 160:
            print(f"⚠️ SEO description truncada de {len(original_description)} a {len(seo_description)} caracteres")
        
        landing_data = {
            "title": content_data["title"],
            "description": content_data["meta_description"],
            "html_content": html_content,
            "css_content": css_content,
            "js_content": js_content,
            "seo_title": content_data["seo_title"],
            "seo_description": seo_description,
            "seo_keywords": keywords,
            "settings": {
                "ai_provider": ai_provider,
                "theme_category": theme_category,
                "phone_number": phone_number,
                "generated_at": datetime.utcnow().isoformat(),
                "generated_with_ai": True
            }
        }
        
        landing_page = self.landing_service.create_landing_page(
            user_id=self.user.id,
            landing_data=landing_data
        )
        
        print(f"🎉 Landing page generada exitosamente con IA - ID: {landing_page.id}")
        
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
            "preview_url": f"/landing/{landing_page.slug}",
            "ai_provider_used": ai_provider,
            "theme_category": theme_category,
            "generated_with_ai": True
        }
    
    async def _generate_content_with_ai(self, 
                                      keywords: str, 
                                      phone_number: str,
                                      ai_provider: str,
                                      theme_category: str,
                                      additional_services: Optional[List[str]] = None,
                                      cta_count: int = 2,
                                      paragraph_count: int = 3,
                                      writing_style: str = "persuasiva",
                                      landing_length: str = "mediana",
                                      include_sliders: bool = True,
                                      include_separators: bool = True,
                                      separator_style: str = "waves",
                                      responsive_menu: bool = True,
                                      testimonial_length: str = "medianos") -> Dict[str, Any]:
        """
        Genera el contenido usando el proveedor de IA especificado
        """
        
        try:
            # Si el proveedor es "auto", decidir automáticamente
            if ai_provider.lower() == "auto":
                if self.openai_api_key:
                    ai_provider = "openai"
                    print(f"🤖 Modo automático: Usando OpenAI")
                elif self.deepseek_api_key:
                    ai_provider = "deepseek"
                    print(f"🤖 Modo automático: Usando DeepSeek")
                elif self.gemini_api_key:
                    ai_provider = "gemini"
                    print(f"🤖 Modo automático: Usando Gemini")
                else:
                    print(f"⚠️ Modo automático: No hay APIs disponibles, usando contenido de fallback")
                    return self._generate_fallback_content(keywords, theme_category)
            
            print(f"🔄 Intentando generar contenido con {ai_provider.upper()}...")
            
            prompt = self._build_content_prompt(
                keywords=keywords, 
                theme_category=theme_category,
                additional_services=additional_services,
                cta_count=cta_count,
                paragraph_count=paragraph_count,
                writing_style=writing_style,
                landing_length=landing_length,
                include_sliders=include_sliders,
                include_separators=include_separators,
                separator_style=separator_style,
                responsive_menu=responsive_menu,
                testimonial_length=testimonial_length
            )
            
            if ai_provider == "openai" and self.openai_api_key:
                content = await self._generate_with_openai(prompt, keywords)
                print(f"✅ Contenido generado exitosamente con OpenAI")
                return content
            elif ai_provider == "deepseek" and self.deepseek_api_key:
                content = await self._generate_with_deepseek(prompt, keywords)
                print(f"✅ Contenido generado exitosamente con DeepSeek")
                return content
            elif ai_provider == "gemini" and self.gemini_api_key:
                content = await self._generate_with_gemini(prompt, keywords)
                print(f"✅ Contenido generado exitosamente con Gemini")
                return content
            else:
                print(f"⚠️ Proveedor de IA no disponible: {ai_provider}, usando contenido de fallback")
                # Fallback a contenido predeterminado
                return self._generate_fallback_content(keywords, theme_category)
        except Exception as e:
            print(f"❌ Error generando contenido con IA ({ai_provider}): {str(e)}")
            print(f"🔄 Usando contenido de fallback personalizado...")
            # Fallback a contenido predeterminado
            return self._generate_fallback_content(keywords, theme_category)
    
    def _build_content_prompt(self, 
                             keywords: str, 
                             theme_category: str,
                             additional_services: Optional[List[str]] = None,
                             cta_count: int = 2,
                             paragraph_count: int = 3,
                             writing_style: str = "persuasiva",
                             landing_length: str = "mediana",
                             include_sliders: bool = True,
                             include_separators: bool = True,
                             separator_style: str = "waves",
                             responsive_menu: bool = True,
                             testimonial_length: str = "medianos") -> str:
        """
        Construye el prompt optimizado para generar contenido de landing page
        """
        
        theme_context = {
            "esoteric": "servicios esotéricos, tarot, astrología, rituales y consultas espirituales",
            "health": "servicios de salud, bienestar, terapias naturales y consultas médicas",
            "business": "servicios empresariales, consultoría, marketing y desarrollo de negocios",
            "technology": "servicios tecnológicos, desarrollo web, consultoría IT",
            "education": "servicios educativos, formación, cursos y capacitación",
            "finance": "servicios financieros, consultoría económica, inversiones",
            "lifestyle": "servicios de estilo de vida, coaching personal, bienestar",
            "general": "servicios profesionales y consultoría especializada"
        }
        
        context = theme_context.get(theme_category, theme_context["general"])
        
        # Configurar estilo de redacción
        style_instructions = {
            "persuasiva": "Usa un tono persuasivo y convincente, enfocado en beneficios emocionales",
            "tecnica": "Usa un tono técnico y profesional, enfocado en especificaciones y detalles",
            "vendedora": "Usa un tono de ventas directo, con urgencia y llamadas a la acción fuertes",
            "informativa": "Usa un tono informativo y educativo, enfocado en proporcionar valor",
            "emocional": "Usa un tono emocional y empático, conectando con sentimientos",
            "profesional": "Usa un tono profesional y formal, transmitiendo autoridad y confianza"
        }
        
        style_instruction = style_instructions.get(writing_style, style_instructions["persuasiva"])
        
        # Configurar longitud de contenido
        length_config = {
            "corta": {"intro_words": "80-120", "about_words": "60-100", "benefits_count": "3-4"},
            "mediana": {"intro_words": "150-200", "about_words": "100-150", "benefits_count": "4-5"},
            "larga": {"intro_words": "200-300", "about_words": "150-250", "benefits_count": "5-6"}
        }
        
        length_info = length_config.get(landing_length, length_config["mediana"])
        
        # Configurar testimonios
        testimonial_config = {
            "cortos": "testimonios breves de 1-2 líneas",
            "medianos": "testimonios de longitud media de 2-3 líneas",
            "largos": "testimonios detallados de 3-4 líneas"
        }
        
        testimonial_instruction = testimonial_config.get(testimonial_length, testimonial_config["medianos"])
        
        # Servicios adicionales
        additional_services_text = ""
        if additional_services:
            services_list = ", ".join(additional_services)
            additional_services_text = f"\nServicios adicionales a mencionar: {services_list}"
        
        return f"""
Crea contenido Y DISEÑO PERSONALIZADO para una landing page ultra-optimizada para SEO sobre: {keywords}

Contexto temático: {context}{additional_services_text}

Configuración de contenido:
- Estilo de redacción: {style_instruction}
- Longitud: {landing_length} ({length_info['intro_words']} palabras intro, {length_info['about_words']} palabras sobre mí)
- Número de CTAs: {cta_count}
- Párrafos informativos: {paragraph_count}
- Testimonios: {testimonial_instruction}
- Incluir sliders de servicios: {'Sí' if include_sliders else 'No'}
- Incluir separadores SVG: {'Sí' if include_separators else 'No'}
- Estilo de separadores: {separator_style}
- Menú responsivo: {'Sí' if responsive_menu else 'No'}

Requiere generar:
1. Título principal atractivo (H1) con la keyword
2. Pregunta que genere interés
3. Texto introductorio ({length_info['intro_words']} palabras)
4. Lista de {length_info['benefits_count']} beneficios o servicios
5. Sección "Quién soy" ({length_info['about_words']} palabras)
6. Lista de habilidades/especialidades
7. 3 testimonios realistas ({testimonial_instruction})
8. {cta_count} llamadas a la acción persuasivas
9. Meta título SEO (50-60 caracteres)
10. Meta descripción SEO (MÁXIMO 160 caracteres - CRÍTICO)
11. {paragraph_count} párrafos informativos adicionales
12. COLORES Y ESTILOS PERSONALIZADOS basados en las keywords

IMPORTANTE - DISEÑO PERSONALIZADO:
Debes generar una paleta de colores ÚNICA y ESPECÍFICA para "{keywords}".
Analiza las palabras clave y genera colores que representen visualmente el tema:
- Para servicios esotéricos: morados, dorados, místicos
- Para servicios médicos/dentales: azules, blancos, verdes suaves
- Para negocios: azules corporativos, grises elegantes
- Para amor/relaciones: rosas, rojos suaves, dorados
- Para tecnología: azules tech, grises modernos
- Etc. (adapta según las keywords específicas)

Requisitos:
- {style_instruction}
- Uso natural de las keywords sin sobreoptimización
- Enfoque en beneficios y resultados
- Estructura optimizada para conversión
- Contenido que parezca escrito por humano profesional
- COLORES ÚNICOS para cada temática de keywords

Formato de respuesta en JSON:
{{
  "title": "Título H1 con keyword",
  "hook_question": "Pregunta que genere interés",
  "intro_text": "Texto introductorio ({length_info['intro_words']} palabras)",
  "benefits": ["Beneficio 1", "Beneficio 2", "Beneficio 3", "Beneficio 4"],
  "about_me": "Texto sobre quién soy ({length_info['about_words']} palabras)",
  "skills": ["Habilidad 1", "Habilidad 2", "Habilidad 3", "Habilidad 4"],
  "testimonials": [
    {{"name": "Nombre", "text": "Testimonio", "rating": 5}},
    {{"name": "Nombre", "text": "Testimonio", "rating": 5}},
    {{"name": "Nombre", "text": "Testimonio", "rating": 5}}
  ],
  "cta_buttons": ["CTA 1", "CTA 2"],
  "info_paragraphs": ["Párrafo 1", "Párrafo 2", "Párrafo 3"],
  "additional_services": ["Servicio extra 1", "Servicio extra 2"],
  "slider_categories": ["Categoría 1", "Categoría 2", "Categoría 3"],
  "seo_title": "Título SEO optimizado",
  "meta_description": "Meta descripción SEO",
  "custom_colors": {{
    "primary": "#CODIGO_HEX",
    "secondary": "#CODIGO_HEX", 
    "accent": "#CODIGO_HEX",
    "text": "#CODIGO_HEX",
    "bg": "#CODIGO_HEX",
    "bg_secondary": "#CODIGO_HEX"
  }}
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
                    {"role": "system", "content": "Eres un experto copywriter y especialista en SEO que crea landing pages de alta conversión. Responde ÚNICAMENTE con JSON válido, sin texto adicional ni bloques de código."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            # Limpiar el contenido si viene en bloque de código markdown
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
            
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
                    {"role": "system", "content": "Eres un experto copywriter y especialista en SEO que crea landing pages de alta conversión. Responde ÚNICAMENTE con JSON válido, sin texto adicional ni bloques de código."},
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
                
                # Limpiar el contenido si viene en bloque de código markdown
                if content.startswith("```json"):
                    content = content.replace("```json", "").replace("```", "").strip()
                elif content.startswith("```"):
                    content = content.replace("```", "").strip()
                
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
    
    def _truncate_seo_description(self, description: str, max_length: int = 160) -> str:
        """
        Trunca la descripción SEO respetando el límite de caracteres
        """
        if len(description) <= max_length:
            return description
        
        # Truncar en la palabra más cercana al límite
        truncated = description[:max_length-3]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.8:  # Si hay un espacio cerca del final
            return truncated[:last_space] + "..."
        else:
            return truncated + "..."
    
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
            "cta_buttons": ["¡Contáctame Ahora por WhatsApp!", "Consulta Gratuita"],
            "info_paragraphs": ["Información adicional sobre nuestros servicios", "Detalles de nuestro proceso de trabajo", "Garantías y compromisos"],
            "additional_services": ["Servicio complementario 1", "Servicio complementario 2"],
            "slider_categories": ["Categoría Principal", "Servicios Especializados", "Consultoría Avanzada"],
            "seo_title": f"Servicios Profesionales de {keywords.title()} | Experto Certificado",
            "meta_description": f"Servicios especializados en {keywords}. Atención personalizada, resultados garantizados. ¡Contacta ahora para una consulta gratuita!",
            "custom_colors": {
                "primary": "#4F46E5",
                "secondary": "#7C3AED",
                "accent": "#F59E0B",
                "text": "#1F2937",
                "bg": "#F9FAFB",
                "bg_secondary": "#F3F4F6"
            }
        }
    
    def _build_optimized_html(self, 
                            content_data: Dict[str, Any], 
                            keywords: str, 
                            phone_number: str,
                            theme_category: str,
                            include_sliders: bool = True,
                            include_separators: bool = True,
                            separator_style: str = "waves",
                            responsive_menu: bool = True) -> str:
        """
        Construye el HTML completo con todas las funcionalidades avanzadas
        """
        
        # Limpiar número de teléfono para WhatsApp
        clean_phone = re.sub(r'[^0-9+]', '', phone_number)
        whatsapp_url = f"https://wa.me/{clean_phone.replace('+', '')}"
        
        # Generar CSS optimizado con colores personalizados
        css_content = self._generate_optimized_css(content_data)
        
        # Generar separadores SVG si están habilitados
        separator_svg = self._generate_separator_svg(separator_style) if include_separators else ""
        
        # Construir navegación responsiva
        nav_class = "responsive-nav" if responsive_menu else "standard-nav"
        
        # Obtener CTAs dinámicamente
        cta_buttons = content_data.get('cta_buttons', ['Contáctanos ahora', 'Solicita información'])
        
        # Construir HTML completo
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="{content_data['meta_description']}">
  <meta name="robots" content="index, follow">
  <title>{content_data['seo_title']}</title>
  <style>
{css_content}
  </style>
</head>
<body>

  <!-- Hero Section -->
  <section class="hero">
    <div class="container">
      <h1>{content_data['title']}</h1>
      <p class="hook">{content_data['hook_question']}</p>
      <p class="intro">{content_data['intro_text']}</p>
      <a href="{whatsapp_url}" class="cta cta-primary" target="_blank">{cta_buttons[0]}</a>
    </div>
  </section>

  {separator_svg}

  <!-- Servicios Section -->
  <section id="servicios">
    <div class="container">
      <h2>Nuestros Servicios</h2>
      <div class="benefits-grid">
"""
        
        # Agregar servicios/beneficios dinámicamente
        for benefit in content_data['benefits']:
            html += f"""
        <div class="benefit-item">
          <div class="benefit-icon">✨</div>
          <h3>{benefit}</h3>
        </div>
"""
        
        html += "      </div>\n    </div>\n  </section>\n\n"
        
        # Agregar slider de categorías si está habilitado
        if include_sliders and content_data.get('slider_categories'):
            html += f"""
  {separator_svg}

  <!-- Slider de Categorías -->
  <section class="slider-section">
    <div class="container">
      <h2>Especialidades</h2>
      <div class="slider-container">
"""
            for category in content_data['slider_categories']:
                html += f'        <div class="slider-item">{category}</div>\n'
            
            html += "      </div>\n    </div>\n  </section>\n\n"
        
        # Agregar párrafos informativos
        if content_data.get('info_paragraphs'):
            html += f"""
  {separator_svg}

  <!-- Información Adicional -->
  <section class="info-section">
    <div class="container">
      <h2>¿Por qué elegirnos?</h2>
"""
            for paragraph in content_data['info_paragraphs']:
                html += f"      <p>{paragraph}</p>\n"
            
            html += "    </div>\n  </section>\n\n"
        
        # Sección Quién Soy
        html += f"""
  {separator_svg}

  <!-- Quién Soy -->
  <section class="about-section">
    <div class="container">
      <h2>Quién Soy</h2>
      <p>{content_data['about_me']}</p>
      
      <!-- Habilidades -->
      <div class="skills-grid">
"""
        
        # Agregar habilidades
        for skill in content_data.get('skills', []):
            html += f"""
        <div class="skill-item">
          <div class="skill-icon">🎯</div>
          <h4>{skill}</h4>
        </div>
"""
        
        html += "      </div>\n    </div>\n  </section>\n\n"
        
        # CTA Section intermedia
        if len(cta_buttons) > 1:
            html += f"""
  {separator_svg}

  <!-- CTA Intermedia -->
  <section class="cta-section">
    <div class="container">
      <h2>¡No esperes más!</h2>
      <a href="{whatsapp_url}" class="cta cta-secondary" target="_blank">{cta_buttons[1]}</a>
    </div>
  </section>

"""
        
        # Testimonios
        if content_data.get('testimonials'):
            html += f"""
  {separator_svg}

  <!-- Testimonios -->
  <section class="testimonials">
    <div class="container">
      <h2>Lo que dicen nuestros clientes</h2>
      <div class="testimonials-grid">
"""
            
            for testimonial in content_data['testimonials']:
                stars = "⭐" * testimonial.get('rating', 5)
                html += f"""
        <div class="testimonial-item">
          <div class="stars">{stars}</div>
          <p>"{testimonial['text']}"</p>
          <cite>- {testimonial['name']}</cite>
        </div>
"""
            
            html += "      </div>\n    </div>\n  </section>\n\n"
        
        # CTAs adicionales si hay más de 2
        for i, cta in enumerate(cta_buttons[2:], 3):
            html += f"""
  {separator_svg}

  <!-- CTA {i} -->
  <section class="cta-section">
    <div class="container">
      <h2>¡Actúa ahora!</h2>
      <a href="{whatsapp_url}" class="cta cta-primary" target="_blank">{cta}</a>
    </div>
  </section>

"""
        
        # Servicios adicionales si existen
        if content_data.get('additional_services'):
            html += f"""
  {separator_svg}

  <!-- Servicios Adicionales -->
  <section class="additional-services">
    <div class="container">
      <h2>Servicios Adicionales</h2>
      <ul>
"""
            for service in content_data['additional_services']:
                html += f"        <li>{service}</li>\n"
            
            html += "      </ul>\n    </div>\n  </section>\n\n"
        
        # Contacto y Footer
        html += f"""
  {separator_svg}

  <!-- Contacto -->
  <section id="contacto">
    <div class="container">
      <h2>Contáctanos</h2>
      <p>WhatsApp: {phone_number}</p>
      <p>Email: contacto@tuweb.com</p>
      <a href="{whatsapp_url}" class="cta cta-primary" target="_blank">{cta_buttons[0]}</a>
    </div>
  </section>

  <!-- WhatsApp Fixed Button -->
  <a href="{whatsapp_url}" class="whatsapp-fixed" target="_blank">
    📱
  </a>

  <footer>
    <div class="container">
      <p>&copy; 2025 Tu Marca. Todos los derechos reservados.</p>
    </div>
  </footer>

</body>
</html>
"""
        
        return html
    
    def _generate_separator_svg(self, style: str) -> str:
        """
        Genera separadores SVG según el estilo seleccionado
        """
        if style == "waves":
            return '''
  <!-- Separador Waves -->
  <div class="separator">
    <svg viewBox="0 0 1200 120" preserveAspectRatio="none">
      <path d="M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V27.35A600.21,600.21,0,0,0,321.39,56.44Z"></path>
    </svg>
  </div>'''
        elif style == "triangles":
            return '''
  <!-- Separador Triangles -->
  <div class="separator">
    <svg viewBox="0 0 1200 120" preserveAspectRatio="none">
      <polygon points="0,0 1200,0 600,120"></polygon>
    </svg>
  </div>'''
        elif style == "curves":
            return '''
  <!-- Separador Curves -->
  <div class="separator">
    <svg viewBox="0 0 1200 120" preserveAspectRatio="none">
      <path d="M0,0V46.29c47.79,22.2,103.59,32.17,158,28,70.36-5.37,136.33-33.31,206.8-37.5C438.64,32.43,512.34,53.67,583,72.05c69.27,18,138.3,24.88,209.4,13.08,36.15-6,69.85-17.84,104.45-29.34C989.49,25,1113-14.29,1200,52.47V0Z"></path>
    </svg>
  </div>'''
        else:
            return '''
  <!-- Separador Simple -->
  <div class="separator">
    <hr style="border: none; height: 2px; background: linear-gradient(90deg, transparent, #4F46E5, transparent); margin: 2rem 0;">
  </div>'''
    
    def _generate_optimized_css(self, content_data: Dict[str, Any]) -> str:
        """
        Genera CSS optimizado usando los colores personalizados de la IA
        """
        
        # Usar colores personalizados de la IA o fallback
        if 'custom_colors' in content_data and content_data['custom_colors']:
            colors = content_data['custom_colors']
        else:
            # Fallback a colores por defecto
            colors = {
                "primary": "#4F46E5",
                "secondary": "#7C3AED",
                "accent": "#F59E0B",
                "text": "#1F2937",
                "bg": "#F9FAFB",
                "bg_secondary": "#F3F4F6"
            }
        
        # Asegurar que todos los colores necesarios estén presentes
        default_colors = {
            "primary": "#4F46E5",
            "secondary": "#7C3AED",
            "accent": "#F59E0B",
            "text": "#1F2937",
            "bg": "#F9FAFB",
            "bg_secondary": "#F3F4F6"
        }
        
        for key, default_value in default_colors.items():
            if key not in colors:
                colors[key] = default_value
        
        # Los colores ya están configurados arriba con los valores personalizados de la IA
        
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
    margin: 0;
    padding: 0;
}}

/* Container */
.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1rem;
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

section p {{
    margin-bottom: 1rem;
    line-height: 1.6;
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

/* CTA Buttons */
.cta {{
    display: inline-block;
    padding: 1rem 2rem;
    text-decoration: none;
    border-radius: 8px;
    font-weight: bold;
    margin: 0.5rem;
    transition: all 0.3s ease;
    cursor: pointer;
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

.cta:hover, .cta-primary:hover, .cta-secondary:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    color: white;
    text-decoration: none;
}}

/* CTA Section */
.cta-section {{
    background: {colors.get('bg_secondary', colors['bg'])};
    text-align: center;
}}

/* Skills Grid */
.skills-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-top: 2rem;
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

/* Slider */
.slider-section {{
    background: {colors.get('bg_secondary', colors['bg'])};
}}

.slider-container {{
    display: flex;
    gap: 1rem;
    overflow-x: auto;
    padding: 1rem 0;
}}

.slider-item {{
    background: white;
    padding: 1rem 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    white-space: nowrap;
    min-width: 200px;
    text-align: center;
    font-weight: 600;
    color: {colors['primary']};
}}

/* Testimonials */
.testimonials {{
    background: {colors.get('bg_secondary', colors['bg'])};
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

/* Separadores */
.separator {{
    width: 100%;
    overflow: hidden;
    line-height: 0;
}}

.separator svg {{
    position: relative;
    display: block;
    width: calc(100% + 1.3px);
    height: 60px;
    fill: {colors['primary']};
}}

/* Additional Services */
.additional-services ul {{
    list-style: none;
    padding: 0;
    max-width: 600px;
    margin: 0 auto;
}}

.additional-services li {{
    background: white;
    padding: 1rem;
    margin-bottom: 0.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    border-left: 4px solid {colors['primary']};
}}

/* Info Section */
.info-section {{
    background: white;
}}

.info-section p {{
    max-width: 800px;
    margin: 0 auto 1.5rem;
    text-align: center;
    font-size: 1.1rem;
}}

/* About Section */
.about-section {{
    background: {colors.get('bg_secondary', colors['bg'])};
}}

.about-section p {{
    max-width: 800px;
    margin: 0 auto 2rem;
    text-align: center;
    font-size: 1.1rem;
}}

/* Footer */
footer {{
    background: #1F2937;
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
    font-size: 1.5rem;
}}

.whatsapp-fixed:hover {{
    transform: scale(1.1);
    box-shadow: 0 6px 25px rgba(37, 211, 102, 0.6);
    color: white;
    text-decoration: none;
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
    
    .benefits-grid, .testimonials-grid {{
        grid-template-columns: 1fr;
    }}
    
    .skills-grid {{
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    }}
    
    .slider-container {{
        justify-content: flex-start;
    }}
}}

/* Servicios legacy support */
#servicios ul {{
    list-style: none;
    padding: 0;
}}

#servicios li {{
    background: white;
    border-left: 4px solid {colors['primary']};
    padding: 1rem;
    margin-bottom: 0.5rem;
    border-radius: 4px;
}}

/* CTA Button */
.cta {{
    display: inline-block;
    background: {colors['primary']};
    color: white;
    padding: 1rem 2rem;
    text-decoration: none;
    border-radius: 8px;
    font-weight: bold;
    margin-top: 1rem;
    transition: background-color 0.3s ease;
}}

.cta:hover {{
    background: {colors['secondary']};
    color: white;
    text-decoration: none;
}}

/* Footer */
footer {{
    background: {colors['text']};
    color: white;
    text-align: center;
    padding: 2rem 0;
    margin-top: 3rem;
}}

/* Responsive */
@media (max-width: 768px) {{
    header h1 {{
        font-size: 1.5rem;
    }}
    
    main {{
        padding: 1rem;
    }}
    
    nav a {{
        display: block;
        margin: 0.5rem 0;
    }}
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
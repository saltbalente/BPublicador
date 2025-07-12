import openai
import requests
from typing import Dict, Any, Optional
from app.core.config import settings
from app.utils.logging import get_logger
from app.models.user import User
from app.models.keyword import Keyword

class ContentGenerator:
    """Generador de contenido usando OpenAI y DeepSeek"""
    
    def __init__(self, user: User):
        self.user = user
        self.openai_api_key = user.api_key_openai or getattr(settings, 'OPENAI_API_KEY', None)
        self.deepseek_api_key = user.api_key_deepseek or getattr(settings, 'DEEPSEEK_API_KEY', None)
    
    async def generate_content_openai(self, keyword: Keyword, content_type: str = "article") -> Dict[str, str]:
        """Generar contenido usando OpenAI GPT"""
        if not self.openai_api_key:
            raise ValueError("API key de OpenAI no configurada")
        
        # Usar la nueva API de OpenAI
        client = openai.AsyncOpenAI(api_key=self.openai_api_key)
        
        prompt = self._create_prompt(keyword, content_type)
        
        try:
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto redactor de contenido SEO."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            return self._parse_generated_content(content)
            
        except Exception as e:
            raise Exception(f"Error generando contenido con OpenAI: {str(e)}")
    
    async def generate_content_deepseek(self, keyword: Keyword, content_type: str = "article") -> Dict[str, str]:
        """Generar contenido usando DeepSeek API"""
        if not self.deepseek_api_key:
            raise ValueError("API key de DeepSeek no configurada")
        
        prompt = self._create_prompt(keyword, content_type)
        
        headers = {
            "Authorization": f"Bearer {self.deepseek_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Eres un experto redactor de contenido SEO."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            return self._parse_generated_content(content)
            
        except Exception as e:
            raise Exception(f"Error generando contenido con DeepSeek: {str(e)}")
    
    def _create_prompt(self, keyword: Keyword, content_type: str) -> str:
        """Crear prompt para generación de contenido"""
        base_prompt = f"""
Genera un {content_type} profesional y optimizado para SEO sobre la palabra clave: "{keyword.keyword}"

Requisitos específicos:
1. Título atractivo y optimizado para SEO (máximo 60 caracteres)
2. Contenido de al menos 1000 palabras, bien estructurado
3. Incluir la palabra clave de forma natural (densidad 1-2%)
4. Meta descripción persuasiva de máximo 160 caracteres
5. Estructura jerárquica clara con subtítulos
6. Contenido original, informativo y de alta calidad
7. Incluir elementos que generen engagement (preguntas, datos, ejemplos)
8. OBLIGATORIO: Usar etiquetas HTML semánticas

Estructura requerida:
- Introducción que enganche al lector
- 3-5 secciones principales con <h2>
- Subsecciones con <h3> cuando sea necesario
- Listas para mejorar legibilidad
- Al menos una cita o dato relevante en <blockquote>
- Conclusión que invite a la acción

Etiquetas HTML OBLIGATORIAS:
- <h2> para títulos principales de sección
- <h3> para subtítulos de subsección
- <p> para cada párrafo (NUNCA texto suelto)
- <strong> para palabras clave y conceptos importantes
- <em> para énfasis y términos técnicos
- <ul><li> para listas de beneficios, características, etc.
- <ol><li> para procesos paso a paso
- <blockquote> para citas de expertos, estadísticas importantes

Tono y estilo:
- Profesional pero accesible
- Directo y útil para el lector
- Incluir preguntas retóricas
- Usar ejemplos concretos
- Evitar jerga excesiva

Formato de respuesta EXACTO:
[TÍTULO]
Título aquí

[META_DESCRIPCIÓN]
Meta descripción aquí

[CONTENIDO]
Contenido completo aquí con etiquetas HTML semánticas
"""
        
        if keyword.search_volume:
            base_prompt += f"\nVolumen de búsqueda: {keyword.search_volume}"
        
        if keyword.difficulty:
            base_prompt += f"\nDificultad de palabra clave: {keyword.difficulty}"
        
        if keyword.notes:
            base_prompt += f"\nNotas adicionales: {keyword.notes}"
        
        return base_prompt
    
    def _parse_generated_content(self, content: str) -> Dict[str, str]:
        """Parsear contenido generado y extraer título, meta descripción y contenido"""
        result = {
            "title": "",
            "meta_description": "",
            "content": "",
            "author_name": "Redactor IA",
            "publisher_name": "Mi Sitio Web",
            "schema_type": "Article",
            "article_section": "General"
        }
        
        lines = content.split('\n')
        current_section = None
        content_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            
            if line_stripped == "[TÍTULO]":
                current_section = "title"
                continue
            elif line_stripped == "[META_DESCRIPCIÓN]":
                current_section = "meta_description"
                continue
            elif line_stripped == "[CONTENIDO]":
                current_section = "content"
                continue
            
            if current_section:
                if current_section == "content":
                    # Preservar el formato original para mantener las etiquetas HTML
                    content_lines.append(line)
                elif line_stripped:
                    result[current_section] = line_stripped
        
        # Unir las líneas de contenido preservando el formato HTML
        if content_lines:
            result["content"] = '\n'.join(content_lines).strip()
        
        # Si no se encontraron las secciones, usar todo como contenido
        if not result["title"] and not result["content"]:
            result["content"] = self._process_content_for_semantic_html(content)
            # Intentar extraer el primer párrafo como título
            first_line = content.split('\n')[0].strip()
            if len(first_line) < 100:
                result["title"] = first_line
        elif result["content"] and not self._has_html_tags(result["content"]):
            # Si el contenido no tiene etiquetas HTML, procesarlo para añadirlas
            result["content"] = self._process_content_for_semantic_html(result["content"])
        
        return result
    
    def _has_html_tags(self, content: str) -> bool:
        """Verificar si el contenido ya tiene etiquetas HTML"""
        html_tags = ['<p>', '<h2>', '<h3>', '<strong>', '<em>', '<ul>', '<ol>', '<li>', '<blockquote>']
        return any(tag in content for tag in html_tags)
    
    def _process_content_for_semantic_html(self, content: str) -> str:
        """Procesar contenido para añadir etiquetas HTML semánticas"""
        if not content.strip():
            return content
        
        lines = content.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Si la línea ya tiene etiquetas HTML, mantenerla
            if self._has_html_tags(line):
                processed_lines.append(line)
            # Si parece un título (línea corta, sin punto final)
            elif len(line) < 100 and not line.endswith('.') and not line.endswith(':'):
                if not line.startswith('<'):
                    processed_lines.append(f'<h3>{line}</h3>')
                else:
                    processed_lines.append(line)
            # Párrafo normal
            else:
                if not line.startswith('<'):
                    processed_lines.append(f'<p>{line}</p>')
                else:
                    processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    async def generate_content(self, keyword: Keyword, provider: str = "auto", content_type: str = "article") -> Dict[str, str]:
        """Generar contenido usando el proveedor especificado o automático"""
        # Si el proveedor es "auto", decidir automáticamente
        if provider.lower() == "auto":
            # Priorizar OpenAI si está disponible, sino usar DeepSeek
            if self.openai_api_key:
                provider = "openai"
            elif self.deepseek_api_key:
                provider = "deepseek"
            else:
                raise ValueError("No hay API keys configuradas. Por favor configura OpenAI o DeepSeek en tu perfil.")
        
        # Intentar con el proveedor especificado, con fallback automático
        if provider.lower() == "openai":
            if not self.openai_api_key:
                if self.deepseek_api_key:
                    print("⚠️ OpenAI no disponible, usando DeepSeek como alternativa...")
                    return await self.generate_content_deepseek(keyword, content_type)
                else:
                    raise ValueError("API key de OpenAI no configurada y DeepSeek tampoco está disponible")
            return await self.generate_content_openai(keyword, content_type)
        elif provider.lower() == "deepseek":
            if not self.deepseek_api_key:
                if self.openai_api_key:
                    print("⚠️ DeepSeek no disponible, usando OpenAI como alternativa...")
                    return await self.generate_content_openai(keyword, content_type)
                else:
                    raise ValueError("API key de DeepSeek no configurada y OpenAI tampoco está disponible")
            return await self.generate_content_deepseek(keyword, content_type)
        else:
            raise ValueError(f"Proveedor no soportado: {provider}. Use 'openai', 'deepseek' o 'auto'")
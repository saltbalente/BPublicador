import openai
import re
import json
from typing import Dict, Optional, Any
from bs4 import BeautifulSoup
from app.core.config import settings

class AIAssistantService:
    """
    Servicio para el asistente de IA que genera elementos HTML, CSS y JavaScript
    basado en descripciones del usuario y el contexto actual de la landing page.
    """
    
    def __init__(self):
        """Inicializa el servicio con la configuración de OpenAI"""
        openai.api_key = settings.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_code_elements(
        self,
        prompt: str,
        current_html: str,
        current_css: str,
        current_js: str
    ) -> Dict[str, Any]:
        """
        Genera elementos de código basado en el prompt del usuario
        
        Args:
            prompt: Descripción del usuario de lo que quiere agregar
            current_html: HTML actual de la landing page
            current_css: CSS actual de la landing page
            current_js: JavaScript actual de la landing page
            
        Returns:
            Dict con los elementos generados (html, css, js, target, explanation)
        """
        try:
            # Analizar el HTML actual para entender la estructura
            soup = BeautifulSoup(current_html, 'html.parser')
            structure_info = self._analyze_html_structure(soup)
            
            # Crear el prompt para la IA
            ai_prompt = self._create_ai_prompt(
                user_prompt=prompt,
                structure_info=structure_info,
                current_css=current_css,
                current_js=current_js
            )
            
            # Llamar a OpenAI
            response = await self._call_openai(ai_prompt)
            
            # Procesar la respuesta
            result = self._process_ai_response(response, current_html)
            
            return result
            
        except Exception as e:
            raise Exception(f"Error al generar elementos con IA: {str(e)}")
    
    def _validate_and_clean_html(self, generated_html: str, current_html: str) -> str:
        """
        Valida y limpia el HTML generado para evitar duplicación de contenido existente
        """
        try:
            # Parsear el HTML generado
            generated_soup = BeautifulSoup(generated_html, 'html.parser')
            current_soup = BeautifulSoup(current_html, 'html.parser')
            
            # Detectar si el HTML generado contiene elementos principales existentes
            problematic_tags = ['main', 'header', 'footer', 'nav']
            
            for tag in problematic_tags:
                # Si el HTML generado contiene estos elementos principales
                generated_main_elements = generated_soup.find_all(tag)
                current_main_elements = current_soup.find_all(tag)
                
                if generated_main_elements and current_main_elements:
                    # Verificar si hay duplicación de contenido
                    for gen_elem in generated_main_elements:
                        for curr_elem in current_main_elements:
                            # Si encuentra contenido similar, extraer solo el nuevo elemento
                            if self._is_similar_content(gen_elem, curr_elem):
                                # Buscar elementos nuevos dentro del contenido duplicado
                                new_elements = self._extract_new_elements(gen_elem, curr_elem)
                                if new_elements:
                                    return str(new_elements)
            
            # Verificar si hay secciones hero duplicadas
            generated_hero = generated_soup.find('section', class_=re.compile(r'hero'))
            current_hero = current_soup.find('section', class_=re.compile(r'hero'))
            
            if generated_hero and current_hero:
                # Si hay duplicación de hero, extraer solo elementos nuevos
                new_elements = self._extract_new_elements(generated_hero, current_hero)
                if new_elements:
                    return str(new_elements)
            
            # Si no hay duplicación detectada, devolver el HTML original
            return generated_html
            
        except Exception as e:
            # En caso de error, devolver el HTML original
            return generated_html
    
    def _is_similar_content(self, elem1, elem2) -> bool:
        """
        Verifica si dos elementos tienen contenido similar
        """
        try:
            text1 = elem1.get_text().strip()[:100]  # Primeros 100 caracteres
            text2 = elem2.get_text().strip()[:100]
            
            # Si tienen más del 70% de similitud en texto, se considera duplicado
            if len(text1) > 0 and len(text2) > 0:
                similarity = len(set(text1.split()) & set(text2.split())) / len(set(text1.split()) | set(text2.split()))
                return similarity > 0.7
            
            return False
        except:
            return False
    
    def _extract_new_elements(self, generated_elem, current_elem):
        """
        Extrae elementos nuevos del contenido generado que no existen en el contenido actual
        """
        try:
            # Buscar elementos con clases que no existen en el contenido actual
            current_classes = set()
            for elem in current_elem.find_all(class_=True):
                classes = elem.get('class')
                if isinstance(classes, list):
                    current_classes.update(classes)
                else:
                    current_classes.add(classes)
            
            new_elements = []
            for elem in generated_elem.find_all(class_=True):
                elem_classes = elem.get('class')
                if isinstance(elem_classes, list):
                    elem_classes_set = set(elem_classes)
                else:
                    elem_classes_set = {elem_classes}
                
                # Si el elemento tiene clases nuevas, es probablemente nuevo
                if not elem_classes_set.intersection(current_classes):
                    new_elements.append(elem)
            
            # Si encontramos elementos nuevos, devolver el primero
            if new_elements:
                return new_elements[0]
            
            return None
        except:
            return None
    
    def _analyze_html_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Analiza la estructura del HTML actual para proporcionar contexto a la IA
        """
        structure = {
            "classes_found": [],
            "ids_found": [],
            "sections": [],
            "existing_elements": []
        }
        
        # Encontrar todas las clases
        for element in soup.find_all(class_=True):
            classes = element.get('class')
            if isinstance(classes, list):
                structure["classes_found"].extend(classes)
            else:
                structure["classes_found"].append(classes)
        
        # Encontrar todos los IDs
        for element in soup.find_all(id=True):
            structure["ids_found"].append(element.get('id'))
        
        # Encontrar secciones principales
        sections = soup.find_all(['section', 'div'], class_=re.compile(r'(section|container|wrapper|content)'))
        for section in sections:
            classes = section.get('class', [])
            if isinstance(classes, list):
                structure["sections"].extend(classes)
            else:
                structure["sections"].append(classes)
        
        # Elementos existentes importantes
        important_elements = soup.find_all(['h1', 'h2', 'h3', 'nav', 'header', 'footer', 'main'])
        for elem in important_elements:
            structure["existing_elements"].append({
                "tag": elem.name,
                "class": elem.get('class', []),
                "id": elem.get('id'),
                "text": elem.get_text()[:50] if elem.get_text() else None
            })
        
        # Remover duplicados
        structure["classes_found"] = list(set(structure["classes_found"]))
        structure["ids_found"] = list(set(structure["ids_found"]))
        structure["sections"] = list(set(structure["sections"]))
        
        return structure
    
    def _create_ai_prompt(self, user_prompt: str, structure_info: Dict, current_css: str, current_js: str) -> str:
        """
        Crea el prompt optimizado para enviar a OpenAI
        """
        # Detectar si el usuario especifica una ubicación
        target_info = ""
        if "encima de" in user_prompt.lower() or "arriba de" in user_prompt.lower():
            target_info = "\nUBICACIÓN ESPECIFICADA: El usuario quiere insertar el elemento en una ubicación específica. Extrae el selector del prompt del usuario."
        elif "debajo de" in user_prompt.lower() or "abajo de" in user_prompt.lower():
            target_info = "\nUBICACIÓN ESPECIFICADA: El usuario quiere insertar el elemento debajo de un elemento específico. Extrae el selector del prompt del usuario."
        
        prompt = f"""
Eres un experto desarrollador web especializado en crear elementos HTML, CSS y JavaScript para landing pages.

El usuario quiere agregar el siguiente elemento a su landing page:
"{user_prompt}"
{target_info}

CONTEXTO ACTUAL DE LA LANDING PAGE:
- Clases CSS existentes: {', '.join(structure_info['classes_found'][:20])}
- IDs existentes: {', '.join(structure_info['ids_found'][:10])}
- Secciones principales: {', '.join(structure_info['sections'][:10])}
- Elementos importantes: {json.dumps(structure_info['existing_elements'][:5], indent=2)}

⚠️ INSTRUCCIONES CRÍTICAS:
1. Genera ÚNICAMENTE el código del NUEVO elemento solicitado
2. NO incluyas ningún HTML existente de la página
3. NO reproduzcas elementos como <main>, <section class="hero">, <footer>, etc.
4. SOLO crea el elemento específico que el usuario pidió
5. El HTML debe ser responsivo y seguir las mejores prácticas
6. El CSS debe ser moderno, usar flexbox/grid cuando sea apropiado
7. El JavaScript debe ser vanilla JS (sin librerías externas)
8. Usa nombres de clases descriptivos y únicos para evitar conflictos
9. Si el usuario menciona una ubicación específica, DEBES extraer el selector correcto del prompt
10. Para fondos místicos, usa gradientes CSS modernos con colores profundos y texturas

FORMATO DE RESPUESTA (JSON):
{{
    "html": "<div class='nuevo-elemento'>...</div>",
    "css": ".nuevo-elemento {{ ... }}",
    "js": "// JavaScript para el nuevo elemento (o null si no se necesita)",
    "target": "selector CSS donde insertar (ej: '.hero', '#home', 'section.hero')",
    "explanation": "Breve explicación de lo que se creó"
}}

EJEMPLOS DE TARGET:
- Si dice "encima de <section class='hero' id='home'>", el target debe ser ".hero" o "#home"
- Si dice "debajo de la clase testimonial-card", el target debe ser ".testimonial-card"
- Si no especifica ubicación, usa null para target

EJEMPLO DE RESPUESTA CORRECTA:
{{
    "html": "<div class='mystical-slider'>...</div>",
    "css": ".mystical-slider {{ background: linear-gradient(...); }}",
    "js": null,
    "target": ".hero",
    "explanation": "Slider místico creado"
}}

EJEMPLO DE RESPUESTA INCORRECTA (NO HAGAS ESTO):
{{
    "html": "<main>...todo el contenido existente...<div class='nuevo-elemento'>...</div></main>"
}}

NOTAS IMPORTANTES:
- Si no se necesita CSS o JS, devuelve null para esos campos
- El target debe ser un selector CSS válido
- Para sliders, incluye CSS para animaciones suaves
- Usa colores místicos como púrpura, azul profundo, dorado, etc.
- NUNCA incluyas HTML existente en tu respuesta
"""
        return prompt
    
    async def _call_openai(self, prompt: str) -> str:
        """
        Realiza la llamada a OpenAI API
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto desarrollador web que genera código HTML, CSS y JavaScript limpio y eficiente. IMPORTANTE: Solo generas elementos NUEVOS específicos solicitados por el usuario. NUNCA reproduzcas o incluyas HTML existente de la página. Tu trabajo es crear únicamente el elemento solicitado, no duplicar contenido."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Error al llamar a OpenAI: {str(e)}")
    
    def _process_ai_response(self, response: str, current_html: str) -> Dict[str, Any]:
        """
        Procesa la respuesta de OpenAI y extrae los elementos de código
        """
        try:
            # Intentar extraer JSON de la respuesta
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
            else:
                # Si no hay JSON, intentar extraer código manualmente
                result = self._extract_code_manually(response)
            
            # Validar y limpiar el resultado
            html_content = result.get("html") if result.get("html") and result.get("html").strip() else None
            
            # Validar que no se esté duplicando contenido existente
            if html_content:
                html_content = self._validate_and_clean_html(html_content, current_html)
            
            cleaned_result = {
                "html": html_content,
                "css": result.get("css") if result.get("css") and result.get("css").strip() else None,
                "js": result.get("js") if result.get("js") and result.get("js").strip() else None,
                "target": result.get("target") if result.get("target") and result.get("target").strip() else None,
                "explanation": result.get("explanation", "Elemento generado por IA")
            }
            
            # Validar que al menos HTML esté presente
            if not cleaned_result["html"]:
                raise Exception("No se pudo generar HTML válido")
            
            return cleaned_result
            
        except json.JSONDecodeError as e:
            raise Exception(f"Error al procesar respuesta JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Error al procesar respuesta de IA: {str(e)}")
    
    def _extract_code_manually(self, response: str) -> Dict[str, Any]:
        """
        Extrae código manualmente si no se encuentra JSON válido
        """
        result = {
            "html": None,
            "css": None,
            "js": None,
            "target": None,
            "explanation": "Código extraído manualmente"
        }
        
        # Extraer HTML
        html_match = re.search(r'```html\s*([\s\S]*?)```', response, re.IGNORECASE)
        if html_match:
            result["html"] = html_match.group(1).strip()
        
        # Extraer CSS
        css_match = re.search(r'```css\s*([\s\S]*?)```', response, re.IGNORECASE)
        if css_match:
            result["css"] = css_match.group(1).strip()
        
        # Extraer JavaScript
        js_match = re.search(r'```(?:javascript|js)\s*([\s\S]*?)```', response, re.IGNORECASE)
        if js_match:
            result["js"] = js_match.group(1).strip()
        
        return result
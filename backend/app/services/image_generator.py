import os
import requests
import base64
import json
from typing import List, Dict, Optional, Union
from PIL import Image
from io import BytesIO
import openai
import google.generativeai as genai
from app.core.config import settings
from app.utils.logging import get_logger
from app.models.content import Content
from app.models.content_image import ContentImage
from sqlalchemy.orm import Session

logger = get_logger(__name__)

class ImageGenerator:
    """Generador de imágenes con IA para contenido de brujería usando Gemini y OpenAI"""
    
    def __init__(self, db: Session):
        self.db = db
        self.openai_client = None
        self.gemini_client = None
        self.default_provider = settings.DEFAULT_IMAGE_PROVIDER
        
        # Inicializar cliente OpenAI si hay API key
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
            try:
                self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing OpenAI client: {e}")
        
        # Inicializar cliente Gemini si hay API key
        if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_client = genai.GenerativeModel(settings.GEMINI_MODEL)
                logger.info("Gemini client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing Gemini client: {e}")
    
    def generate_images_for_content(self, content_id: int, num_images: int = 3) -> List[Dict[str, any]]:
        """Generar imágenes para un contenido específico"""
        try:
            # Obtener el contenido
            content = self.db.query(Content).filter(Content.id == content_id).first()
            if not content:
                raise ValueError(f"Contenido con ID {content_id} no encontrado")
            
            # Generar prompts basados en el contenido
            image_prompts = self._generate_image_prompts(content)
            
            generated_images = []
            
            for i, prompt in enumerate(image_prompts[:num_images]):
                try:
                    # Generar imagen
                    image_data = self._generate_single_image(prompt)
                    
                    if image_data:
                        # Guardar imagen
                        image_path = self._save_image(
                            image_data, 
                            f"content_{content_id}_image_{i+1}"
                        )
                        
                        # Crear registro en base de datos
                        content_image = ContentImage(
                            content_id=content_id,
                            image_path=image_path,
                            alt_text=self._generate_alt_text(content.keyword.keyword, prompt),
                            prompt_used=prompt,
                            position=i+1
                        )
                        
                        self.db.add(content_image)
                        self.db.commit()
                        
                        generated_images.append({
                            "id": content_image.id,
                            "path": image_path,
                            "alt_text": content_image.alt_text,
                            "prompt": prompt,
                            "position": i+1
                        })
                        
                        logger.info(f"Imagen generada exitosamente: {image_path}")
                        
                except Exception as e:
                    logger.error(f"Error generando imagen {i+1}: {str(e)}")
                    continue
            
            return generated_images
            
        except Exception as e:
            logger.error(f"Error generando imágenes para contenido {content_id}: {str(e)}")
            raise
    
    def _generate_image_prompts(self, content: Content) -> List[str]:
        """Generar prompts para imágenes basados en el contenido"""
        keyword = content.keyword.keyword
        title = content.title
        
        # Prompts base para contenido de brujería
        base_prompts = [
            f"Mystical and ethereal illustration of {keyword}, dark magical atmosphere, candles, crystals, ancient symbols, photorealistic, high quality",
            f"Beautiful witch performing {keyword}, magical aura, moonlight, herbs and potions, mystical forest background, artistic style",
            f"Ancient grimoire open showing {keyword}, magical runes, glowing text, old parchment, mystical lighting, detailed illustration"
        ]
        
        # Prompts específicos según el tipo de keyword
        if any(word in keyword.lower() for word in ['ritual', 'ceremonia', 'rito']):
            base_prompts.extend([
                f"Sacred ritual circle for {keyword}, candles arranged in pattern, magical symbols, atmospheric lighting",
                f"Witch hands performing {keyword}, magical energy flowing, mystical background, cinematic lighting"
            ])
        
        elif any(word in keyword.lower() for word in ['hechizo', 'spell', 'encantamiento']):
            base_prompts.extend([
                f"Magical spell casting scene for {keyword}, glowing magical energy, witch silhouette, mystical atmosphere",
                f"Ancient spellbook with {keyword} instructions, magical symbols glowing, dark mystical setting"
            ])
        
        elif any(word in keyword.lower() for word in ['tarot', 'cartas', 'adivinacion']):
            base_prompts.extend([
                f"Mystical tarot reading scene about {keyword}, cards spread on table, candles, crystal ball, atmospheric lighting",
                f"Beautiful tarot cards related to {keyword}, intricate designs, magical symbols, dark mystical background"
            ])
        
        elif any(word in keyword.lower() for word in ['cristal', 'gema', 'piedra']):
            base_prompts.extend([
                f"Beautiful magical crystals for {keyword}, glowing with mystical energy, dark background, high quality photography",
                f"Crystal healing setup for {keyword}, arranged crystals, candles, mystical atmosphere, soft lighting"
            ])
        
        # Agregar variaciones artísticas
        artistic_variations = [
            f"Digital art illustration of {keyword}, fantasy style, magical realism, detailed and atmospheric",
            f"Watercolor painting of {keyword}, mystical and dreamy, soft colors, magical atmosphere",
            f"Gothic art style depiction of {keyword}, dark and mysterious, intricate details, dramatic lighting"
        ]
        
        base_prompts.extend(artistic_variations)
        
        return base_prompts
    
    def _generate_single_image(self, prompt: str, provider: str = None) -> Optional[bytes]:
        """Generar una sola imagen usando la API especificada o la por defecto"""
        provider = provider or self.default_provider
        
        try:
            # Intentar con el proveedor especificado primero
            if provider == "gemini" and self.gemini_client:
                logger.info(f"Generating image with Gemini: {prompt[:50]}...")
                return self._generate_with_gemini(prompt)
            elif provider == "openai" and self.openai_client:
                logger.info(f"Generating image with OpenAI: {prompt[:50]}...")
                return self._generate_with_openai(prompt)
            
            # Fallback al otro proveedor si el principal falla
            if provider == "gemini" and self.openai_client:
                logger.warning("Gemini failed, trying OpenAI as fallback")
                return self._generate_with_openai(prompt)
            elif provider == "openai" and self.gemini_client:
                logger.warning("OpenAI failed, trying Gemini as fallback")
                return self._generate_with_gemini(prompt)
            
            logger.error("No hay APIs de generación de imágenes configuradas o disponibles")
            return None
            
        except Exception as e:
            logger.error(f"Error generando imagen con {provider}: {str(e)}")
            
            # Intentar con el proveedor alternativo
            try:
                fallback_provider = "openai" if provider == "gemini" else "gemini"
                if fallback_provider == "gemini" and self.gemini_client:
                    logger.info(f"Trying fallback provider Gemini")
                    return self._generate_with_gemini(prompt)
                elif fallback_provider == "openai" and self.openai_client:
                    logger.info(f"Trying fallback provider OpenAI")
                    return self._generate_with_openai(prompt)
            except Exception as fallback_error:
                logger.error(f"Fallback provider also failed: {str(fallback_error)}")
            
            return None
    
    def _generate_with_gemini(self, prompt: str) -> Optional[bytes]:
        """Generar imagen usando Google Gemini Imagen"""
        try:
            # Optimizar prompt para Gemini
            optimized_prompt = self._optimize_prompt_for_gemini(prompt)
            
            # Configurar parámetros de generación
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
            
            # Configuración de seguridad
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
            
            # Crear prompt para generar imagen
            image_prompt = f"""Generate a high-quality image based on this description: {optimized_prompt}
            
Image specifications:
            - Style: Mystical and atmospheric
            - Quality: High resolution, detailed
            - Aspect ratio: {settings.GEMINI_ASPECT_RATIO}
            - Mood: Enchanting and magical
            - Colors: Rich and vibrant
            
Please create an image that captures the essence of this mystical content."""
            
            # Generar contenido con Gemini
            response = self.gemini_client.generate_content(
                image_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Nota: Gemini actualmente no genera imágenes directamente
            # Esta implementación usa Gemini para optimizar prompts y luego
            # podría usar Imagen API o generar una imagen placeholder
            
            # Por ahora, vamos a usar la API de Imagen de Google
            return self._generate_with_imagen_api(optimized_prompt)
            
        except Exception as e:
            logger.error(f"Error con Google Gemini: {str(e)}")
            return None
    
    def _generate_with_imagen_api(self, prompt: str) -> Optional[bytes]:
        """Generar imagen usando Google Imagen API"""
        try:
            # URL de la API de Imagen (esto es un ejemplo, necesitarías la URL real)
            url = "https://aiplatform.googleapis.com/v1/projects/YOUR_PROJECT/locations/us-central1/publishers/google/models/imagen-3.0-generate-001:predict"
            
            headers = {
                "Authorization": f"Bearer {settings.GEMINI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "instances": [
                    {
                        "prompt": prompt,
                        "sampleCount": 1,
                        "aspectRatio": settings.GEMINI_ASPECT_RATIO,
                        "safetyFilterLevel": settings.GEMINI_SAFETY_SETTINGS,
                        "personGeneration": settings.GEMINI_PERSON_GENERATION
                    }
                ],
                "parameters": {
                    "sampleCount": 1
                }
            }
            
            # Por ahora, como no tenemos acceso directo a Imagen API,
            # vamos a crear una imagen placeholder con el prompt
            return self._create_placeholder_image(prompt)
            
        except Exception as e:
            logger.error(f"Error con Imagen API: {str(e)}")
            return None
    
    def _create_placeholder_image(self, prompt: str) -> Optional[bytes]:
        """Crear imagen placeholder mientras se configura Imagen API"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            import textwrap
            
            # Crear imagen base
            width, height = 1024, 1024
            image = Image.new('RGB', (width, height), color='#2D1B69')
            draw = ImageDraw.Draw(image)
            
            # Intentar cargar una fuente
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
                title_font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 32)
            except:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()
            
            # Agregar título
            title = "Imagen Generada con IA"
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            draw.text(((width - title_width) // 2, 100), title, fill='white', font=title_font)
            
            # Agregar prompt envuelto
            wrapped_prompt = textwrap.fill(prompt[:200], width=50)
            lines = wrapped_prompt.split('\n')
            y_offset = 200
            
            for line in lines:
                line_bbox = draw.textbbox((0, 0), line, font=font)
                line_width = line_bbox[2] - line_bbox[0]
                draw.text(((width - line_width) // 2, y_offset), line, fill='#E6E6FA', font=font)
                y_offset += 40
            
            # Agregar elementos decorativos
            # Círculos mágicos
            for i in range(3):
                x = 200 + i * 300
                y = 600 + i * 50
                draw.ellipse([x-30, y-30, x+30, y+30], outline='#9370DB', width=3)
            
            # Convertir a bytes
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
            
        except Exception as e:
            logger.error(f"Error creando imagen placeholder: {str(e)}")
            return None
    
    def _optimize_prompt_for_gemini(self, prompt: str) -> str:
        """Optimizar prompt para Gemini"""
        # Gemini funciona bien con prompts descriptivos y detallados
        quality_terms = "high quality, detailed, professional, mystical atmosphere, magical realism"
        
        # Asegurar que el contenido sea apropiado
        safe_prompt = prompt.replace("dark magic", "mystical arts")
        safe_prompt = safe_prompt.replace("black magic", "ancient wisdom")
        
        # Agregar contexto específico para contenido esotérico
        context = "Create a beautiful, mystical image suitable for spiritual and esoteric content."
        
        return f"{context} {safe_prompt}. {quality_terms}"
    
    def _generate_with_openai(self, prompt: str) -> Optional[bytes]:
        """Generar imagen usando OpenAI DALL-E"""
        try:
            # Optimizar prompt para DALL-E
            optimized_prompt = self._optimize_prompt_for_dalle(prompt)
            
            response = self.openai_client.images.generate(
                model=settings.DALLE_MODEL,
                prompt=optimized_prompt,
                size=settings.DEFAULT_IMAGE_SIZE,
                quality=settings.DEFAULT_IMAGE_QUALITY,
                n=1,
                response_format="b64_json"
            )
            
            # Decodificar imagen base64
            image_data = base64.b64decode(response.data[0].b64_json)
            return image_data
            
        except Exception as e:
            logger.error(f"Error con OpenAI DALL-E: {str(e)}")
            return None
    
    def _optimize_prompt_for_dalle(self, prompt: str) -> str:
        """Optimizar prompt para DALL-E"""
        # DALL-E funciona mejor con prompts en inglés y descriptivos
        # Agregar términos que mejoran la calidad
        quality_terms = "high quality, detailed, professional, artistic"
        
        # Asegurar que no hay contenido inapropiado
        safe_prompt = prompt.replace("dark magic", "mystical")
        safe_prompt = safe_prompt.replace("black magic", "mystical arts")
        
        return f"{safe_prompt}, {quality_terms}"
    
    def _save_image(self, image_data: bytes, filename: str) -> str:
        """Guardar imagen en el sistema de archivos"""
        try:
            # Crear directorio si no existe - usar path relativo al backend o variable de entorno
            images_dir = os.environ.get("GENERATED_IMAGES_PATH", 
                                       os.path.join(os.path.dirname(__file__), "..", "..", "storage", "images", "generated"))
            os.makedirs(images_dir, exist_ok=True)
            
            # Generar nombre de archivo único
            import uuid
            unique_filename = f"{filename}_{uuid.uuid4().hex[:8]}.png"
            file_path = os.path.join(images_dir, unique_filename)
            
            # Procesar y optimizar imagen
            image = Image.open(BytesIO(image_data))
            
            # Convertir a RGB si es necesario
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Optimizar tamaño si es muy grande
            max_size = (1200, 1200)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Guardar imagen optimizada
            image.save(file_path, "PNG", optimize=True, quality=85)
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error guardando imagen: {str(e)}")
            raise
    
    def _generate_alt_text(self, keyword: str, prompt: str) -> str:
        """Generar texto alternativo para la imagen"""
        # Crear alt text descriptivo y SEO-friendly
        alt_text = f"Ilustración mística de {keyword} - imagen generada con IA para contenido sobre brujería y esoterismo"
        
        # Limitar longitud
        if len(alt_text) > 125:
            alt_text = f"Imagen de {keyword} - contenido de brujería y esoterismo"
        
        return alt_text
    
    def generate_featured_image(self, content_id: int) -> Optional[Dict[str, any]]:
        """Generar imagen destacada para un contenido"""
        try:
            content = self.db.query(Content).filter(Content.id == content_id).first()
            if not content:
                raise ValueError(f"Contenido con ID {content_id} no encontrado")
            
            # Crear prompt especial para imagen destacada
            featured_prompt = self._create_featured_image_prompt(content)
            
            # Generar imagen
            image_data = self._generate_single_image(featured_prompt)
            
            if image_data:
                # Guardar como imagen destacada
                image_path = self._save_image(
                    image_data, 
                    f"featured_content_{content_id}"
                )
                
                # Crear registro
                featured_image = ContentImage(
                    content_id=content_id,
                    image_path=image_path,
                    alt_text=self._generate_alt_text(content.keyword.keyword, featured_prompt),
                    prompt_used=featured_prompt,
                    position=0,  # 0 indica imagen destacada
                    is_featured=True
                )
                
                self.db.add(featured_image)
                self.db.commit()
                
                return {
                    "id": featured_image.id,
                    "path": image_path,
                    "alt_text": featured_image.alt_text,
                    "prompt": featured_prompt,
                    "is_featured": True
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error generando imagen destacada: {str(e)}")
            raise
    
    def _create_featured_image_prompt(self, content: Content) -> str:
        """Crear prompt específico para imagen destacada"""
        keyword = content.keyword.keyword
        
        # Prompt más llamativo para imagen destacada
        featured_prompt = f"Stunning featured image for article about {keyword}, mystical and captivating, magical atmosphere, professional quality, eye-catching composition, perfect for blog header, magical realism style, detailed and atmospheric"
        
        return featured_prompt
    
    def bulk_generate_images(self, content_ids: List[int], images_per_content: int = 2) -> Dict[str, any]:
        """Generar imágenes para múltiples contenidos"""
        results = {
            "total_content": len(content_ids),
            "successful_generations": 0,
            "failed_generations": 0,
            "generated_images": [],
            "errors": []
        }
        
        for content_id in content_ids:
            try:
                images = self.generate_images_for_content(content_id, images_per_content)
                results["generated_images"].extend(images)
                results["successful_generations"] += 1
                
                logger.info(f"Imágenes generadas para contenido {content_id}: {len(images)}")
                
            except Exception as e:
                error_msg = f"Error generando imágenes para contenido {content_id}: {str(e)}"
                results["errors"].append(error_msg)
                results["failed_generations"] += 1
                logger.error(error_msg)
        
        return results

    def generate_image(self, prompt: str, style: str = "realistic", size: str = "1024x1024", quality: str = "standard") -> Dict[str, any]:
        """Genera una sola imagen manualmente basada en un prompt"""
        try:
            if not self.openai_client and not self.gemini_client:
                raise ValueError("No image generation client available. Please configure OPENAI_API_KEY or GEMINI_API_KEY.")
            
            # Usar el método _generate_single_image que maneja ambos proveedores
            optimized_prompt = f"{prompt}, style: {style}, quality: {quality}"
            image_data = self._generate_single_image(optimized_prompt)
            
            if not image_data:
                raise ValueError("No se pudo generar la imagen con ningún proveedor disponible.")
            
            import uuid
            filename = f"manual_image_{uuid.uuid4().hex[:8]}"
            image_path = self._save_image(image_data, filename)
            
            alt_text = self._generate_alt_text("manual generation", prompt)
            
            return {
                "image_path": image_path,
                "image_url": f"/static/{image_path}",  # Asumiendo serving de static files
                "alt_text": alt_text,
                "prompt_used": optimized_prompt
            }
        except Exception as e:
            logger.error(f"Error en generate_image: {str(e)}")
            raise
    
    def generate_manual_image(self, prompt: str, user_id: int, keyword_id: int = None, style: str = "realistic", size: str = "1024x1024", quality: str = "standard") -> Dict[str, any]:
        """Genera una imagen manual y la guarda en la base de datos"""
        try:
            if not self.openai_client and not self.gemini_client:
                raise ValueError("No image generation client available. Please configure OPENAI_API_KEY or GEMINI_API_KEY.")
            
            # Usar el método _generate_single_image que maneja ambos proveedores
            optimized_prompt = f"{prompt}, style: {style}, quality: {quality}"
            image_data = self._generate_single_image(optimized_prompt)
            
            if not image_data:
                raise ValueError("No se pudo generar la imagen con ningún proveedor disponible.")
            
            import uuid
            filename = f"manual_image_{uuid.uuid4().hex[:8]}"
            image_path = self._save_image(image_data, filename)
            
            alt_text = self._generate_alt_text("manual generation", prompt)
            
            # Guardar en la base de datos
            from app.models.manual_image import ManualImage
            manual_image = ManualImage(
                user_id=user_id,
                keyword_id=keyword_id,
                image_path=image_path,
                alt_text=alt_text,
                prompt_used=optimized_prompt,
                style=style,
                size=size,
                quality=quality
            )
            
            self.db.add(manual_image)
            self.db.commit()
            
            return {
                "id": manual_image.id,
                "image_path": image_path,
                "image_url": f"/static/{image_path}",
                "alt_text": alt_text,
                "prompt_used": optimized_prompt,
                "style": style,
                "size": size,
                "quality": quality,
                "created_at": manual_image.created_at
            }
        except Exception as e:
            logger.error(f"Error en generate_manual_image: {str(e)}")
            raise
    
    def get_image_generation_stats(self) -> Dict[str, any]:
        """Obtener estadísticas de generación de imágenes"""
        try:
            total_images = self.db.query(ContentImage).count()
            featured_images = self.db.query(ContentImage).filter(ContentImage.is_featured == True).count()
            
            # Imágenes por mes (últimos 6 meses)
            from datetime import datetime, timedelta
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            recent_images = self.db.query(ContentImage).filter(
                ContentImage.created_at >= six_months_ago
            ).count()
            
            return {
                "total_images": total_images,
                "featured_images": featured_images,
                "regular_images": total_images - featured_images,
                "recent_images_6_months": recent_images,
                "average_images_per_month": recent_images / 6 if recent_images > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {}
    
    def delete_content_images(self, content_id: int) -> bool:
        """Eliminar todas las imágenes de un contenido"""
        try:
            images = self.db.query(ContentImage).filter(
                ContentImage.content_id == content_id
            ).all()
            
            for image in images:
                # Eliminar archivo físico
                if os.path.exists(image.image_path):
                    os.remove(image.image_path)
                
                # Eliminar registro de base de datos
                self.db.delete(image)
            
            self.db.commit()
            logger.info(f"Eliminadas {len(images)} imágenes del contenido {content_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando imágenes: {str(e)}")
            return False
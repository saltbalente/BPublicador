"""Content generation service using AI providers."""

import logging
import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from config import config

logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """Available AI providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    FALLBACK = "fallback"


@dataclass
class ContentRequest:
    """Content generation request."""
    topic: str
    content_type: str = "blog_post"
    tone: str = "professional"
    length: str = "medium"
    language: str = "es"
    keywords: Optional[List[str]] = None
    target_audience: Optional[str] = None
    include_images: bool = True
    seo_optimized: bool = True


@dataclass
class GeneratedContent:
    """Generated content response."""
    title: str
    content: str
    summary: str
    tags: List[str]
    meta_description: str
    provider: str
    generation_time: float
    word_count: int
    images_suggested: List[str]
    seo_score: Optional[float] = None


class ContentService:
    """Service for AI-powered content generation."""
    
    def __init__(self):
        self.providers = {}
        self.default_provider = AIProvider.OPENAI
        self.fallback_provider = AIProvider.GEMINI
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize available AI providers."""
        try:
            # Initialize OpenAI if API key is available
            if config.openai_api_key:
                self.providers[AIProvider.OPENAI] = OpenAIProvider(config.openai_api_key)
                logger.info("OpenAI provider initialized")
            
            # Initialize Gemini if API key is available
            if config.gemini_api_key:
                self.providers[AIProvider.GEMINI] = GeminiProvider(config.gemini_api_key)
                logger.info("Gemini provider initialized")
            
            # Always have fallback provider
            self.providers[AIProvider.FALLBACK] = FallbackProvider()
            
            if not self.providers:
                logger.warning("No AI providers configured, using fallback only")
                
        except Exception as e:
            logger.error(f"Error initializing AI providers: {e}")
            self.providers = {AIProvider.FALLBACK: FallbackProvider()}
    
    async def generate_content(
        self, 
        request: ContentRequest, 
        preferred_provider: Optional[AIProvider] = None
    ) -> GeneratedContent:
        """Generate content using AI providers with fallback."""
        start_time = datetime.now()
        
        # Determine provider order
        providers_to_try = self._get_provider_order(preferred_provider)
        
        last_error = None
        
        for provider_type in providers_to_try:
            if provider_type not in self.providers:
                continue
                
            try:
                logger.info(f"Attempting content generation with {provider_type.value}")
                
                provider = self.providers[provider_type]
                content = await provider.generate_content(request)
                
                # Calculate generation time
                generation_time = (datetime.now() - start_time).total_seconds()
                content.generation_time = generation_time
                content.provider = provider_type.value
                
                logger.info(
                    f"Content generated successfully with {provider_type.value} "
                    f"in {generation_time:.2f}s"
                )
                
                return content
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Content generation failed with {provider_type.value}: {e}"
                )
                continue
        
        # If all providers failed, raise the last error
        raise Exception(
            f"All content generation providers failed. Last error: {last_error}"
        )
    
    def _get_provider_order(self, preferred: Optional[AIProvider]) -> List[AIProvider]:
        """Get ordered list of providers to try."""
        available_providers = list(self.providers.keys())
        
        if preferred and preferred in available_providers:
            # Try preferred first, then others, fallback last
            order = [preferred]
            for provider in available_providers:
                if provider != preferred and provider != AIProvider.FALLBACK:
                    order.append(provider)
            if AIProvider.FALLBACK in available_providers:
                order.append(AIProvider.FALLBACK)
            return order
        
        # Default order: primary, fallback, others
        order = []
        if self.default_provider in available_providers:
            order.append(self.default_provider)
        if self.fallback_provider in available_providers and self.fallback_provider != self.default_provider:
            order.append(self.fallback_provider)
        
        # Add remaining providers
        for provider in available_providers:
            if provider not in order and provider != AIProvider.FALLBACK:
                order.append(provider)
        
        # Fallback always last
        if AIProvider.FALLBACK in available_providers:
            order.append(AIProvider.FALLBACK)
        
        return order
    
    async def generate_title_suggestions(
        self, 
        topic: str, 
        count: int = 5
    ) -> List[str]:
        """Generate title suggestions for a topic."""
        request = ContentRequest(
            topic=topic,
            content_type="title_suggestions",
            length="short"
        )
        
        try:
            # Use the first available provider
            provider_type = next(iter(self.providers.keys()))
            provider = self.providers[provider_type]
            
            if hasattr(provider, 'generate_titles'):
                return await provider.generate_titles(topic, count)
            else:
                # Fallback to content generation
                content = await provider.generate_content(request)
                return [content.title]
                
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            return [f"Artículo sobre {topic}"]
    
    async def optimize_content_for_seo(
        self, 
        content: str, 
        target_keywords: List[str]
    ) -> Dict[str, Any]:
        """Optimize content for SEO."""
        try:
            # Simple SEO analysis
            word_count = len(content.split())
            keyword_density = {}
            
            for keyword in target_keywords:
                count = content.lower().count(keyword.lower())
                density = (count / word_count) * 100 if word_count > 0 else 0
                keyword_density[keyword] = {
                    "count": count,
                    "density": round(density, 2)
                }
            
            # Calculate basic SEO score
            seo_score = self._calculate_seo_score(content, target_keywords)
            
            return {
                "word_count": word_count,
                "keyword_density": keyword_density,
                "seo_score": seo_score,
                "recommendations": self._get_seo_recommendations(
                    content, target_keywords, seo_score
                )
            }
            
        except Exception as e:
            logger.error(f"SEO optimization failed: {e}")
            return {
                "word_count": len(content.split()),
                "seo_score": 50.0,
                "recommendations": ["Error analyzing SEO"]
            }
    
    def _calculate_seo_score(self, content: str, keywords: List[str]) -> float:
        """Calculate basic SEO score."""
        score = 0.0
        word_count = len(content.split())
        
        # Word count score (optimal: 300-2000 words)
        if 300 <= word_count <= 2000:
            score += 30
        elif word_count > 100:
            score += 15
        
        # Keyword presence score
        for keyword in keywords:
            if keyword.lower() in content.lower():
                score += 20 / len(keywords)
        
        # Content structure score (basic)
        if len(content) > 500:
            score += 20
        
        # Readability score (basic)
        sentences = content.count('.') + content.count('!') + content.count('?')
        if sentences > 0:
            avg_words_per_sentence = word_count / sentences
            if 10 <= avg_words_per_sentence <= 25:
                score += 30
            elif avg_words_per_sentence <= 35:
                score += 15
        
        return min(score, 100.0)
    
    def _get_seo_recommendations(
        self, 
        content: str, 
        keywords: List[str], 
        score: float
    ) -> List[str]:
        """Get SEO improvement recommendations."""
        recommendations = []
        word_count = len(content.split())
        
        if word_count < 300:
            recommendations.append("Considera expandir el contenido a al menos 300 palabras")
        elif word_count > 2000:
            recommendations.append("El contenido es muy largo, considera dividirlo")
        
        for keyword in keywords:
            if keyword.lower() not in content.lower():
                recommendations.append(f"Incluye la palabra clave '{keyword}' en el contenido")
        
        if score < 70:
            recommendations.append("Mejora la estructura del contenido con subtítulos")
            recommendations.append("Optimiza la densidad de palabras clave")
        
        return recommendations or ["El contenido está bien optimizado"]


class BaseAIProvider:
    """Base class for AI providers."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    async def generate_content(self, request: ContentRequest) -> GeneratedContent:
        """Generate content based on request."""
        raise NotImplementedError
    
    def _create_prompt(self, request: ContentRequest) -> str:
        """Create prompt for AI generation."""
        prompt_parts = [
            f"Genera un {request.content_type} sobre el tema: {request.topic}",
            f"Tono: {request.tone}",
            f"Longitud: {request.length}",
            f"Idioma: {request.language}"
        ]
        
        if request.keywords:
            prompt_parts.append(f"Palabras clave: {', '.join(request.keywords)}")
        
        if request.target_audience:
            prompt_parts.append(f"Audiencia objetivo: {request.target_audience}")
        
        if request.seo_optimized:
            prompt_parts.append("Optimizado para SEO")
        
        prompt_parts.extend([
            "\nFormato de respuesta JSON:",
            "{",
            '  "title": "Título del artículo",',
            '  "content": "Contenido completo del artículo",',
            '  "summary": "Resumen breve",',
            '  "tags": ["tag1", "tag2", "tag3"],',
            '  "meta_description": "Descripción meta para SEO",',
            '  "images_suggested": ["descripción imagen 1", "descripción imagen 2"]',
            "}"
        ])
        
        return "\n".join(prompt_parts)


class OpenAIProvider(BaseAIProvider):
    """OpenAI content provider."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("OpenAI library not installed")
    
    async def generate_content(self, request: ContentRequest) -> GeneratedContent:
        """Generate content using OpenAI."""
        try:
            prompt = self._create_prompt(request)
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto redactor de contenido."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            content_text = response.choices[0].message.content
            return self._parse_response(content_text)
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise
    
    def _parse_response(self, response_text: str) -> GeneratedContent:
        """Parse AI response into GeneratedContent."""
        try:
            # Try to extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                data = json.loads(json_str)
                
                return GeneratedContent(
                    title=data.get('title', 'Título generado'),
                    content=data.get('content', response_text),
                    summary=data.get('summary', 'Resumen no disponible'),
                    tags=data.get('tags', ['general']),
                    meta_description=data.get('meta_description', ''),
                    images_suggested=data.get('images_suggested', []),
                    provider="openai",
                    generation_time=0.0,
                    word_count=len(data.get('content', '').split())
                )
            else:
                # Fallback parsing
                return self._fallback_parse(response_text)
                
        except json.JSONDecodeError:
            return self._fallback_parse(response_text)
    
    def _fallback_parse(self, text: str) -> GeneratedContent:
        """Fallback parsing when JSON parsing fails."""
        lines = text.split('\n')
        title = lines[0] if lines else "Título generado"
        content = text
        
        return GeneratedContent(
            title=title,
            content=content,
            summary=content[:200] + "..." if len(content) > 200 else content,
            tags=['general'],
            meta_description=content[:160] if len(content) > 160 else content,
            images_suggested=[],
            provider="openai",
            generation_time=0.0,
            word_count=len(content.split())
        )


class GeminiProvider(BaseAIProvider):
    """Google Gemini content provider."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        except ImportError:
            raise ImportError("Google Generative AI library not installed")
    
    async def generate_content(self, request: ContentRequest) -> GeneratedContent:
        """Generate content using Gemini."""
        try:
            prompt = self._create_prompt(request)
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            content_text = response.text
            return self._parse_response(content_text)
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            raise
    
    def _parse_response(self, response_text: str) -> GeneratedContent:
        """Parse Gemini response (similar to OpenAI)."""
        # Use same parsing logic as OpenAI
        openai_provider = OpenAIProvider("dummy")
        content = openai_provider._parse_response(response_text)
        content.provider = "gemini"
        return content


class FallbackProvider(BaseAIProvider):
    """Fallback provider for when AI services are unavailable."""
    
    def __init__(self):
        super().__init__()
    
    async def generate_content(self, request: ContentRequest) -> GeneratedContent:
        """Generate basic content without AI."""
        logger.info("Using fallback content generation")
        
        # Generate basic content structure
        title = f"Artículo sobre {request.topic}"
        
        content_parts = [
            f"# {title}\n",
            f"Este es un artículo sobre {request.topic}. ",
            "El contenido ha sido generado usando el modo de respaldo ",
            "debido a que los servicios de IA no están disponibles.\n\n",
            f"## Introducción\n",
            f"En este artículo exploraremos {request.topic} ",
            "y sus aspectos más relevantes.\n\n",
            f"## Desarrollo\n",
            f"El tema de {request.topic} es importante porque ",
            "permite comprender mejor diversos aspectos ",
            "relacionados con el área de interés.\n\n",
            f"## Conclusión\n",
            f"En resumen, {request.topic} es un tema que merece ",
            "atención y estudio detallado."
        ]
        
        content = "".join(content_parts)
        
        return GeneratedContent(
            title=title,
            content=content,
            summary=f"Artículo básico sobre {request.topic}",
            tags=[request.topic.lower(), "general"],
            meta_description=f"Información sobre {request.topic}",
            images_suggested=[f"Imagen relacionada con {request.topic}"],
            provider="fallback",
            generation_time=0.1,
            word_count=len(content.split())
        )


# Global content service instance
content_service = ContentService()
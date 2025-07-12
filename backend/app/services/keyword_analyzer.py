import re
import requests
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.keyword import Keyword
from app.models.content import Content
from app.utils.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)

class KeywordAnalyzer:
    """Analizador de keywords para detectar canibalización y optimización SEO"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_keyword_cannibalization(self, keyword: str) -> Dict[str, any]:
        """Analizar canibalización de keywords"""
        try:
            # Buscar contenido existente con la misma keyword
            existing_content = self.db.query(Content).join(Keyword).filter(
                Keyword.keyword.ilike(f"%{keyword}%")
            ).all()
            
            # Buscar keywords similares
            similar_keywords = self._find_similar_keywords(keyword)
            
            # Calcular score de canibalización
            cannibalization_score = self._calculate_cannibalization_score(
                keyword, existing_content, similar_keywords
            )
            
            return {
                "keyword": keyword,
                "cannibalization_risk": cannibalization_score,
                "existing_content_count": len(existing_content),
                "similar_keywords": similar_keywords,
                "existing_content": [
                    {
                        "id": content.id,
                        "title": content.title,
                        "keyword": content.keyword.keyword,
                        "created_at": content.created_at.isoformat()
                    } for content in existing_content
                ],
                "recommendations": self._get_cannibalization_recommendations(
                    cannibalization_score, existing_content
                )
            }
            
        except Exception as e:
            logger.error(f"Error analizando canibalización: {str(e)}")
            raise
    
    def _find_similar_keywords(self, keyword: str) -> List[Dict[str, any]]:
        """Encontrar keywords similares en la base de datos"""
        # Dividir keyword en palabras
        words = keyword.lower().split()
        similar_keywords = []
        
        # Buscar keywords que contengan palabras similares
        for word in words:
            if len(word) > 3:  # Solo palabras significativas
                similar = self.db.query(Keyword).filter(
                    Keyword.keyword.ilike(f"%{word}%")
                ).limit(10).all()
                
                for kw in similar:
                    if kw.keyword.lower() != keyword.lower():
                        similarity_score = self._calculate_similarity(keyword, kw.keyword)
                        if similarity_score > 0.6:  # Umbral de similitud
                            similar_keywords.append({
                                "keyword": kw.keyword,
                                "similarity_score": similarity_score,
                                "status": kw.status.value,
                                "priority": kw.priority
                            })
        
        # Ordenar por similitud y eliminar duplicados
        unique_keywords = {}
        for kw in similar_keywords:
            if kw["keyword"] not in unique_keywords:
                unique_keywords[kw["keyword"]] = kw
        
        return sorted(unique_keywords.values(), key=lambda x: x["similarity_score"], reverse=True)
    
    def _calculate_similarity(self, keyword1: str, keyword2: str) -> float:
        """Calcular similitud entre dos keywords usando Jaccard similarity"""
        words1 = set(keyword1.lower().split())
        words2 = set(keyword2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if len(union) == 0:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _calculate_cannibalization_score(self, keyword: str, existing_content: List[Content], similar_keywords: List[Dict]) -> str:
        """Calcular score de riesgo de canibalización"""
        score = 0
        
        # Penalizar por contenido existente con la misma keyword
        score += len(existing_content) * 30
        
        # Penalizar por keywords muy similares
        for similar in similar_keywords:
            if similar["similarity_score"] > 0.8:
                score += 25
            elif similar["similarity_score"] > 0.6:
                score += 15
        
        # Determinar nivel de riesgo
        if score >= 70:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        elif score >= 20:
            return "LOW"
        else:
            return "NONE"
    
    def _get_cannibalization_recommendations(self, risk_level: str, existing_content: List[Content]) -> List[str]:
        """Obtener recomendaciones basadas en el riesgo de canibalización"""
        recommendations = []
        
        if risk_level == "HIGH":
            recommendations.extend([
                "⚠️ Alto riesgo de canibalización detectado",
                "Considera consolidar el contenido existente",
                "Usa variaciones long-tail de la keyword",
                "Enfócate en diferentes intenciones de búsqueda"
            ])
        elif risk_level == "MEDIUM":
            recommendations.extend([
                "⚡ Riesgo moderado de canibalización",
                "Revisa el contenido existente antes de proceder",
                "Considera un enfoque diferente o más específico",
                "Asegúrate de que el nuevo contenido aporte valor único"
            ])
        elif risk_level == "LOW":
            recommendations.extend([
                "✅ Riesgo bajo de canibalización",
                "Puedes proceder con precaución",
                "Asegúrate de diferenciar el contenido"
            ])
        else:
            recommendations.extend([
                "🎯 No se detectó riesgo de canibalización",
                "Keyword segura para usar",
                "Procede con la generación de contenido"
            ])
        
        if existing_content:
            recommendations.append(f"📊 Se encontraron {len(existing_content)} contenidos relacionados")
        
        return recommendations
    
    def analyze_keyword_seo_potential(self, keyword: str) -> Dict[str, any]:
        """Analizar potencial SEO de una keyword"""
        try:
            # Análisis básico de la keyword
            word_count = len(keyword.split())
            character_count = len(keyword)
            
            # Detectar tipo de keyword
            keyword_type = self._detect_keyword_type(keyword)
            
            # Calcular dificultad estimada
            difficulty = self._estimate_keyword_difficulty(keyword)
            
            # Sugerir variaciones
            variations = self._suggest_keyword_variations(keyword)
            
            return {
                "keyword": keyword,
                "word_count": word_count,
                "character_count": character_count,
                "keyword_type": keyword_type,
                "estimated_difficulty": difficulty,
                "seo_score": self._calculate_seo_score(keyword, word_count, keyword_type),
                "variations": variations,
                "recommendations": self._get_seo_recommendations(keyword, keyword_type, difficulty)
            }
            
        except Exception as e:
            logger.error(f"Error analizando potencial SEO: {str(e)}")
            raise
    
    def _detect_keyword_type(self, keyword: str) -> str:
        """Detectar tipo de keyword (informacional, comercial, navegacional, transaccional)"""
        keyword_lower = keyword.lower()
        
        # Palabras indicadoras de intención
        informational_words = ['qué', 'cómo', 'por qué', 'cuándo', 'dónde', 'guía', 'tutorial', 'significado']
        commercial_words = ['mejor', 'top', 'comparar', 'vs', 'review', 'opinión', 'recomendación']
        transactional_words = ['comprar', 'precio', 'barato', 'oferta', 'descuento', 'gratis']
        
        # Palabras específicas del dominio de brujería
        brujeria_informational = ['ritual', 'hechizo', 'significado', 'historia', 'origen', 'tradición']
        brujeria_commercial = ['mejor', 'efectivo', 'poderoso', 'auténtico']
        
        if any(word in keyword_lower for word in informational_words + brujeria_informational):
            return "informational"
        elif any(word in keyword_lower for word in commercial_words + brujeria_commercial):
            return "commercial"
        elif any(word in keyword_lower for word in transactional_words):
            return "transactional"
        else:
            return "navigational"
    
    def _estimate_keyword_difficulty(self, keyword: str) -> str:
        """Estimar dificultad de keyword basada en características"""
        word_count = len(keyword.split())
        
        # Keywords más largas tienden a ser menos competitivas
        if word_count >= 4:
            return "LOW"
        elif word_count == 3:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _calculate_seo_score(self, keyword: str, word_count: int, keyword_type: str) -> int:
        """Calcular score SEO de 0-100"""
        score = 50  # Base score
        
        # Bonificación por long-tail keywords
        if word_count >= 3:
            score += 20
        elif word_count >= 4:
            score += 30
        
        # Bonificación por tipo de keyword
        if keyword_type == "informational":
            score += 15
        elif keyword_type == "commercial":
            score += 10
        
        # Penalización por keywords muy cortas
        if word_count == 1:
            score -= 20
        
        return min(100, max(0, score))
    
    def _suggest_keyword_variations(self, keyword: str) -> List[str]:
        """Sugerir variaciones de la keyword"""
        variations = []
        
        # Prefijos y sufijos comunes para brujería
        prefixes = ['ritual de', 'hechizo de', 'significado de', 'historia de', 'origen de']
        suffixes = ['efectivo', 'poderoso', 'auténtico', 'tradicional', 'moderno', 'fácil']
        
        # Generar variaciones con prefijos
        for prefix in prefixes:
            if not keyword.lower().startswith(prefix):
                variations.append(f"{prefix} {keyword}")
        
        # Generar variaciones con sufijos
        for suffix in suffixes:
            if not keyword.lower().endswith(suffix):
                variations.append(f"{keyword} {suffix}")
        
        # Variaciones long-tail
        long_tail_additions = ['paso a paso', 'para principiantes', 'casero', 'gratis', '2024']
        for addition in long_tail_additions:
            variations.append(f"{keyword} {addition}")
        
        return variations[:10]  # Limitar a 10 variaciones
    
    def _get_seo_recommendations(self, keyword: str, keyword_type: str, difficulty: str) -> List[str]:
        """Obtener recomendaciones SEO específicas"""
        recommendations = []
        
        if difficulty == "HIGH":
            recommendations.extend([
                "🔥 Keyword de alta competencia",
                "Considera usar variaciones long-tail",
                "Enfócate en crear contenido muy detallado y único",
                "Planifica una estrategia de link building"
            ])
        elif difficulty == "MEDIUM":
            recommendations.extend([
                "⚡ Keyword de competencia moderada",
                "Buen balance entre volumen y competencia",
                "Crea contenido de alta calidad y bien estructurado"
            ])
        else:
            recommendations.extend([
                "✅ Keyword de baja competencia",
                "Excelente oportunidad para posicionar",
                "Ideal para contenido especializado"
            ])
        
        if keyword_type == "informational":
            recommendations.append("📚 Enfócate en contenido educativo y detallado")
        elif keyword_type == "commercial":
            recommendations.append("💼 Incluye comparaciones y recomendaciones")
        elif keyword_type == "transactional":
            recommendations.append("🛒 Optimiza para conversión y llamadas a la acción")
        
        return recommendations
    
    def bulk_analyze_keywords(self, keywords: List[str]) -> Dict[str, any]:
        """Analizar múltiples keywords en lote"""
        results = {
            "total_keywords": len(keywords),
            "analysis_results": [],
            "summary": {
                "high_cannibalization_risk": 0,
                "medium_cannibalization_risk": 0,
                "low_cannibalization_risk": 0,
                "no_cannibalization_risk": 0,
                "average_seo_score": 0
            }
        }
        
        total_seo_score = 0
        
        for keyword in keywords:
            try:
                cannibalization_analysis = self.analyze_keyword_cannibalization(keyword)
                seo_analysis = self.analyze_keyword_seo_potential(keyword)
                
                combined_analysis = {
                    "keyword": keyword,
                    "cannibalization": cannibalization_analysis,
                    "seo_potential": seo_analysis
                }
                
                results["analysis_results"].append(combined_analysis)
                
                # Actualizar resumen
                risk_level = cannibalization_analysis["cannibalization_risk"]
                if risk_level == "HIGH":
                    results["summary"]["high_cannibalization_risk"] += 1
                elif risk_level == "MEDIUM":
                    results["summary"]["medium_cannibalization_risk"] += 1
                elif risk_level == "LOW":
                    results["summary"]["low_cannibalization_risk"] += 1
                else:
                    results["summary"]["no_cannibalization_risk"] += 1
                
                total_seo_score += seo_analysis["seo_score"]
                
            except Exception as e:
                logger.error(f"Error analizando keyword '{keyword}': {str(e)}")
                continue
        
        # Calcular promedio de SEO score
        if len(results["analysis_results"]) > 0:
            results["summary"]["average_seo_score"] = total_seo_score / len(results["analysis_results"])
        
        return results
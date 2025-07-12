from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.database import get_db
from app.services.keyword_analyzer import KeywordAnalyzer
from app.models.keyword import Keyword
from app.schemas.keyword import KeywordWithContent
from app.schemas.keyword_analysis import (
    KeywordAnalysisRequest,
    BulkKeywordAnalysisRequest,
    KeywordAnalysisResponse,
    SEOAnalysisResponse,
    BulkAnalysisResponse,
    SimilarityMatrixResponse,
    KeywordRecommendationsResponse
)
from app.api.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.post("/analyze-cannibalization", response_model=KeywordAnalysisResponse)
async def analyze_cannibalization(
    request: KeywordAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Analiza la canibalización de una keyword específica
    """
    try:
        keyword_analyzer = KeywordAnalyzer(db)
        result = keyword_analyzer.analyze_keyword_cannibalization(request.keyword)
        return {
            "keyword": request.keyword,
            "cannibalization_detected": result["cannibalization_risk"] in ["HIGH", "MEDIUM"],
            "similar_keywords": result["similar_keywords"],
            "recommendations": result["recommendations"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing cannibalization: {str(e)}"
        )

@router.post("/analyze-seo-potential", response_model=SEOAnalysisResponse)
async def analyze_seo_potential(
    request: KeywordAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Analiza el potencial SEO de una keyword
    """
    try:
        keyword_analyzer = KeywordAnalyzer(db)
        result = keyword_analyzer.analyze_keyword_seo_potential(request.keyword)
        return {
            "keyword": request.keyword,
            "seo_score": result["seo_score"],
            "difficulty": result["estimated_difficulty"],
            "search_volume_estimate": "N/A",  # No implementado aún
            "recommendations": result["recommendations"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing SEO potential: {str(e)}"
        )

@router.post("/bulk-analyze", response_model=BulkAnalysisResponse)
async def bulk_analyze_keywords(
    request: BulkKeywordAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Analiza múltiples keywords en lote
    """
    if len(request.keywords) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 keywords allowed per batch"
        )
    
    try:
        keyword_analyzer = KeywordAnalyzer(db)
        results = []
        
        for keyword in request.keywords:
            cannibalization_result = keyword_analyzer.analyze_keyword_cannibalization(keyword)
            seo_result = keyword_analyzer.analyze_keyword_seo_potential(keyword)
            
            results.append({
                "keyword": keyword,
                "seo_score": seo_result["seo_score"],
                "cannibalization_detected": cannibalization_result["cannibalization_risk"] in ["HIGH", "MEDIUM"],
                "difficulty": seo_result["estimated_difficulty"],
                "recommendations": seo_result["recommendations"]
            })
        
        return {
            "total_analyzed": len(request.keywords),
            "results": results,
            "summary": {
                "high_potential": len([r for r in results if r["seo_score"] > 7]),
                "medium_potential": len([r for r in results if 4 <= r["seo_score"] <= 7]),
                "low_potential": len([r for r in results if r["seo_score"] < 4]),
                "cannibalization_issues": len([r for r in results if r["cannibalization_detected"]])
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in bulk analysis: {str(e)}"
        )

@router.get("/similarity-matrix", response_model=SimilarityMatrixResponse)
async def get_similarity_matrix(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene una matriz de similitud entre todas las keywords
    """
    try:
        # Obtener todas las keywords activas
        keywords = db.query(Keyword).filter(Keyword.status != "used").all()
        keyword_texts = [k.keyword for k in keywords]
        
        if len(keyword_texts) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many keywords for similarity matrix. Maximum 100 allowed."
            )
        
        keyword_analyzer = KeywordAnalyzer(db)
        
        # Calcular matriz de similitud simple
        similarity_matrix = []
        for i, kw1 in enumerate(keyword_texts):
            row = []
            for j, kw2 in enumerate(keyword_texts):
                if i == j:
                    row.append(1.0)
                else:
                    similarity = keyword_analyzer._calculate_similarity(kw1, kw2)
                    row.append(similarity)
            similarity_matrix.append(row)
        
        # Encontrar pares con alta similitud
        high_similarity_pairs = []
        for i, kw1 in enumerate(keyword_texts):
            for j, kw2 in enumerate(keyword_texts[i+1:], i+1):
                similarity = similarity_matrix[i][j]
                if similarity > 0.8:
                    high_similarity_pairs.append({
                        "keyword1": kw1,
                        "keyword2": kw2,
                        "similarity": similarity
                    })
        
        return {
            "keywords": keyword_texts,
            "similarity_matrix": similarity_matrix,
            "high_similarity_pairs": high_similarity_pairs
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating similarity matrix: {str(e)}"
        )

@router.get("/recommendations/{keyword_id}", response_model=KeywordRecommendationsResponse)
async def get_keyword_recommendations(
    keyword_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene recomendaciones específicas para una keyword
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword not found"
        )
    
    try:
        keyword_analyzer = KeywordAnalyzer(db)
        
        # Obtener análisis completo
        cannibalization_result = keyword_analyzer.analyze_keyword_cannibalization(keyword.keyword)
        seo_result = keyword_analyzer.analyze_keyword_seo_potential(keyword.keyword)
        
        # Combinar recomendaciones
        recommendations = {
            "cannibalization": cannibalization_result["recommendations"],
            "seo": seo_result["recommendations"],
            "general": [
                f"Tipo de keyword: {seo_result['keyword_type']}",
                f"Dificultad estimada: {seo_result['estimated_difficulty']}",
                f"Riesgo de canibalización: {cannibalization_result['cannibalization_risk']}"
            ]
        }
        
        return {
            "keyword_id": keyword_id,
            "keyword": keyword.keyword,
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting recommendations: {str(e)}"
        )
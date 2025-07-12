from pydantic import BaseModel
from typing import List, Optional

class KeywordAnalysisRequest(BaseModel):
    keyword: str

class BulkKeywordAnalysisRequest(BaseModel):
    keywords: List[str]

class KeywordAnalysisResponse(BaseModel):
    keyword: str
    cannibalization_detected: bool
    similar_keywords: List[dict]
    recommendations: List[str]

class SEOAnalysisResponse(BaseModel):
    keyword: str
    seo_score: int
    difficulty: str
    search_volume_estimate: str
    recommendations: List[str]

class BulkAnalysisResponse(BaseModel):
    total_analyzed: int
    results: List[dict]
    summary: dict

class SimilarityMatrixResponse(BaseModel):
    keywords: List[str]
    similarity_matrix: List[List[float]]
    high_similarity_pairs: List[dict]

class KeywordRecommendationsResponse(BaseModel):
    keyword_id: int
    keyword: str
    recommendations: dict
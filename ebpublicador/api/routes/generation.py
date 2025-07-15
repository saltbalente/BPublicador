"""Content generation API routes."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from api.core.database import get_db
from api.models import GenerationHistory
from api.services import content_service, ContentRequest, AIProvider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generate", tags=["generation"])


# Pydantic models
from pydantic import BaseModel, Field

class GenerationRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    content_type: str = Field("blog_post", pattern="^(blog_post|article|social_post|email|landing_page)$")
    tone: str = Field("professional", pattern="^(professional|casual|friendly|formal|creative|persuasive)$")
    length: str = Field("medium", pattern="^(short|medium|long|very_long)$")
    language: str = Field("es", pattern="^(es|en|fr|de|it|pt)$")
    keywords: List[str] = Field(default_factory=list, max_items=10)
    target_audience: Optional[str] = Field(None, max_length=100)
    include_images: bool = True
    seo_optimized: bool = True
    provider: Optional[str] = Field(None, pattern="^(openai|gemini|fallback)$")

class TitleGenerationRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    count: int = Field(5, ge=1, le=20)
    tone: str = Field("professional", pattern="^(professional|casual|friendly|formal|creative|persuasive)$")
    language: str = Field("es", pattern="^(es|en|fr|de|it|pt)$")

class SEOAnalysisRequest(BaseModel):
    content: str = Field(..., min_length=10)
    target_keywords: List[str] = Field(..., min_items=1, max_items=10)

class GenerationResponse(BaseModel):
    id: Optional[int] = None
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
    created_at: Optional[datetime] = None

class TitleSuggestionsResponse(BaseModel):
    titles: List[str]
    topic: str
    generation_time: float

class SEOAnalysisResponse(BaseModel):
    word_count: int
    keyword_density: Dict[str, Dict[str, Any]]
    seo_score: float
    recommendations: List[str]
    analysis_time: float


@router.post("/content", response_model=GenerationResponse)
async def generate_content(
    request: GenerationRequest,
    save_history: bool = Query(True, description="Save generation to history"),
    db: Session = Depends(get_db)
):
    """Generate content using AI with specified parameters."""
    try:
        start_time = datetime.now()
        
        logger.info(
            f"Content generation requested - Topic: {request.topic}, "
            f"Type: {request.content_type}, Provider: {request.provider}"
        )
        
        # Create content request
        content_request = ContentRequest(
            topic=request.topic,
            content_type=request.content_type,
            tone=request.tone,
            length=request.length,
            language=request.language,
            keywords=request.keywords,
            target_audience=request.target_audience,
            include_images=request.include_images,
            seo_optimized=request.seo_optimized
        )
        
        # Determine AI provider
        preferred_provider = None
        if request.provider:
            try:
                preferred_provider = AIProvider(request.provider)
            except ValueError:
                logger.warning(f"Invalid AI provider: {request.provider}")
        
        # Generate content
        generated_content = await content_service.generate_content(
            content_request, preferred_provider
        )
        
        # Save to history if requested
        history_id = None
        if save_history:
            try:
                history = GenerationHistory(
                    topic=request.topic,
                    content_type=request.content_type,
                    provider=generated_content.provider,
                    parameters={
                        "tone": request.tone,
                        "length": request.length,
                        "language": request.language,
                        "keywords": request.keywords,
                        "target_audience": request.target_audience,
                        "seo_optimized": request.seo_optimized
                    },
                    result={
                        "title": generated_content.title,
                        "word_count": generated_content.word_count,
                        "generation_time": generated_content.generation_time,
                        "seo_score": generated_content.seo_score
                    },
                    generation_time=generated_content.generation_time
                )
                
                db.add(history)
                db.commit()
                db.refresh(history)
                history_id = history.id
                
                logger.info(f"Generation saved to history: {history_id}")
                
            except Exception as e:
                logger.warning(f"Could not save generation to history: {e}")
                # Don't fail the request if history saving fails
        
        # Prepare response
        response = GenerationResponse(
            id=history_id,
            title=generated_content.title,
            content=generated_content.content,
            summary=generated_content.summary,
            tags=generated_content.tags,
            meta_description=generated_content.meta_description,
            provider=generated_content.provider,
            generation_time=generated_content.generation_time,
            word_count=generated_content.word_count,
            images_suggested=generated_content.images_suggested,
            seo_score=generated_content.seo_score,
            created_at=datetime.now()
        )
        
        logger.info(
            f"Content generated successfully - Provider: {generated_content.provider}, "
            f"Words: {generated_content.word_count}, Time: {generated_content.generation_time:.2f}s"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Content generation failed: {str(e)}"
        )


@router.post("/titles", response_model=TitleSuggestionsResponse)
async def generate_title_suggestions(
    request: TitleGenerationRequest
):
    """Generate title suggestions for a given topic."""
    try:
        start_time = datetime.now()
        
        logger.info(f"Title generation requested - Topic: {request.topic}, Count: {request.count}")
        
        # Generate titles
        titles = await content_service.generate_title_suggestions(
            request.topic, request.count
        )
        
        generation_time = (datetime.now() - start_time).total_seconds()
        
        response = TitleSuggestionsResponse(
            titles=titles,
            topic=request.topic,
            generation_time=generation_time
        )
        
        logger.info(
            f"Title suggestions generated - Count: {len(titles)}, "
            f"Time: {generation_time:.2f}s"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Title generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Title generation failed: {str(e)}"
        )


@router.post("/seo-analysis", response_model=SEOAnalysisResponse)
async def analyze_seo(
    request: SEOAnalysisRequest
):
    """Analyze content for SEO optimization."""
    try:
        start_time = datetime.now()
        
        logger.info(
            f"SEO analysis requested - Content length: {len(request.content)}, "
            f"Keywords: {len(request.target_keywords)}"
        )
        
        # Perform SEO analysis
        seo_analysis = await content_service.optimize_content_for_seo(
            request.content, request.target_keywords
        )
        
        analysis_time = (datetime.now() - start_time).total_seconds()
        
        response = SEOAnalysisResponse(
            word_count=seo_analysis["word_count"],
            keyword_density=seo_analysis["keyword_density"],
            seo_score=seo_analysis["seo_score"],
            recommendations=seo_analysis["recommendations"],
            analysis_time=analysis_time
        )
        
        logger.info(
            f"SEO analysis completed - Score: {seo_analysis['seo_score']:.1f}, "
            f"Time: {analysis_time:.2f}s"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"SEO analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"SEO analysis failed: {str(e)}"
        )


@router.get("/history")
async def get_generation_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    content_type: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get generation history with pagination and filtering."""
    try:
        # Build query
        query = db.query(GenerationHistory)
        
        # Apply filters
        if content_type:
            query = query.filter(GenerationHistory.content_type == content_type)
        
        if provider:
            query = query.filter(GenerationHistory.provider == provider)
        
        # Order by creation date (newest first)
        query = query.order_by(GenerationHistory.created_at.desc())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        history_items = query.offset(offset).limit(per_page).all()
        
        # Prepare response
        items = []
        for item in history_items:
            items.append({
                "id": item.id,
                "topic": item.topic,
                "content_type": item.content_type,
                "provider": item.provider,
                "parameters": item.parameters,
                "result": item.result,
                "generation_time": item.generation_time,
                "created_at": item.created_at
            })
        
        total_pages = (total + per_page - 1) // per_page
        
        return JSONResponse(
            content={
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting generation history: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving generation history")


@router.get("/history/{history_id}")
async def get_generation_detail(
    history_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific generation."""
    try:
        history = db.query(GenerationHistory).filter(
            GenerationHistory.id == history_id
        ).first()
        
        if not history:
            raise HTTPException(status_code=404, detail="Generation not found")
        
        return JSONResponse(
            content={
                "id": history.id,
                "topic": history.topic,
                "content_type": history.content_type,
                "provider": history.provider,
                "parameters": history.parameters,
                "result": history.result,
                "generation_time": history.generation_time,
                "created_at": history.created_at
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting generation detail {history_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving generation detail")


@router.delete("/history/{history_id}")
async def delete_generation_history(
    history_id: int,
    db: Session = Depends(get_db)
):
    """Delete a generation from history."""
    try:
        history = db.query(GenerationHistory).filter(
            GenerationHistory.id == history_id
        ).first()
        
        if not history:
            raise HTTPException(status_code=404, detail="Generation not found")
        
        db.delete(history)
        db.commit()
        
        logger.info(f"Generation history deleted: {history_id}")
        
        return JSONResponse(
            status_code=200,
            content={"message": "Generation deleted successfully"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting generation history {history_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting generation")


@router.get("/providers")
async def get_available_providers():
    """Get list of available AI providers and their status."""
    try:
        providers_status = []
        
        # Check each provider
        for provider in AIProvider:
            if provider == AIProvider.FALLBACK:
                status = "available"
                description = "Fallback provider (always available)"
            else:
                # Check if provider is configured
                if provider in content_service.providers:
                    status = "available"
                    description = f"{provider.value.title()} provider configured"
                else:
                    status = "unavailable"
                    description = f"{provider.value.title()} provider not configured"
            
            providers_status.append({
                "name": provider.value,
                "status": status,
                "description": description,
                "is_default": provider == content_service.default_provider
            })
        
        return JSONResponse(
            content={
                "providers": providers_status,
                "default_provider": content_service.default_provider.value
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting providers status: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving providers status")


@router.get("/stats")
async def get_generation_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get generation statistics for the specified period."""
    try:
        from sqlalchemy import func
        from datetime import timedelta
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get basic stats
        total_generations = db.query(GenerationHistory).filter(
            GenerationHistory.created_at >= start_date
        ).count()
        
        # Get stats by provider
        provider_stats = db.query(
            GenerationHistory.provider,
            func.count(GenerationHistory.id).label('count'),
            func.avg(GenerationHistory.generation_time).label('avg_time')
        ).filter(
            GenerationHistory.created_at >= start_date
        ).group_by(GenerationHistory.provider).all()
        
        # Get stats by content type
        content_type_stats = db.query(
            GenerationHistory.content_type,
            func.count(GenerationHistory.id).label('count')
        ).filter(
            GenerationHistory.created_at >= start_date
        ).group_by(GenerationHistory.content_type).all()
        
        # Get daily generation counts
        daily_stats = db.query(
            func.date(GenerationHistory.created_at).label('date'),
            func.count(GenerationHistory.id).label('count')
        ).filter(
            GenerationHistory.created_at >= start_date
        ).group_by(
            func.date(GenerationHistory.created_at)
        ).order_by(
            func.date(GenerationHistory.created_at)
        ).all()
        
        return JSONResponse(
            content={
                "period_days": days,
                "total_generations": total_generations,
                "provider_stats": [
                    {
                        "provider": stat.provider,
                        "count": stat.count,
                        "avg_generation_time": round(float(stat.avg_time or 0), 2)
                    }
                    for stat in provider_stats
                ],
                "content_type_stats": [
                    {
                        "content_type": stat.content_type,
                        "count": stat.count
                    }
                    for stat in content_type_stats
                ],
                "daily_stats": [
                    {
                        "date": stat.date.isoformat(),
                        "count": stat.count
                    }
                    for stat in daily_stats
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting generation stats: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving generation statistics")
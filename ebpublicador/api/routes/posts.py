"""Posts API routes for content management."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Form, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, or_

from api.core.database import get_db
from api.models import Post, PostImage, PostTag
from api.services import content_service, storage_service, ContentRequest, AIProvider, StorageType
from api.middleware import cloud_error_handler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/posts", tags=["posts"])


# Pydantic models for request/response
from pydantic import BaseModel, Field
from typing import Union

class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: Optional[str] = None
    summary: Optional[str] = None
    meta_description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    theme_id: Optional[int] = None
    is_published: bool = False
    generate_with_ai: bool = False
    ai_topic: Optional[str] = None
    ai_tone: str = "professional"
    ai_length: str = "medium"
    ai_keywords: List[str] = Field(default_factory=list)
    ai_provider: Optional[str] = None

class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    summary: Optional[str] = None
    meta_description: Optional[str] = None
    tags: Optional[List[str]] = None
    theme_id: Optional[int] = None
    is_published: Optional[bool] = None

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    summary: Optional[str]
    meta_description: Optional[str]
    tags: List[str]
    theme_id: Optional[int]
    is_published: bool
    created_at: datetime
    updated_at: datetime
    images: List[Dict[str, Any]] = Field(default_factory=list)
    word_count: int
    reading_time: int

    class Config:
        from_attributes = True

class PostListResponse(BaseModel):
    posts: List[PostResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


@router.get("/", response_model=PostListResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    published_only: bool = Query(False),
    tag: Optional[str] = Query(None),
    sort_by: str = Query("created_at", pattern="^(created_at|updated_at|title)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """List posts with filtering and pagination."""
    try:
        # Build query
        query = db.query(Post)
        
        # Apply filters
        if published_only:
            query = query.filter(Post.is_published == True)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Post.title.ilike(search_term),
                    Post.content.ilike(search_term),
                    Post.summary.ilike(search_term)
                )
            )
        
        if tag:
            query = query.join(PostTag).filter(PostTag.name == tag)
        
        # Apply sorting
        sort_column = getattr(Post, sort_by)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        posts = query.offset(offset).limit(per_page).all()
        
        # Convert to response format
        post_responses = []
        for post in posts:
            post_dict = {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "summary": post.summary,
                "meta_description": post.meta_description,
                "tags": [tag.name for tag in post.tags],
                "theme_id": post.theme_id,
                "is_published": post.is_published,
                "created_at": post.created_at,
                "updated_at": post.updated_at,
                "images": [
                    {
                        "id": img.id,
                        "filename": img.filename,
                        "url": img.url,
                        "alt_text": img.alt_text
                    } for img in post.images
                ],
                "word_count": len(post.content.split()) if post.content else 0,
                "reading_time": max(1, len(post.content.split()) // 200) if post.content else 1
            }
            post_responses.append(PostResponse(**post_dict))
        
        total_pages = (total + per_page - 1) // per_page
        
        return PostListResponse(
            posts=post_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error listing posts: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving posts")


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    """Get a specific post by ID."""
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        post_dict = {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "summary": post.summary,
            "meta_description": post.meta_description,
            "tags": [tag.name for tag in post.tags],
            "theme_id": post.theme_id,
            "is_published": post.is_published,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "images": [
                {
                    "id": img.id,
                    "filename": img.filename,
                    "url": img.url,
                    "alt_text": img.alt_text
                } for img in post.images
            ],
            "word_count": len(post.content.split()) if post.content else 0,
            "reading_time": max(1, len(post.content.split()) // 200) if post.content else 1
        }
        
        return PostResponse(**post_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting post {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving post")


@router.post("/", response_model=PostResponse)
async def create_post(post_data: PostCreate, db: Session = Depends(get_db)):
    """Create a new post, optionally with AI generation."""
    try:
        # If AI generation is requested
        if post_data.generate_with_ai and post_data.ai_topic:
            logger.info(f"Generating AI content for topic: {post_data.ai_topic}")
            
            # Prepare AI request
            ai_request = ContentRequest(
                topic=post_data.ai_topic,
                tone=post_data.ai_tone,
                length=post_data.ai_length,
                keywords=post_data.ai_keywords,
                language="es",
                seo_optimized=True
            )
            
            # Determine AI provider
            preferred_provider = None
            if post_data.ai_provider:
                try:
                    preferred_provider = AIProvider(post_data.ai_provider)
                except ValueError:
                    logger.warning(f"Invalid AI provider: {post_data.ai_provider}")
            
            # Generate content
            try:
                generated_content = await content_service.generate_content(
                    ai_request, preferred_provider
                )
                
                # Use generated content
                title = post_data.title or generated_content.title
                content = generated_content.content
                summary = post_data.summary or generated_content.summary
                meta_description = post_data.meta_description or generated_content.meta_description
                ai_tags = generated_content.tags
                
                logger.info(
                    f"AI content generated successfully with {generated_content.provider} "
                    f"({generated_content.word_count} words)"
                )
                
            except Exception as ai_error:
                logger.error(f"AI content generation failed: {ai_error}")
                # Fall back to manual content
                title = post_data.title or f"Artículo sobre {post_data.ai_topic}"
                content = post_data.content or f"Contenido sobre {post_data.ai_topic}"
                summary = post_data.summary
                meta_description = post_data.meta_description
                ai_tags = []
        else:
            # Use provided content
            title = post_data.title
            content = post_data.content or ""
            summary = post_data.summary
            meta_description = post_data.meta_description
            ai_tags = []
        
        # Create post
        post = Post(
            title=title,
            content=content,
            summary=summary,
            meta_description=meta_description,
            theme_id=post_data.theme_id,
            is_published=post_data.is_published
        )
        
        db.add(post)
        db.flush()  # Get the post ID
        
        # Add tags
        all_tags = list(set(post_data.tags + ai_tags))  # Remove duplicates
        for tag_name in all_tags:
            if tag_name.strip():
                # Check if tag exists
                existing_tag = db.query(PostTag).filter(PostTag.name == tag_name.strip()).first()
                if not existing_tag:
                    tag = PostTag(name=tag_name.strip(), post_id=post.id)
                    db.add(tag)
                else:
                    existing_tag.post_id = post.id
        
        db.commit()
        db.refresh(post)
        
        # Prepare response
        post_dict = {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "summary": post.summary,
            "meta_description": post.meta_description,
            "tags": [tag.name for tag in post.tags],
            "theme_id": post.theme_id,
            "is_published": post.is_published,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "images": [],
            "word_count": len(post.content.split()) if post.content else 0,
            "reading_time": max(1, len(post.content.split()) // 200) if post.content else 1
        }
        
        logger.info(f"Post created successfully: {post.id}")
        return PostResponse(**post_dict)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating post: {e}")
        raise HTTPException(status_code=500, detail="Error creating post")


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int, 
    post_data: PostUpdate, 
    db: Session = Depends(get_db)
):
    """Update an existing post."""
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Update fields
        update_data = post_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "tags":
                # Handle tags separately
                continue
            setattr(post, field, value)
        
        # Update tags if provided
        if post_data.tags is not None:
            # Remove existing tags
            db.query(PostTag).filter(PostTag.post_id == post_id).delete()
            
            # Add new tags
            for tag_name in post_data.tags:
                if tag_name.strip():
                    tag = PostTag(name=tag_name.strip(), post_id=post_id)
                    db.add(tag)
        
        post.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(post)
        
        # Prepare response
        post_dict = {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "summary": post.summary,
            "meta_description": post.meta_description,
            "tags": [tag.name for tag in post.tags],
            "theme_id": post.theme_id,
            "is_published": post.is_published,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "images": [
                {
                    "id": img.id,
                    "filename": img.filename,
                    "url": img.url,
                    "alt_text": img.alt_text
                } for img in post.images
            ],
            "word_count": len(post.content.split()) if post.content else 0,
            "reading_time": max(1, len(post.content.split()) // 200) if post.content else 1
        }
        
        logger.info(f"Post updated successfully: {post_id}")
        return PostResponse(**post_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating post {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Error updating post")


@router.delete("/{post_id}")
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    """Delete a post and its associated data."""
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Delete associated images from storage
        for image in post.images:
            try:
                await storage_service.delete_file(image.filename, StorageType.UPLOADS)
            except Exception as e:
                logger.warning(f"Could not delete image file {image.filename}: {e}")
        
        # Delete from database (cascade will handle tags and images)
        db.delete(post)
        db.commit()
        
        logger.info(f"Post deleted successfully: {post_id}")
        return JSONResponse(
            status_code=200,
            content={"message": "Post deleted successfully"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting post {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting post")


@router.post("/{post_id}/images")
async def upload_post_image(
    post_id: int,
    file: UploadFile = File(...),
    alt_text: str = Form(""),
    db: Session = Depends(get_db)
):
    """Upload an image for a post."""
    try:
        # Check if post exists
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Validate file type
        if not storage_service.is_image_file(file.filename):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Upload file
        upload_result = await storage_service.upload_file(
            file.file, file.filename, StorageType.UPLOADS
        )
        
        if not upload_result.success:
            raise HTTPException(status_code=400, detail=upload_result.error)
        
        # Create image record
        image = PostImage(
            post_id=post_id,
            filename=upload_result.file_info.filename,
            url=upload_result.file_info.url_path,
            alt_text=alt_text or f"Image for {post.title}"
        )
        
        db.add(image)
        db.commit()
        db.refresh(image)
        
        logger.info(f"Image uploaded for post {post_id}: {image.filename}")
        
        return JSONResponse(
            status_code=201,
            content={
                "id": image.id,
                "filename": image.filename,
                "url": image.url,
                "alt_text": image.alt_text,
                "fallback_used": upload_result.fallback_used
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading image for post {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Error uploading image")


@router.delete("/{post_id}/images/{image_id}")
async def delete_post_image(
    post_id: int,
    image_id: int,
    db: Session = Depends(get_db)
):
    """Delete an image from a post."""
    try:
        image = db.query(PostImage).filter(
            and_(PostImage.id == image_id, PostImage.post_id == post_id)
        ).first()
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Delete file from storage
        try:
            await storage_service.delete_file(image.filename, StorageType.UPLOADS)
        except Exception as e:
            logger.warning(f"Could not delete image file {image.filename}: {e}")
        
        # Delete from database
        db.delete(image)
        db.commit()
        
        logger.info(f"Image deleted from post {post_id}: {image_id}")
        
        return JSONResponse(
            status_code=200,
            content={"message": "Image deleted successfully"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting image {image_id} from post {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting image")


@router.get("/tags/popular")
async def get_popular_tags(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get most popular tags."""
    try:
        from sqlalchemy import func
        
        tags = db.query(
            PostTag.name,
            func.count(PostTag.id).label('count')
        ).group_by(PostTag.name).order_by(
            func.count(PostTag.id).desc()
        ).limit(limit).all()
        
        return JSONResponse(
            content={
                "tags": [
                    {"name": tag.name, "count": tag.count}
                    for tag in tags
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting popular tags: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving tags")
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.services.image_generator import ImageGenerator
from app.models.content import Content
from app.models.content_image import ContentImage
from app.models.image_config import ImageConfig, ImageStyle, ImageQuality, ImageSize, ImagePlacement, ImageProvider, GeminiAspectRatio, GeminiSafetyLevel
from app.api.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.models.manual_image import ManualImage
from pydantic import BaseModel
import os
import uuid
from PIL import Image
import shutil
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ImageGenerationRequest(BaseModel):
    prompt: str
    style: Optional[str] = "realistic"
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = "standard"

class BulkImageRequest(BaseModel):
    prompts: List[str]
    style: Optional[str] = "realistic"
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = "standard"

class ContentImageRequest(BaseModel):
    content_id: int
    num_images: Optional[int] = 3
    style: Optional[str] = "realistic"
    include_featured: Optional[bool] = True

class ImageConfigRequest(BaseModel):
    imagesPerContent: int = 2
    imageSize: str = "1024x1024"
    imageQuality: str = "standard"
    imagePlacement: str = "middle"
    imageStyle: str = "realistic"
    autoGenerateImages: bool = True
    includeFeaturedImage: bool = True
    imageProvider: str = "gemini"
    geminiAspectRatio: str = "1:1"
    geminiSafetyLevel: str = "BLOCK_MEDIUM_AND_ABOVE"
    geminiPersonGeneration: bool = True

class KeywordImageConfigRequest(BaseModel):
    keyword_id: int
    prompt: Optional[str] = None
    style: Optional[str] = None
    count: Optional[int] = None

class ManualImageGenerationRequest(BaseModel):
    keyword_id: int
    prompt: str
    count: int = 1
    style: Optional[str] = "realistic"
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = "standard"

class DalleImageRequest(BaseModel):
    prompt: str
    size: Optional[str] = "1024x1024"
    quality: Optional[str] = "standard"

@router.post("/generate", response_model=None)
async def generate_image(
    request: ImageGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Genera una imagen usando IA
    """
    try:
        image_generator = ImageGenerator(db)
        if not image_generator.openai_client and not image_generator.gemini_client:
            raise HTTPException(status_code=400, detail="No image generation API configured. Please set OpenAI or Gemini API key in settings.")
        
        result = image_generator.generate_image(
            prompt=request.prompt,
            style=request.style,
            size=request.size,
            quality=request.quality
        )
        return {
            "success": True,
            "image_url": result["image_url"],
            "image_path": result["image_path"],
            "prompt_used": request.prompt,
            "alt_text": result["alt_text"]
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating image: {str(e)}"
        )

@router.post("/generate-for-content", response_model=None)
async def generate_images_for_content(
    request: ContentImageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Genera imágenes específicas para un contenido
    """
    # Verificar que el contenido existe
    content = db.query(Content).filter(Content.id == request.content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Verificar que el usuario tiene acceso al contenido
    if content.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate images for this content"
        )
    
    try:
        image_generator = ImageGenerator(db)
        result = await image_generator.generate_images_for_content(
            content_id=request.content_id,
            num_images=request.num_images,
            style=request.style,
            include_featured=request.include_featured,
            db=db
        )
        return {
            "success": True,
            "content_id": request.content_id,
            "images_generated": len(result["images"]),
            "images": result["images"],
            "featured_image": result.get("featured_image")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating images for content: {str(e)}"
        )

@router.post("/bulk-generate", response_model=None)
async def bulk_generate_images(
    request: BulkImageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Genera múltiples imágenes en lote
    """
    if len(request.prompts) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 images allowed per batch"
        )
    
    try:
        image_generator = ImageGenerator(db)
        if not image_generator.openai_client and not image_generator.gemini_client:
            raise HTTPException(status_code=400, detail="No image generation API configured. Please set OpenAI or Gemini API key in settings.")
        
        results = {
            "images": [],
            "failed": []
        }
        
        for prompt in request.prompts:
            try:
                image = image_generator.generate_image(
                    prompt=prompt,
                    style=request.style,
                    size=request.size,
                    quality=request.quality
                )
                results["images"].append(image)
            except Exception as e:
                results["failed"].append({"prompt": prompt, "error": str(e)})
        
        return {
            "success": True,
            "total_generated": len(results["images"]),
            "images": results["images"],
            "failed": results["failed"]
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in bulk image generation: {str(e)}"
        )

@router.get("/content/{content_id}/images", response_model=None)
async def get_content_images(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene todas las imágenes de un contenido
    """
    # Verificar que el contenido existe
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found"
        )
    
    # Verificar acceso
    if content.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this content's images"
        )
    
    images = db.query(ContentImage).filter(
        ContentImage.content_id == content_id
    ).order_by(ContentImage.position).all()
    
    return {
        "content_id": content_id,
        "total_images": len(images),
        "images": [
            {
                "id": img.id,
                "image_path": img.image_path,
                "alt_text": img.alt_text,
                "position": img.position,
                "is_featured": img.is_featured,
                "prompt_used": img.prompt_used,
                "created_at": img.created_at
            }
            for img in images
        ]
    }

@router.delete("/images/{image_id}", response_model=None)
async def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Elimina una imagen
    """
    image = db.query(ContentImage).filter(ContentImage.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Verificar acceso a través del contenido
    content = db.query(Content).filter(Content.id == image.content_id).first()
    if content.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this image"
        )
    
    try:
        # Eliminar archivo físico
        image_generator = ImageGenerator(db)
        await image_generator.delete_image(image.image_path)
        
        # Eliminar de la base de datos
        db.delete(image)
        db.commit()
        
        return {"success": True, "message": "Image deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting image: {str(e)}"
        )

@router.get("/stats", response_model=None)
async def get_image_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene estadísticas de generación de imágenes
    """
    try:
        image_generator = ImageGenerator(db)
        stats = await image_generator.get_image_stats(db, current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting image stats: {str(e)}"
        )

@router.post("/optimize-alt-text/{image_id}", response_model=None)
async def optimize_alt_text(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Optimiza el texto alternativo de una imagen usando IA
    """
    image = db.query(ContentImage).filter(ContentImage.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Verificar acceso
    content = db.query(Content).filter(Content.id == image.content_id).first()
    if content.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this image"
        )
    
    try:
        image_generator = ImageGenerator(db)
        optimized_alt = await image_generator.generate_alt_text(
            image.image_path, content.title, content.keyword.keyword if content.keyword else None
        )
        
        # Actualizar en la base de datos
        image.alt_text = optimized_alt
        db.commit()
        
        return {
            "success": True,
            "image_id": image_id,
            "optimized_alt_text": optimized_alt
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error optimizing alt text: {str(e)}"
        )

@router.post("/config", response_model=None)
async def save_image_config(
    request: ImageConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Guarda la configuración global de imágenes
    """
    try:
        # Buscar configuración global existente (keyword_id = None)
        existing_config = db.query(ImageConfig).filter(
            ImageConfig.user_id == current_user.id,
            ImageConfig.keyword_id.is_(None)
        ).first()
        
        if existing_config:
            # Actualizar configuración existente
            existing_config.num_images = request.imagesPerContent
            existing_config.image_size = ImageSize(request.imageSize)
            existing_config.image_quality = ImageQuality(request.imageQuality)
            existing_config.image_placement = ImagePlacement(request.imagePlacement)
            existing_config.style = ImageStyle(request.imageStyle)
            existing_config.auto_generate = request.autoGenerateImages
            existing_config.include_featured = request.includeFeaturedImage
            existing_config.image_provider = ImageProvider(request.imageProvider)
            existing_config.gemini_aspect_ratio = GeminiAspectRatio(request.geminiAspectRatio)
            existing_config.gemini_safety_level = GeminiSafetyLevel(request.geminiSafetyLevel)
            existing_config.gemini_person_generation = request.geminiPersonGeneration
        else:
            # Crear nueva configuración
            new_config = ImageConfig(
                user_id=current_user.id,
                keyword_id=None,  # Configuración global
                num_images=request.imagesPerContent,
                image_size=ImageSize(request.imageSize),
                image_quality=ImageQuality(request.imageQuality),
                image_placement=ImagePlacement(request.imagePlacement),
                style=ImageStyle(request.imageStyle),
                auto_generate=request.autoGenerateImages,
                include_featured=request.includeFeaturedImage,
                image_provider=ImageProvider(request.imageProvider),
                gemini_aspect_ratio=GeminiAspectRatio(request.geminiAspectRatio),
                gemini_safety_level=GeminiSafetyLevel(request.geminiSafetyLevel),
                gemini_person_generation=request.geminiPersonGeneration
            )
            db.add(new_config)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Configuración guardada exitosamente",
            "config": request.dict()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving image config: {str(e)}"
        )

@router.get("/config", response_model=None)
async def get_image_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene la configuración global de imágenes
    """
    try:
        # Buscar configuración global del usuario
        config = db.query(ImageConfig).filter(
            ImageConfig.user_id == current_user.id,
            ImageConfig.keyword_id.is_(None)
        ).first()
        
        if config:
            return {
                "imagesPerContent": config.num_images,
                "imageSize": config.image_size.value,
                "imageQuality": config.image_quality.value,
                "imagePlacement": config.image_placement.value,
                "imageStyle": config.style.value,
                "autoGenerateImages": config.auto_generate,
                "includeFeaturedImage": config.include_featured,
                "imageProvider": config.image_provider.value,
                "geminiAspectRatio": config.gemini_aspect_ratio.value,
                "geminiSafetyLevel": config.gemini_safety_level.value,
                "geminiPersonGeneration": config.gemini_person_generation
            }
        else:
            # Configuración por defecto si no existe
            return {
                "imagesPerContent": 2,
                "imageSize": "1024x1024",
                "imageQuality": "standard",
                "imagePlacement": "middle",
                "imageStyle": "mystical",
                "autoGenerateImages": True,
                "includeFeaturedImage": True,
                "imageProvider": "gemini",
                "geminiAspectRatio": "1:1",
                "geminiSafetyLevel": "BLOCK_MEDIUM_AND_ABOVE",
                "geminiPersonGeneration": False
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting image config: {str(e)}"
        )

@router.post("/keyword-config", response_model=None)
async def save_keyword_image_config(
    request: KeywordImageConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Guarda la configuración de imágenes específica para una keyword
    """
    try:
        # Verificar que la keyword existe
        from app.models.keyword import Keyword
        keyword = db.query(Keyword).filter(
            Keyword.id == request.keyword_id
        ).first()
        
        if not keyword:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Keyword not found"
            )
        
        # Buscar configuración existente para esta keyword
        existing_config = db.query(ImageConfig).filter(
            ImageConfig.user_id == current_user.id,
            ImageConfig.keyword_id == request.keyword_id
        ).first()
        
        if existing_config:
            # Actualizar configuración existente
            if request.prompt is not None:
                existing_config.custom_prompt = request.prompt
            if request.style is not None:
                existing_config.custom_style = ImageStyle(request.style)
            if request.count is not None:
                existing_config.custom_count = request.count
        else:
            # Crear nueva configuración para keyword
            new_config = ImageConfig(
                user_id=current_user.id,
                keyword_id=request.keyword_id,
                custom_prompt=request.prompt,
                custom_style=ImageStyle(request.style) if request.style else None,
                custom_count=request.count
            )
            db.add(new_config)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Configuración de keyword guardada exitosamente",
            "keyword_id": request.keyword_id,
            "config": request.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving keyword image config: {str(e)}"
        )

@router.get("/keyword-configs", response_model=None)
async def get_keyword_image_configs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene todas las configuraciones de imágenes por keyword
    """
    try:
        # Obtener todas las configuraciones de keywords del usuario
        configs = db.query(ImageConfig).filter(
            ImageConfig.user_id == current_user.id,
            ImageConfig.keyword_id.isnot(None)
        ).all()
        
        result = {}
        for config in configs:
            result[str(config.keyword_id)] = {
                "prompt": config.custom_prompt,
                "style": config.custom_style.value if config.custom_style else None,
                "count": config.custom_count
            }
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting keyword image configs: {str(e)}"
        )

@router.get("/images", response_model=None)
async def get_all_images(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene todas las imágenes del usuario (contenido + manuales)
    """
    try:
        from app.models.keyword import Keyword
        from app.models.manual_image import ManualImage
        import os
        
        # Obtener imágenes de contenido
        content_images_query = db.query(ContentImage).join(
            Content, ContentImage.content_id == Content.id
        ).filter(
            Content.user_id == current_user.id
        )
        
        # Obtener imágenes manuales
        manual_images_query = db.query(ManualImage).filter(
            ManualImage.user_id == current_user.id
        )
        
        # Contar totales
        total_content = content_images_query.count()
        total_manual = manual_images_query.count()
        total = total_content + total_manual
        
        # Obtener imágenes con paginación
        content_images = content_images_query.order_by(ContentImage.created_at.desc()).all()
        manual_images = manual_images_query.order_by(ManualImage.created_at.desc()).all()
        
        # Combinar y ordenar por fecha
        all_images = []
        
        # Agregar imágenes de contenido
        for img in content_images:
            # Verificar si el archivo existe
            file_exists = os.path.exists(img.image_path) if img.image_path else False
            
            all_images.append({
                "id": f"content_{img.id}",
                "type": "content",
                "image_path": img.image_path,
                "file_exists": file_exists,
                "alt_text": img.alt_text,
                "position": img.position,
                "is_featured": img.is_featured,
                "prompt_used": img.prompt_used,
                "created_at": img.created_at,
                "content_id": img.content_id,
                "content_title": img.content.title if img.content else None
            })
        
        # Agregar imágenes manuales
        for img in manual_images:
            # Verificar si el archivo existe
            file_exists = os.path.exists(img.image_path) if img.image_path else False
            
            all_images.append({
                "id": f"manual_{img.id}",
                "type": "manual",
                "image_path": img.image_path,
                "file_exists": file_exists,
                "alt_text": img.alt_text,
                "prompt_used": img.prompt_used,
                "style": img.style,
                "size": img.size,
                "quality": img.quality,
                "created_at": img.created_at,
                "keyword_id": img.keyword_id,
                "keyword_name": img.keyword.keyword if img.keyword else None
            })
        
        # Ordenar por fecha de creación (más recientes primero)
        all_images.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Aplicar paginación
        paginated_images = all_images[offset:offset + limit]
        
        # Debug: Log the image paths
        logger.info(f"Found {len(paginated_images)} images for user {current_user.id}")
        for img in paginated_images:
            logger.info(f"Image: {img['id']}, Type: {img['type']}, Path: {img['image_path']}, Exists: {img['file_exists']}")
        
        return {
            "total": total,
            "total_content_images": total_content,
            "total_manual_images": total_manual,
            "images": paginated_images
        }
    except Exception as e:
        logger.error(f"Error getting images: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting images: {str(e)}"
        )

@router.get("/manual-images/{filename}", response_class=FileResponse)
async def get_manual_image(
    filename: str,
    db: Session = Depends(get_db)
):
    """
    Sirve una imagen manual específica
    """
    try:
        logger.info(f"Serving manual image: {filename}")
        
        # Buscar la imagen en la base de datos
        manual_image = db.query(ManualImage).filter(
            ManualImage.image_path.like(f"%{filename}%")
        ).first()
        
        if not manual_image:
            logger.error(f"Manual image not found in database: {filename}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )
        
        logger.info(f"Found manual image in database: {manual_image.image_path}")
        
        # Verificar que el archivo existe
        if not os.path.exists(manual_image.image_path):
            logger.error(f"Manual image file not found on disk: {manual_image.image_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image file not found on disk"
            )
        
        logger.info(f"Serving manual image file: {manual_image.image_path}")
        
        return FileResponse(
            path=manual_image.image_path,
            media_type="image/*",
            filename=filename
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error serving manual image {filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error serving image: {str(e)}"
        )

@router.post("/generate-manual", response_model=None)
async def generate_manual_images(
    request: ManualImageGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Genera imágenes manualmente basadas en una keyword y prompt
    """
    try:
        # Verificar que la keyword existe
        from app.models.keyword import Keyword
        keyword = db.query(Keyword).filter(
            Keyword.id == request.keyword_id
        ).first()
        
        if not keyword:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Keyword not found"
            )
        
        if request.count > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 5 images allowed per manual generation"
            )
        
        image_generator = ImageGenerator(db)
        if not image_generator.openai_client and not image_generator.gemini_client:
            raise HTTPException(status_code=400, detail="No image generation API configured. Please set OpenAI or Gemini API key in settings.")
        
        results = []
        
        for i in range(request.count):
            prompt_with_keyword = f"{request.prompt} related to {keyword.keyword}"
            result = image_generator.generate_manual_image(
                prompt=prompt_with_keyword,
                user_id=current_user.id,
                keyword_id=request.keyword_id,
                style=request.style,
                size=request.size,
                quality=request.quality
            )
            results.append(result)
        
        return {
            "success": True,
            "keyword_id": request.keyword_id,
            "images_generated": len(results),
            "images": results
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating manual images: {str(e)}"
        )

@router.post("/upload-manual", response_model=None)
async def upload_manual_image(
    file: UploadFile = File(...),
    keyword_id: int = None,
    alt_text: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Sube una imagen manual desde un archivo local
    """
    try:
        # Validar tipo de archivo
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Validar tamaño de archivo (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size must be less than 10MB"
            )
        
        # Verificar keyword si se proporciona
        keyword = None
        if keyword_id:
            from app.models.keyword import Keyword
            keyword = db.query(Keyword).filter(
                Keyword.id == keyword_id
            ).first()
            
            if not keyword:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Keyword not found"
                )
        
        # Crear directorio de imágenes si no existe - usar path seguro para Railway
        upload_dir = os.environ.get("MANUAL_IMAGES_PATH", 
                                   os.path.join(os.path.dirname(__file__), "..", "..", "..", "storage", "images", "manual"))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generar nombre único para el archivo
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Guardar archivo
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Procesar imagen con PIL para obtener información
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                image_size = f"{width}x{height}"
        except Exception:
            image_size = "unknown"
        
        # Generar alt_text automático si no se proporciona
        if not alt_text:
            if keyword:
                alt_text = f"Image related to {keyword.keyword}"
            else:
                alt_text = f"Uploaded image - {file.filename}"
        
        # Crear registro en la base de datos
        manual_image = ManualImage(
            user_id=current_user.id,
            keyword_id=keyword_id,
            image_path=file_path,
            alt_text=alt_text,
            prompt_used=f"Manual upload: {file.filename}",
            style="uploaded",
            size=image_size,
            quality="original"
        )
        
        db.add(manual_image)
        db.commit()
        db.refresh(manual_image)
        
        return {
            "success": True,
            "image_id": manual_image.id,
            "image_path": manual_image.image_path,
            "alt_text": manual_image.alt_text,
            "size": image_size,
            "keyword_id": keyword_id,
            "keyword_name": keyword.keyword if keyword else None,
            "message": "Image uploaded successfully"
        }
        
    except HTTPException as he:
        # Limpiar archivo si hubo error
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise he
    except Exception as e:
        # Limpiar archivo si hubo error
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading image: {str(e)}"
        )

@router.delete("/manual/{image_id}", response_model=None)
async def delete_manual_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Elimina una imagen manual
    """
    try:
        # Buscar la imagen
        manual_image = db.query(ManualImage).filter(
            ManualImage.id == image_id,
            ManualImage.user_id == current_user.id
        ).first()
        
        if not manual_image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Manual image not found"
            )
        
        # Eliminar archivo físico
        if os.path.exists(manual_image.image_path):
            os.remove(manual_image.image_path)
        
        # Eliminar registro de la base de datos
        db.delete(manual_image)
        db.commit()
        
        return {
            "success": True,
            "message": "Manual image deleted successfully"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting manual image: {str(e)}"
        )

@router.post("/dalle-generate", response_model=None)
async def generate_dalle_image(
    request: DalleImageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Genera una imagen usando DALL-E y la guarda en la carpeta especificada
    """
    try:
        image_generator = ImageGenerator(db)
        if not image_generator.openai_client:
            raise HTTPException(status_code=400, detail="OpenAI API key not configured. Please set OpenAI API key in settings.")
        
        # Generar la imagen
        result = image_generator.generate_image(
            prompt=request.prompt,
            style="realistic",
            size=request.size,
            quality=request.quality
        )
        
        # Mover la imagen a la carpeta específica - usar path seguro para Railway
        target_dir = os.environ.get("GENERATED_IMAGES_PATH", 
                                   os.path.join(os.path.dirname(__file__), "..", "..", "..", "storage", "images", "generated"))
        os.makedirs(target_dir, exist_ok=True)
        
        # Generar nombre único
        file_extension = ".png"  # DALL-E genera PNG
        unique_filename = f"dalle_{uuid.uuid4()}{file_extension}"
        target_path = os.path.join(target_dir, unique_filename)
        
        # Copiar la imagen a la nueva ubicación
        if os.path.exists(result["image_path"]):
            shutil.copy2(result["image_path"], target_path)
        
        # URL relativa para acceso web
        image_url = f"/static/images/generated/{unique_filename}"
        
        return {
            "success": True,
            "image_url": image_url,
            "image_path": target_path,
            "filename": unique_filename,
            "prompt_used": request.prompt,
            "alt_text": result["alt_text"],
            "created_at": str(uuid.uuid1().time)
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating DALL-E image: {str(e)}"
        )

@router.get("/dalle-gallery", response_model=None)
async def get_dalle_gallery(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene la galería de imágenes generadas con DALL-E
    """
    try:
        images_dir = os.environ.get("GENERATED_IMAGES_PATH", 
                                   os.path.join(os.path.dirname(__file__), "..", "..", "..", "storage", "images", "generated"))
        
        if not os.path.exists(images_dir):
            return {"success": True, "images": []}
        
        images = []
        for filename in os.listdir(images_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                file_path = os.path.join(images_dir, filename)
                file_stats = os.stat(file_path)
                
                images.append({
                    "filename": filename,
                    "url": f"/static/images/generated/{filename}",
                    "created_at": file_stats.st_ctime,
                    "size": file_stats.st_size
                })
        
        # Ordenar por fecha de creación (más recientes primero)
        images.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "success": True,
            "images": images
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading DALL-E gallery: {str(e)}"
        )

@router.delete("/dalle-delete/{filename}", response_model=None)
async def delete_dalle_image(
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Elimina una imagen generada con DALL-E
    """
    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        images_dir = os.path.join(backend_dir, "static", "images", "generated")
        file_path = os.path.join(images_dir, filename)
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )
        
        # Verificar que el archivo está en el directorio correcto (seguridad)
        if not file_path.startswith(images_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path"
            )
        
        # Eliminar el archivo
        os.remove(file_path)
        
        return {
            "success": True,
            "message": "Image deleted successfully",
            "filename": filename
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting DALL-E image: {str(e)}"
        )
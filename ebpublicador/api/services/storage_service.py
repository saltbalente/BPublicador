"""Storage service for file management across cloud environments."""

import logging
import os
import shutil
import hashlib
import mimetypes
from typing import Dict, List, Optional, Tuple, BinaryIO
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from config import config

logger = logging.getLogger(__name__)


class StorageType(Enum):
    """Types of storage locations."""
    UPLOADS = "uploads"
    GENERATED = "generated"
    CACHE = "cache"
    TEMP = "temp"


@dataclass
class FileInfo:
    """File information structure."""
    filename: str
    original_name: str
    size: int
    mime_type: str
    storage_path: str
    url_path: str
    hash_md5: str
    created_at: datetime
    storage_type: StorageType


@dataclass
class UploadResult:
    """Result of file upload operation."""
    success: bool
    file_info: Optional[FileInfo] = None
    error: Optional[str] = None
    fallback_used: bool = False


class StorageService:
    """Service for managing file storage across different environments."""
    
    def __init__(self):
        self.base_storage_path = Path(config.storage_path)
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_extensions = {
            'images': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'},
            'documents': {'.pdf', '.doc', '.docx', '.txt', '.md'},
            'archives': {'.zip', '.tar', '.gz'}
        }
        self.allowed_mime_types = {
            'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
            'application/pdf', 'text/plain', 'text/markdown',
            'application/zip', 'application/x-tar', 'application/gzip'
        }
        
        # Initialize storage directories
        self._initialize_storage()
    
    def init_storage_dirs(self) -> None:
        """Public method to initialize storage directories (for testing)."""
        self._initialize_storage()
    
    def _initialize_storage(self) -> None:
        """Initialize storage directories with fallback handling."""
        try:
            for storage_type in StorageType:
                storage_dir = self.base_storage_path / storage_type.value
                self._ensure_directory(storage_dir)
            
            logger.info(f"Storage initialized at: {self.base_storage_path}")
            
        except Exception as e:
            logger.error(f"Storage initialization failed: {e}")
            # Try fallback to /tmp
            try:
                self.base_storage_path = Path("/tmp/ebpublicador_storage")
                for storage_type in StorageType:
                    storage_dir = self.base_storage_path / storage_type.value
                    self._ensure_directory(storage_dir)
                
                logger.warning(f"Using fallback storage at: {self.base_storage_path}")
                
            except Exception as fallback_error:
                logger.error(f"Fallback storage initialization failed: {fallback_error}")
                # Use in-memory storage as last resort
                self.base_storage_path = Path("/tmp")
    
    def _ensure_directory(self, directory: Path) -> None:
        """Ensure directory exists with proper error handling."""
        try:
            directory.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions
            test_file = directory.joinpath(".write_test")
            test_file.write_text("test")
            test_file.unlink()
            
        except PermissionError:
            logger.warning(f"Permission denied for directory: {directory}")
            raise
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            raise
    
    async def upload_file(
        self, 
        file_data: BinaryIO, 
        filename: str, 
        storage_type: StorageType = StorageType.UPLOADS
    ) -> UploadResult:
        """Upload file with comprehensive validation and error handling."""
        try:
            # Validate file
            validation_result = self._validate_file(file_data, filename)
            if not validation_result[0]:
                return UploadResult(success=False, error=validation_result[1])
            
            # Generate unique filename
            safe_filename = self._generate_safe_filename(filename)
            
            # Determine storage path
            storage_dir = self.base_storage_path / storage_type.value
            file_path = storage_dir / safe_filename
            
            # Read file data
            file_data.seek(0)
            content = file_data.read()
            
            # Calculate file hash
            file_hash = hashlib.md5(content).hexdigest()
            
            # Check for duplicate files
            existing_file = self._find_duplicate_file(file_hash, storage_type)
            if existing_file:
                logger.info(f"File already exists: {existing_file.filename}")
                return UploadResult(success=True, file_info=existing_file)
            
            # Save file with fallback handling
            try:
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                fallback_used = False
                
            except (PermissionError, OSError) as e:
                logger.warning(f"Primary storage failed: {e}, trying fallback")
                
                # Try fallback location
                fallback_dir = Path("/tmp") / "ebpublicador" / storage_type.value
                self._ensure_directory(fallback_dir)
                file_path = fallback_dir / safe_filename
                
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                fallback_used = True
            
            # Create file info
            file_info = FileInfo(
                filename=safe_filename,
                original_name=filename,
                size=len(content),
                mime_type=mimetypes.guess_type(filename)[0] or 'application/octet-stream',
                storage_path=str(file_path),
                url_path=f"/storage/{storage_type.value}/{safe_filename}",
                hash_md5=file_hash,
                created_at=datetime.now(),
                storage_type=storage_type
            )
            
            logger.info(
                f"File uploaded successfully: {safe_filename} "
                f"({len(content)} bytes, fallback: {fallback_used})"
            )
            
            return UploadResult(
                success=True, 
                file_info=file_info, 
                fallback_used=fallback_used
            )
            
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return UploadResult(success=False, error=str(e))
    
    def _validate_file(self, file_data: BinaryIO, filename: str) -> Tuple[bool, Optional[str]]:
        """Validate uploaded file."""
        try:
            # Check file size
            file_data.seek(0, 2)  # Seek to end
            file_size = file_data.tell()
            file_data.seek(0)  # Reset to beginning
            
            if file_size > self.max_file_size:
                return False, f"File too large: {file_size} bytes (max: {self.max_file_size})"
            
            if file_size == 0:
                return False, "File is empty"
            
            # Check file extension
            file_ext = Path(filename).suffix.lower()
            all_allowed_extensions = set()
            for ext_set in self.allowed_extensions.values():
                all_allowed_extensions.update(ext_set)
            
            if file_ext not in all_allowed_extensions:
                return False, f"File type not allowed: {file_ext}"
            
            # Check MIME type
            mime_type = mimetypes.guess_type(filename)[0]
            if mime_type and mime_type not in self.allowed_mime_types:
                return False, f"MIME type not allowed: {mime_type}"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def _generate_safe_filename(self, original_filename: str) -> str:
        """Generate safe, unique filename."""
        # Get file extension
        file_path = Path(original_filename)
        name = file_path.stem
        ext = file_path.suffix
        
        # Sanitize filename
        safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_', '.'))
        safe_name = safe_name[:50]  # Limit length
        
        # Add timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"{timestamp}_{safe_name}{ext}"
    
    def _find_duplicate_file(self, file_hash: str, storage_type: StorageType) -> Optional[FileInfo]:
        """Find duplicate file by hash."""
        try:
            storage_dir = self.base_storage_path / storage_type.value
            
            for file_path in storage_dir.iterdir():
                if file_path.is_file():
                    try:
                        with open(file_path, 'rb') as f:
                            existing_hash = hashlib.md5(f.read()).hexdigest()
                        
                        if existing_hash == file_hash:
                            return FileInfo(
                                filename=file_path.name,
                                original_name=file_path.name,
                                size=file_path.stat().st_size,
                                mime_type=mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream',
                                storage_path=str(file_path),
                                url_path=f"/storage/{storage_type.value}/{file_path.name}",
                                hash_md5=existing_hash,
                                created_at=datetime.fromtimestamp(file_path.stat().st_ctime),
                                storage_type=storage_type
                            )
                    except Exception:
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            return None
    
    async def delete_file(self, filename: str, storage_type: StorageType) -> bool:
        """Delete file from storage."""
        try:
            file_path = self.base_storage_path / storage_type.value / filename
            
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted: {filename}")
                return True
            else:
                logger.warning(f"File not found for deletion: {filename}")
                return False
                
        except Exception as e:
            logger.error(f"File deletion failed: {e}")
            return False
    
    async def get_file_info(self, filename: str, storage_type: StorageType) -> Optional[FileInfo]:
        """Get file information."""
        try:
            file_path = self.base_storage_path / storage_type.value / filename
            
            if not file_path.exists():
                return None
            
            stat = file_path.stat()
            
            # Calculate hash
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            return FileInfo(
                filename=filename,
                original_name=filename,
                size=stat.st_size,
                mime_type=mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream',
                storage_path=str(file_path),
                url_path=f"/storage/{storage_type.value}/{filename}",
                hash_md5=file_hash,
                created_at=datetime.fromtimestamp(stat.st_ctime),
                storage_type=storage_type
            )
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None
    
    async def list_files(self, storage_type: StorageType, limit: int = 100) -> List[FileInfo]:
        """List files in storage."""
        try:
            storage_dir = self.base_storage_path / storage_type.value
            files = []
            
            for file_path in storage_dir.iterdir():
                if file_path.is_file() and len(files) < limit:
                    try:
                        stat = file_path.stat()
                        
                        file_info = FileInfo(
                            filename=file_path.name,
                            original_name=file_path.name,
                            size=stat.st_size,
                            mime_type=mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream',
                            storage_path=str(file_path),
                            url_path=f"/storage/{storage_type.value}/{file_path.name}",
                            hash_md5="",  # Skip hash calculation for listing
                            created_at=datetime.fromtimestamp(stat.st_ctime),
                            storage_type=storage_type
                        )
                        
                        files.append(file_info)
                        
                    except Exception as e:
                        logger.warning(f"Error reading file {file_path}: {e}")
                        continue
            
            # Sort by creation time (newest first)
            files.sort(key=lambda f: f.created_at, reverse=True)
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []
    
    async def cleanup_old_files(self, storage_type: StorageType, days_old: int = 30) -> int:
        """Clean up old files from storage."""
        try:
            storage_dir = self.base_storage_path / storage_type.value
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            deleted_count = 0
            
            for file_path in storage_dir.iterdir():
                if file_path.is_file():
                    try:
                        if file_path.stat().st_ctime < cutoff_time:
                            file_path.unlink()
                            deleted_count += 1
                            logger.debug(f"Deleted old file: {file_path.name}")
                    except Exception as e:
                        logger.warning(f"Error deleting old file {file_path}: {e}")
                        continue
            
            logger.info(f"Cleaned up {deleted_count} old files from {storage_type.value}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return 0
    
    async def get_storage_stats(self) -> Dict[str, any]:
        """Get storage statistics."""
        try:
            stats = {
                "base_path": str(self.base_storage_path),
                "total_size": 0,
                "storage_types": {}
            }
            
            for storage_type in StorageType:
                storage_dir = self.base_storage_path / storage_type.value
                
                if storage_dir.exists():
                    file_count = 0
                    total_size = 0
                    
                    for file_path in storage_dir.iterdir():
                        if file_path.is_file():
                            try:
                                size = file_path.stat().st_size
                                total_size += size
                                file_count += 1
                            except Exception:
                                continue
                    
                    stats["storage_types"][storage_type.value] = {
                        "file_count": file_count,
                        "total_size": total_size,
                        "path": str(storage_dir)
                    }
                    
                    stats["total_size"] += total_size
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {"error": str(e)}
    
    def get_file_url(self, filename: str, storage_type: StorageType) -> str:
        """Get public URL for file."""
        return f"/storage/{storage_type.value}/{filename}"
    
    def is_image_file(self, filename: str) -> bool:
        """Check if file is an image."""
        ext = Path(filename).suffix.lower()
        return ext in self.allowed_extensions['images']
    
    def is_document_file(self, filename: str) -> bool:
        """Check if file is a document."""
        ext = Path(filename).suffix.lower()
        return ext in self.allowed_extensions['documents']


# Global storage service instance
storage_service = StorageService()
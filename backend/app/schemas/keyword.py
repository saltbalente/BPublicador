from pydantic import BaseModel
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from .content import Content

class KeywordStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class KeywordPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class KeywordBase(BaseModel):
    keyword: str
    status: KeywordStatus = KeywordStatus.PENDING
    priority: KeywordPriority = KeywordPriority.MEDIUM
    search_volume: Optional[int] = None
    difficulty: Optional[float] = None
    notes: Optional[str] = None

class KeywordCreate(KeywordBase):
    pass

class KeywordUpdate(BaseModel):
    keyword: Optional[str] = None
    status: Optional[KeywordStatus] = None
    priority: Optional[KeywordPriority] = None
    search_volume: Optional[int] = None
    difficulty: Optional[float] = None
    notes: Optional[str] = None

class Keyword(KeywordBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class KeywordWithContent(Keyword):
    content_items: List['Content'] = []
    
    class Config:
        from_attributes = True
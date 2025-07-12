from pydantic import BaseModel, EmailStr
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .content import Content

class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_active: bool = True
    api_key_openai: Optional[str] = None
    api_key_deepseek: Optional[str] = None
    daily_limit: int = 10

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    api_key_openai: Optional[str] = None
    api_key_deepseek: Optional[str] = None
    daily_limit: int = 10

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    api_key_openai: Optional[str] = None
    api_key_deepseek: Optional[str] = None
    daily_limit: Optional[int] = None

class User(UserBase):
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserWithContent(User):
    content_items: List['Content'] = []
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
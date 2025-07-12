# Schemas package
from .keyword import (
    KeywordStatus,
    KeywordPriority,
    KeywordBase,
    KeywordCreate,
    KeywordUpdate,
    Keyword,
    KeywordWithContent
)
from .content import (
    ContentStatus,
    ContentBase,
    ContentCreate,
    ContentUpdate,
    Content,
    ContentWithKeyword,
    ContentWithUser
)
from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    User,
    UserWithContent,
    UserLogin,
    Token,
    TokenData
)

# Rebuild models to resolve forward references
KeywordWithContent.model_rebuild()
ContentWithKeyword.model_rebuild()
ContentWithUser.model_rebuild()
UserWithContent.model_rebuild()

__all__ = [
    # Keyword schemas
    "KeywordStatus",
    "KeywordPriority",
    "KeywordBase",
    "KeywordCreate",
    "KeywordUpdate",
    "Keyword",
    "KeywordWithContent",
    # Content schemas
    "ContentStatus",
    "ContentBase",
    "ContentCreate",
    "ContentUpdate",
    "Content",
    "ContentWithKeyword",
    "ContentWithUser",
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "User",
    "UserWithContent",
    "UserLogin",
    "Token",
    "TokenData"
]
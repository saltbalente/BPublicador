"""API routes package."""

from .posts import router as posts_router
from .generation import router as generation_router
from .admin import router as admin_router

__all__ = [
    "posts_router",
    "generation_router", 
    "admin_router"
]
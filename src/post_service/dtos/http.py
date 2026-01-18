from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


class Author(BaseModel):
    """Информация об авторе публикации"""
    id: str
    username: Optional[str] = None
    name: Optional[str] = None  # Полное имя, если доступно


class PostCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None  # Краткое описание
    page: Dict[str, Any]  # JSON структура страницы (было content)
    game: Optional[str] = None  # ID игры, если публикация связана с игрой
    tags: List[str] = []


class PostUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    page: Optional[Dict[str, Any]] = None  # JSON структура страницы
    game: Optional[str] = None
    tags: Optional[List[str]] = None


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: Optional[str] = None
    page: Dict[str, Any]  # JSON структура страницы (было content)
    author: Author  # Автор как отдельный объект
    game: Optional[str] = None  # ID игры
    status: str
    tags: List[str]
    view_count: int
    like_count: int
    comment_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None


class PostStatsResponse(BaseModel):
    post_id: str
    view_count: int
    like_count: int
    comment_count: int


class PostListResponse(BaseModel):
    posts: List[PostResponse]
    total: int
    page: int
    size: int
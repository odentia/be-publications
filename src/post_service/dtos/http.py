from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class PostCreateRequest(BaseModel):
    title: str
    content: str
    tags: List[str] = []


class PostUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    content: str
    author_id: str
    author_username: Optional[str]
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
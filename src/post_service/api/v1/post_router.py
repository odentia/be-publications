from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

# Исправьте импорт - возможно нужно абсолютный путь
from ...core.dependencies import get_post_service  # Попробуйте так

from ...dtos.http import (
    PostCreateRequest,
    PostResponse,
    PostUpdateRequest,
    PostListResponse
)
from ...domain.services import PostService
from ...clients.auth_service import AuthClient

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreateRequest,
    current_user: dict = Depends(AuthClient.get_user_profile),
    post_service: PostService = Depends(get_post_service)  # ✅
):
    return await post_service.create_post(
        title=post_data.title,
        content=post_data.content,
        author_id=current_user["user_id"],
        author_username=current_user.get("username", "unknown"),
        tags=post_data.tags
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    increment_views: bool = Query(True),
    post_service: PostService = Depends(get_post_service)  # ✅ Исправлено: было Depends()
):
    if increment_views:
        post = await post_service.view_post(post_id)
    else:
        post = await post_service.post_repo.find_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    return post


@router.post("/{post_id}/publish", response_model=PostResponse)
async def publish_post(
    post_id: str,
    current_user: dict = Depends(AuthClient.get_user_profile),
    post_service: PostService = Depends(get_post_service)  # ✅ Исправлено: было Depends()
):
    post = await post_service.publish_post(post_id, current_user["user_id"])
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or access denied")
    return post


@router.get("/", response_model=PostListResponse)
async def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    author_id: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    post_service: PostService = Depends(get_post_service)  # ✅ Исправлено: было Depends()
):
    if author_id:
        posts = await post_service.post_repo.find_by_author(author_id, skip, limit)
    else:
        posts = await post_service.post_repo.find_published(skip, limit, tags)

    return PostListResponse(
        posts=posts,
        total=len(posts),
        page=skip // limit + 1,
        size=limit
    )


@router.get("/search/", response_model=PostListResponse)
async def search_posts(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    post_service: PostService = Depends(get_post_service)  # ✅ Исправлено: было Depends()
):
    posts = await post_service.post_repo.search(q, skip, limit)

    return PostListResponse(
        posts=posts,
        total=len(posts),
        page=skip // limit + 1,
        size=limit
    )
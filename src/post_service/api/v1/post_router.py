from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

# Исправьте импорт - возможно нужно абсолютный путь
from ...core.dependencies import get_post_service  # Попробуйте так

from ...dtos.http import (
    PostCreateRequest,
    PostResponse,
    PostUpdateRequest,
    PostListResponse,
    Author
)
from ...domain.services import PostService
from ...domain.models import Post as PostModel
from ...clients.auth_service import AuthClient

router = APIRouter(prefix="/posts", tags=["posts"])


def post_to_response(post: PostModel, current_user_info: dict = None) -> PostResponse:
    """Преобразует модель Post в PostResponse с объектом Author"""
    # Если нет информации о пользователе, берем из auth_service или используем базовые данные
    author_id = post.author_id
    username = current_user_info.get("username") if current_user_info else None
    
    # TODO: Получить полную информацию об авторе из auth-service если нужно
    author = Author(
        id=author_id,
        username=username
    )
    
    # Преобразуем Post в PostResponse
    return PostResponse(
        id=post.id,
        title=post.title,
        description=post.description,
        page=post.page if isinstance(post.page, dict) else {},
        author=author,
        game=post.game,
        status=post.status,
        tags=post.tags if post.tags else [],
        view_count=post.view_count,
        like_count=post.like_count,
        comment_count=post.comment_count,
        created_at=post.created_at,
        updated_at=post.updated_at,
        published_at=post.published_at
    )


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreateRequest,
    current_user: dict = Depends(AuthClient.get_user_profile),
    post_service: PostService = Depends(get_post_service)
):
    post = await post_service.create_post(
        title=post_data.title,
        description=post_data.description,
        page=post_data.page,
        author_id=current_user["user_id"],
        author_username=current_user.get("username", "unknown"),
        game=post_data.game,
        tags=post_data.tags
    )
    
    return post_to_response(post, current_user)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    increment_views: bool = Query(True),
    post_service: PostService = Depends(get_post_service)
):
    if increment_views:
        post = await post_service.view_post(post_id)
    else:
        post = await post_service.post_repo.find_by_id(post_id)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # TODO: Получить информацию об авторе из auth-service
    return post_to_response(post)


@router.post("/{post_id}/publish", response_model=PostResponse)
async def publish_post(
    post_id: str,
    current_user: dict = Depends(AuthClient.get_user_profile),
    post_service: PostService = Depends(get_post_service)
):
    post = await post_service.publish_post(
        post_id, 
        current_user["user_id"],
        author_username=current_user.get("username", "unknown")
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or access denied")
    return post_to_response(post, current_user)


@router.get("/", response_model=PostListResponse)
async def list_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    author_id: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    game: Optional[str] = Query(None),  # Фильтр по игре
    post_service: PostService = Depends(get_post_service)
):
    if author_id:
        posts = await post_service.post_repo.find_by_author(author_id, skip, limit)
    else:
        posts = await post_service.post_repo.find_published(skip, limit, tags)
    
    # Фильтр по игре (если указан)
    if game:
        posts = [p for p in posts if p.game == game]

    # Преобразуем посты в ответы
    post_responses = [post_to_response(post) for post in posts]

    return PostListResponse(
        posts=post_responses,
        total=len(post_responses),
        page=skip // limit + 1,
        size=limit
    )


@router.get("/search/", response_model=PostListResponse)
async def search_posts(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    post_service: PostService = Depends(get_post_service)
):
    posts = await post_service.post_repo.search(q, skip, limit)

    # Преобразуем посты в ответы
    post_responses = [post_to_response(post) for post in posts]

    return PostListResponse(
        posts=post_responses,
        total=len(post_responses),
        page=skip // limit + 1,
        size=limit
    )
from __future__ import annotations
from typing import AsyncGenerator, Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from .db import get_db
from .config import Settings, settings
from ..domain.repositories import PostRepository
from ..repo.sql.repositories import SQLAlchemyPostRepository
from ..domain.services import PostService
from ..domain.jwt_service import JWTService
from ..mq.publisher import EventPublisher
import logging

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


def get_settings(request: Request) -> Settings:
    """Получить настройки из app state"""
    settings: Settings = request.app.state.settings
    return settings


async def get_current_token(
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> str:
    """Получить токен из кук или заголовка Authorization (приоритет у кук)
    
    Работает в двух режимах:
    1. С куками (для браузеров) - проверяет куку access_token
    2. С заголовками (для API клиентов) - проверяет Authorization: Bearer <token>
    """
    # 1. Проверяем куки (приоритет для HTTP-only, используется браузерами)
    access_token_cookie = request.cookies.get("access_token")
    if access_token_cookie:
        return access_token_cookie
    
    # 2. Если нет в куках, проверяем заголовок Authorization (для API клиентов)
    if creds and creds.credentials:
        return creds.credentials
    
    # Также проверяем заголовок напрямую (на случай, если HTTPBearer не сработал)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    
    return ""


async def get_current_user_id(
    request: Request,
    token: Annotated[str, Depends(get_current_token)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    """Получить ID текущего пользователя из JWT токена"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Проверяем JWT токен через JWTService
    jwt_service = JWTService(settings)
    payload = jwt_service.verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def get_user_profile(
    user_id: Annotated[str, Depends(get_current_user_id)],
    token: Annotated[str, Depends(get_current_token)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    """Получить информацию о текущем пользователе из JWT токена"""
    jwt_service = JWTService(settings)
    payload = jwt_service.verify_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    
    return {
        "user_id": payload.get("sub") or payload.get("user_id") or payload.get("id") or user_id,
        "username": payload.get("username") or payload.get("preferred_username"),
        "email": payload.get("email"),
        **payload  # Включаем все остальные поля из токена
    }


async def get_post_repository(
    db: AsyncSession = Depends(get_db)
) -> AsyncGenerator[PostRepository, None]:
    yield SQLAlchemyPostRepository(db)

async def get_event_publisher() -> AsyncGenerator[EventPublisher, None]:
    publisher = EventPublisher()
    try:
        await publisher.connect()
        yield publisher
    finally:
        await publisher.close()

async def get_post_service(
    post_repo: PostRepository = Depends(get_post_repository),
    event_publisher: EventPublisher = Depends(get_event_publisher)
) -> AsyncGenerator[PostService, None]:
    yield PostService(post_repo, event_publisher)


SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_db)]
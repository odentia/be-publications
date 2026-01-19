import httpx
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Header
from ..core.config import settings
from ..core.exeptions import PostServiceException

logger = logging.getLogger(__name__)


class AuthClient:
    def __init__(self):
        self.base_url = "http://auth-service:8000/api/v1"  # Adjust based on your setup
        self.timeout = 30.0

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Валидирует токен и возвращает информацию о пользователе"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(
                    f"{self.base_url}/auth/verify",
                    headers=headers
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Token validation failed: {response.status_code}")
                    return None

            except httpx.RequestError as e:
                logger.error(f"Auth service request failed: {e}")
                return None

    async def get_user_profile(self, user_id: str, token: str) -> Optional[Dict[str, Any]]:
        """Получает профиль пользователя по ID"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(
                    f"{self.base_url}/users/{user_id}/profile",
                    headers=headers
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"Failed to get user profile: {response.status_code}")
                    return None

            except httpx.RequestError as e:
                logger.error(f"Auth service request failed: {e}")
                return None


auth_client = AuthClient()


async def get_user_profile(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Зависимость FastAPI для получения информации о текущем пользователе
    из токена в заголовке Authorization
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    # Извлекаем токен из заголовка "Bearer <token>"
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>"
        )
    
    token = parts[1]
    
    # Валидируем токен через auth-service
    user_info = await auth_client.validate_token(token)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Возвращаем информацию о пользователе
    # Предполагаем, что validate_token возвращает объект с user_id и username
    return {
        "user_id": user_info.get("user_id") or user_info.get("id") or user_info.get("sub"),
        "username": user_info.get("username"),
        "email": user_info.get("email"),
        **user_info  # Включаем все остальные поля
    }
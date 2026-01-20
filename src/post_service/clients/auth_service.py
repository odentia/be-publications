import httpx
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AuthClient:
    def __init__(self):
        self.base_url = "http://auth-service:8000/api/v1"  # Adjust based on your setup
        self.timeout = 30.0

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Валидирует токен и возвращает информацию о пользователе"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # Отправляем токен через cookie
                cookies = {"access_token": token}
                response = await client.get(
                    f"{self.base_url}/auth/verify",
                    cookies=cookies
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
                # Отправляем токен через cookie
                cookies = {"access_token": token}
                response = await client.get(
                    f"{self.base_url}/users/{user_id}/profile",
                    cookies=cookies
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
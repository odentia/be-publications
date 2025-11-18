import httpx
import logging
from typing import Optional, Dict, Any
from ..core.config import settings
from ..core.exceptions import PostServiceException

logger = logging.getLogger(__name__)


class AuthClient:
    def __init__(self):
        self.base_url = "http://auth-service:8000/api/v1"  # Adjust based on your setup
        self.timeout = 30.0

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
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
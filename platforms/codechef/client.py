# platforms/codechef/client.py
from typing import Dict, Any, Optional
import json
import time
import aiohttp
import asyncio
from aiohttp import ClientError, ClientResponse
from tenacity import retry, stop_after_attempt, wait_exponential
from tenacity.retry import retry_if_exception_type

from platforms.base import BasePlatformClient
from core.exceptions import (
    ScraperError,
    RateLimitError,
    AuthenticationError,
    UserNotFoundError,
)
from core.logging import get_logger
from core.config import get_settings

logger = get_logger(__name__)

settings = get_settings()

CODECHEF_API_URL = settings.url.codechef_api_url
CODECHEF_CLIENT_ID = settings.api.codechef_client_id
CODECHEF_CLIENT_SECRET = settings.api.codechef_client_secret


class CodeChefClient(BasePlatformClient):
    """CodeChef API client"""

    def __init__(self) -> None:
        """Initialize the client"""
        super().__init__()
        self.access_token = None
        self.token_fetch_time = 0
        self.token_expires = 3000

    async def get_access_token(self) -> str:
        """Get an access token for the CodeChef API"""
        url = f"{CODECHEF_API_URL}/oauth/token"
        data = {
            "grant_type": "client_credentials",
            "scope": "public",
            "client_id": CODECHEF_CLIENT_ID,
            "client_secret": CODECHEF_CLIENT_SECRET,
            "redirect_uri": "",
        }
        try:
            response = await self.request("POST", url, json=data)  # Properly await
            json_response = await response.json()
            access_token = (
                json_response.get("result", {}).get("data", {}).get("access_token")
            )
            logger.info(f"Got access token: {access_token}")
            self.access_token = access_token
            self.token_fetch_time = time.time()
            return access_token
        except (ClientError, KeyError) as e:
            logger.error("Failed to get access token", error=str(e), exc_info=True)
            raise AuthenticationError("Failed to get access token")

    async def get_user_info(self, username: str) -> Dict[str, Any]:
        """Get user information from CodeChef"""
        if (
            not self.access_token
            or time.time() - self.token_fetch_time > self.token_expires
        ):
            await self.get_access_token()
        url = f"{CODECHEF_API_URL}/users/{username}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params = {"fields": "ratings"}
        try:
            response = await self.request(
                "GET",
                url,
                headers=headers,
                params=params,
                rate_limit=30,
                rate_limit_by_minute=True,
            )
            if response.status == 200:
                json_response = await response.json()
                data = json_response.get("result", {}).get("data", {})
                if data.get("message") in (
                    "user does not exists",
                    "no user found for this search",
                ):
                    logger.error("User not found", username=username)
                    raise UserNotFoundError
            return data.get("content", {})
        except (ClientError, KeyError) as e:
            logger.error("Failed to get user info", error=str(e), exc_info=True)
            raise ScraperError("Failed to get user info")

# platforms/codeforces/client.py
import time
import json
from typing import Dict, Any, List, Optional
import aiohttp
from aiohttp import ClientError, ClientResponse
from tenacity import retry, stop_after_attempt, wait_exponential
from tenacity.retry import retry_if_exception_type

from platforms.base import BasePlatformClient
from core.exceptions import ScraperError, RateLimitError, UserNotFoundError
from core.logging import get_logger
from core.config import get_settings
from utils.codeforces_utils import generate_random_string, generate_api_sig

logger = get_logger(__name__)
settings = get_settings()

CODEFORCES_URL = settings.url.codeforces_url
API_KEY = settings.api.codeforces_key
API_SECRET = settings.api.codeforces_secret

class CodeforcesClient(BasePlatformClient):
    """Codeforces API client"""
    
    def __init__(self) -> None:
        """Initialize the client"""
        super().__init__(rate_limit=1, timeout=30)
    
    async def get_user_info(self, handles: List[str]) -> Dict[str, Any]:
        """Get user information from Codeforces API
        
        Args:
            handles (List[str]): List of Codeforces handles to query
            
        Returns:
            Dict[str, Any]: Response data from Codeforces API
            
        Raises:
            UserNotFoundError: If user not found
            ScraperError: For general errors
            RateLimitError: If rate limit is exceeded
        """
        if not handles:
            raise ValueError("No handles provided")
            
        # Filter out invalid handles
        valid_handles = [handle for handle in handles if handle and handle != "#n/a" and "@" not in handle]
        if not valid_handles:
            raise UserNotFoundError("No valid handles provided")
            
        # Generate request parameters
        random_string = generate_random_string(6)
        current_time = int(time.time())
        handles_string = ";".join(valid_handles)
        
        # Generate API signature
        api_sig = generate_api_sig(
            random_string, 
            "user.info", 
            handles_string, 
            current_time,
            API_SECRET,
            API_KEY
        )
        
        # Construct the request URL
        url = f"{CODEFORCES_URL}/user.info"
        params = {
            "handles": handles_string,
            "apiKey": API_KEY,
            "time": current_time,
            "apiSig": f"{random_string}{api_sig}"
        }
        
        try:
            response = await self.request("GET", url, params=params)
            json_response = await response.json()
            
            if json_response.get("status") != "OK":
                error_message = json_response.get("comment", "Unknown error")
                if "not found" in error_message.lower():
                    logger.error("User not found", handles=handles_string)
                    raise UserNotFoundError(f"User not found: {error_message}")
                logger.error(f"API Error: {error_message}")
                raise ScraperError(f"API Error: {error_message}")
                
            return json_response.get("result", [])
            
        except (ClientError, json.JSONDecodeError) as e:
            if isinstance(e, aiohttp.ClientResponseError) and e.status == 429:
                logger.error("Rate limit exceeded", error=str(e), exc_info=True)
                raise RateLimitError(f"Rate limit exceeded: {e}")
            logger.error("Failed to get user info", error=str(e), exc_info=True)
            raise ScraperError(f"Failed to get user info: {e}")
            
    async def get_single_user_info(self, handle: str) -> Optional[Dict[str, Any]]:
        """Get information for a single user
        
        Args:
            handle (str): Codeforces handle
            
        Returns:
            Optional[Dict[str, Any]]: User data or None if not found
        """
        if not handle or handle == "#n/a" or "@" in handle:
            return None
            
        try:
            results = await self.get_user_info([handle])
            if results and len(results) > 0:
                return results[0]
            return None
        except (UserNotFoundError, ScraperError, RateLimitError):
            return None 
import json
import asyncio
import urllib.parse
from typing import Dict, Any, Optional
import aiohttp
from aiohttp import ClientError, ClientResponse
from tenacity import retry, stop_after_attempt, wait_exponential
from tenacity.retry import retry_if_exception_type

from platforms.base import BasePlatformClient
from core.exceptions import ScraperError, RateLimitError, UserNotFoundError
from core.logging import get_logger
from core.config import get_settings
from utils.leetcode_utils import format_graphql_query

logger = get_logger(__name__)
settings = get_settings()

LEETCODE_API_BASE_URL = "https://leetcode.com/graphql"
LEETCODE_URL = "https://leetcode.com"

class LeetCodeClient(BasePlatformClient):
    """LeetCode API client"""
    
    def __init__(self) -> None:
        """Initialize the client"""
        # Use rate limit of 1 request per second to be safe
        super().__init__(rate_limit=1, timeout=30)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Referer": LEETCODE_URL,
            "Cache-Control": "no-cache"
        }
        self.user_cache = {}  # Simple cache to avoid repeated API calls
        
    async def get_user_contest_data(self, handle: str) -> Dict[str, Any]:
        """Get contest data for a LeetCode handle
        
        Args:
            handle (str): LeetCode handle
            
        Returns:
            Dict[str, Any]: API response with contest data
            
        Raises:
            UserNotFoundError: If user is not found
            ScraperError: For general errors
        """
        if not handle or handle == "#n/a":
            return {}
            
        # Check cache first
        if handle in self.user_cache:
            logger.debug(f"Using cached data for {handle}")
            return self.user_cache[handle]
            
        # Format the GraphQL query
        query = format_graphql_query(handle)
        
        # URL encode the query
        encoded_query = urllib.parse.quote(query, safe='')
        
        # Construct the full URL with the query parameter
        url = f"{LEETCODE_API_BASE_URL}?query={encoded_query}"
        
        # Log the URL for debugging
        logger.debug(f"Calling LeetCode API URL: {url}")
        
        try:
            # Use retry mechanism to handle potential transient failures
            for attempt in range(3):
                try:
                    response = await self.request(
                        "GET", 
                        url, 
                        headers=self.headers
                    )
                    break
                except (aiohttp.ClientResponseError, asyncio.TimeoutError) as e:
                    if isinstance(e, aiohttp.ClientResponseError) and e.status == 429:
                        # Rate limit - wait longer between retries
                        logger.warning(f"Rate limit hit for {handle}, waiting before retry (attempt {attempt+1}/3)")
                        await asyncio.sleep(10 * (attempt + 1))  # Exponential backoff
                    elif attempt < 2:  # Don't log on last attempt
                        logger.warning(f"Retrying request for {handle} after error: {str(e)} (attempt {attempt+1}/3)")
                        await asyncio.sleep(3 * (attempt + 1))
                    else:
                        raise
            
            json_response = await response.json()
            
            # Check for errors
            if "errors" in json_response:
                error_message = json_response["errors"][0]["message"]
                # Possible text: User matching query does not exist
                if "could not find user" in error_message.lower() or "user matching query does not exist" in error_message.lower():
                    logger.error(f"User not found: {handle}")
                    raise UserNotFoundError(f"User not found: {handle}")
                else:
                    logger.error(f"Failed to get contest data for {handle}: {error_message}")
                    raise ScraperError(f"Failed to get contest data: {error_message}")
                    
            # Check if user contest ranking exists
            if not json_response.get("data", {}).get("userContestRanking"):
                logger.warning(f"No contest data found for {handle}")
                # This is not an error, just no contests participated
                # Return an empty contest ranking
                json_response = {
                    "data": {
                        "userContestRanking": {
                            "attendedContestsCount": 0,
                            "rating": 0,
                            "globalRanking": None,
                            "totalParticipants": None,
                            "topPercentage": None
                        }
                    }
                }
                
            # Cache the result
            self.user_cache[handle] = json_response
            return json_response
            
        except UserNotFoundError:
            raise
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                logger.error(f"Rate limit exceeded for {handle}", error=str(e), exc_info=True)
                raise RateLimitError(f"Rate limit exceeded: {e}")
            elif e.status == 403:
                logger.error(f"Access forbidden for {handle}, may need authentication", error=str(e))
                raise ScraperError(f"Access forbidden: {e}")
            else:
                logger.error(f"HTTP error for {handle}: {e.status}", error=str(e))
                raise ScraperError(f"HTTP error: {e}")
        except (ClientError, json.JSONDecodeError, asyncio.TimeoutError) as e:
            logger.error(f"Failed to get contest data for {handle}", error=str(e), exc_info=True)
            raise ScraperError(f"Failed to get contest data: {e}")
            
    async def verify_user_exists(self, handle: str) -> bool:
        """Verify if a user exists
        
        Args:
            handle (str): LeetCode handle
            
        Returns:
            bool: True if the user exists, False otherwise
        """
        if not handle or handle == "#n/a":
            return False
            
        try:
            await self.get_user_contest_data(handle)
            return True
        except UserNotFoundError:
            return False
        except (ScraperError, RateLimitError):
            # Assume user exists if we get an error other than UserNotFoundError
            logger.warning(f"Error verifying user {handle}, assuming exists")
            return True 
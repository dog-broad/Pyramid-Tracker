from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
import time
import aiohttp
import asyncio
from aiohttp import ClientError, ClientResponse
from tenacity import retry, stop_after_attempt, wait_exponential
from tenacity.retry import retry_if_exception_type

from core.exceptions import ScraperError, RateLimitError
from core.logging import get_logger
from db.models import Participant, PlatformStatus

logger = get_logger(__name__)

class BasePlatformClient(ABC):
    """Base class for platform API clients"""
    
    def __init__(self, rate_limit: int = 2, timeout: int = 30, rate_limit_by_minute: bool = False, bypass_rate_limit: bool = False) -> None:
        """Initialize the client"""
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.rate_limit_by_minute = rate_limit_by_minute
        self.bypass_rate_limit = bypass_rate_limit
        self.last_request_time = 0
        
        # Create a session for making requests
        self.session = aiohttp.ClientSession()
        
    async def initialize(self):
        """Initialize aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _rate_limit(self, rate_limit: Optional[int] = None) -> None:
        """Apply rate limiting"""
        if self.bypass_rate_limit:
            return
        
        effective_rate_limit = rate_limit if rate_limit is not None else self.rate_limit
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        # If we're making requests too quickly, sleep
        if time_since_last_request < (1.0 / effective_rate_limit):
            sleep_time = (1.0 / effective_rate_limit) - time_since_last_request
            await asyncio.sleep(sleep_time)
            
        self.last_request_time = time.time()
        
    async def _rate_limit_by_minute(self, rate_limit: Optional[int] = None) -> None:
        """Apply rate limiting by minute"""
        if self.bypass_rate_limit:
            return
        
        effective_rate_limit = rate_limit if rate_limit is not None else self.rate_limit
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        # If we're making requests too quickly, sleep
        # CALL_INTERVAL = SECONDS_PER_MINUTE / MAX_CALLS_PER_MINUTE
        if time_since_last_request < (300.0 / effective_rate_limit):
            sleep_time = (300.0 / effective_rate_limit) - time_since_last_request
            await asyncio.sleep(sleep_time)
            
        self.last_request_time = time.time()
    
    # Retry 3 times with exponential backoff (4s, 8s, 16s) if
    # the request raises a ClientError
    # ClientError is raised if the response status code is not 200
    @retry(
        retry=retry_if_exception_type(ClientError),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        stop=stop_after_attempt(3)
    )
    async def request(self, method: str, url: str, rate_limit: Optional[int] = None, rate_limit_by_minute: bool = False, bypass_rate_limit: bool = False, **kwargs) -> ClientResponse:
        """Make a rate-limited request"""
        if self.session is None or self.session.closed:
            await self.initialize()  # Ensure session is open
            
        if rate_limit:
            self.rate_limit = rate_limit
        if rate_limit_by_minute:
            self.rate_limit_by_minute = rate_limit_by_minute
        if bypass_rate_limit:
            self.bypass_rate_limit = bypass_rate_limit
        
        if not bypass_rate_limit:
            if rate_limit_by_minute:
                await self._rate_limit_by_minute(self.rate_limit)
            else:
                await self._rate_limit(self.rate_limit)
        try:
            async with self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            ) as response:
                await response.read()  # Ensure the response is read
                response.raise_for_status()
                return response
        except aiohttp.ClientResponseError as e:
            if e.status == 429:
                logger.error("Rate limit exceeded", error=str(e))
                raise RateLimitError(f"Rate limit exceeded: {e}")
            logger.error("HTTP error", error=str(e), exc_info=True)
            raise ScraperError(f"HTTP error: {e}")


class BasePlatformService(ABC):
    """Base class for platform services that handles both data retrieval and verification"""
    
    def __init__(self) -> None:
        """Initialize the service"""
        self.client = self._create_client()
        
    @abstractmethod
    def _create_client(self) -> BasePlatformClient:
        """Create the platform client"""
        pass
        
    async def close(self):
        """Close the service's client"""
        await self.client.close()
        
    @abstractmethod
    async def get_participant_data(self, participant: Participant) -> PlatformStatus:
        """Get data for a participant"""
        pass
        
    @abstractmethod
    async def process_batch(self, participants: List[Participant]) -> List[Participant]:
        """Process a batch of participants"""
        pass
        
    @abstractmethod
    async def verify_participant(self, participant: Participant) -> bool:
        """Verify a participant's handle"""
        pass


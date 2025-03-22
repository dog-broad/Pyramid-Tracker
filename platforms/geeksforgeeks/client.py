import json
import asyncio
from typing import Dict, Any, List, Optional, Set
import aiohttp
from aiohttp import ClientError, ClientResponse
from tenacity import retry, stop_after_attempt, wait_exponential
from tenacity.retry import retry_if_exception_type

from platforms.base import BasePlatformClient
from core.exceptions import ScraperError, RateLimitError, UserNotFoundError
from core.logging import get_logger
from core.config import get_settings
from utils.gfg_utils import extract_practice_score, extract_weekly_contest_score
from db.repositories import LeaderboardCacheRepository
from db.models import LeaderboardCache
from core.constants import Platform
from db.client import DatabaseClient

logger = get_logger(__name__)
settings = get_settings()

GFG_API_URL = settings.url.gfg_api_url + "?handle="
GFG_WEEKLY_CONTEST_URL = settings.url.gfg_weekly_contest_url + "?leaderboard_type=0&page="
GEEKSFORGEEKS_URL = settings.url.geeksforgeeks_url
GFG_USERNAME = settings.api.gfg_username
GFG_PASSWORD = settings.api.gfg_password

class GeeksForGeeksClient(BasePlatformClient):
    """GeeksForGeeks API client"""
    
    def __init__(self, cache_repository: Optional[LeaderboardCacheRepository] = None) -> None:
        """Initialize the client"""
        super().__init__(rate_limit=2, timeout=30)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Referer": GEEKSFORGEEKS_URL
        }
        # In-memory cache for leaderboard data
        self.leaderboard_cache = {}  # Maps contest_id -> list of entries
        self.user_cache = {}  # Maps user_handle -> {contest_id: entry}
        self.is_cache_initialized = False
        
        # Database cache repository
        if cache_repository is None:
            # Initialize database client and repository if not provided
            db_client = DatabaseClient(settings.db.mongodb_cache_name)
            self.cache_repository = LeaderboardCacheRepository(db_client)
        else:
            self.cache_repository = cache_repository
        
    async def initialize_cache(self, max_pages: int = 1000, force_refresh: bool = False) -> None:
        """Initialize the cache by fetching all leaderboard data
        
        Args:
            max_pages (int): Maximum number of pages to fetch
            force_refresh (bool): Force refresh the cache even if already initialized
        """
        if self.is_cache_initialized and not force_refresh:
            return
            
        logger.info("Initializing leaderboard cache...")
        start_time = asyncio.get_event_loop().time()
        
        # Check if we have cache in the database first
        if not force_refresh:
            try:
                # Get only fresh cache entries (not older than 1 day)
                db_cache_entries = self.cache_repository.get_platform_cache_entries(
                    Platform.GEEKSFORGEEKS,
                    only_fresh=True
                )
                
                if db_cache_entries:
                    # Load from database cache
                    logger.info(f"Loading cache from database: {len(db_cache_entries)} fresh entries")
                    
                    for entry in db_cache_entries:
                        contest_id = entry.cache_id
                        self.leaderboard_cache[contest_id] = entry.entries
                        
                        # Also index by user handle for faster lookups
                        for user_entry in entry.entries:
                            user_handle = user_entry.get("user_handle", "").lower()
                            if user_handle:
                                if user_handle not in self.user_cache:
                                    self.user_cache[user_handle] = {}
                                    
                                self.user_cache[user_handle][contest_id] = user_entry
                    
                    self.is_cache_initialized = True
                    logger.info(f"Cache loaded from database: {len(self.leaderboard_cache)} contests with {len(self.user_cache)} unique users")
                    return
                else:
                    logger.info("No fresh cache entries found in database, will fetch fresh data")
            except Exception as e:
                logger.error(f"Error loading cache from database: {e}")
                # Continue with fetching fresh data
        
        # If force refresh or no database cache, fetch fresh data
        db_cache_entries_to_save = []
        
        # Track which pages we've already processed successfully
        processed_pages = set()
        max_retries = 3
        
        # Determine starting page - resume from where we left off if possible
        start_page = 0
        if self.leaderboard_cache:
            processed_page_ids = [int(page_id) for page_id in self.leaderboard_cache.keys() if page_id.isdigit()]
            if processed_page_ids:
                processed_pages = set(processed_page_ids)
                start_page = max(processed_page_ids) + 1
                logger.info(f"Resuming from page {start_page}, {len(processed_pages)} pages already cached")
        
        for page in range(start_page, max_pages):
            # Skip if we've already processed this page
            if page in processed_pages:
                continue
                
            logger.info(f"Fetching leaderboard page {page}")
            retry_count = 0
            rate_limited = False
            
            while retry_count <= max_retries:
                try:
                    # Fetch the leaderboard page
                    url = f"{GFG_WEEKLY_CONTEST_URL}{page}"
                    response = await self.request("GET", url, headers=self.headers)
                    json_response = await response.json()
                    
                    entries = json_response.get("results", [])
                    if not entries:
                        # No more results
                        logger.info(f"No more leaderboard entries after page {page}")
                        break
                        
                    # Store in cache by contest ID (page number)
                    self.leaderboard_cache[str(page)] = entries
                    
                    # Create database cache entry
                    cache_entry = LeaderboardCache(
                        platform=Platform.GEEKSFORGEEKS,
                        cache_id=str(page),
                        entries=entries
                    )
                    db_cache_entries_to_save.append(cache_entry)
                    
                    # Record that we've processed this page
                    processed_pages.add(page)
                    
                    # Check if we reached a page with zero scores
                    found_zero = False
                    
                    # Also index by user handle for faster lookups
                    for entry in entries:
                        user_handle = entry.get("user_handle", "").lower()
                        user_score = entry.get("user_score")
                        
                        if user_handle:
                            if user_handle not in self.user_cache:
                                self.user_cache[user_handle] = {}
                                
                            self.user_cache[user_handle][str(page)] = entry
                            
                        # Check if we've reached low scores
                        if user_score == 0 or user_score is None:
                            found_zero = True
                    
                    # Progress logging
                    if page % 10 == 0:
                        elapsed = asyncio.get_event_loop().time() - start_time
                        logger.info(f"Cached {page+1} leaderboard pages, {len(self.user_cache)} unique users in {elapsed:.2f}s")
                    
                    # Save periodically to preserve progress
                    if len(db_cache_entries_to_save) >= 10:
                        try:
                            logger.info(f"Saving {len(db_cache_entries_to_save)} cache entries to database (progress save)")
                            self.cache_repository.save_cache_entries(db_cache_entries_to_save)
                            db_cache_entries_to_save = []
                        except Exception as e:
                            logger.error(f"Error saving progress to database: {e}")
                    
                    if found_zero:
                        # We've reached entries with zero scores, stop fetching more pages
                        logger.info(f"Reached zero scores at page {page}, stopping cache initialization")
                        break
                        
                    # Sleep to avoid hitting rate limits
                    await asyncio.sleep(0.1)
                    
                    # Successfully processed this page, move on to next
                    break
                    
                except (ClientError, json.JSONDecodeError) as e:
                    if isinstance(e, aiohttp.ClientResponseError) and e.status == 429:
                        rate_limited = True
                        retry_count += 1
                        logger.warning(f"Rate limit hit for page {page}, attempt {retry_count}/{max_retries}")
                        
                        if retry_count <= max_retries:
                            # Exponential backoff
                            wait_time = 60 * retry_count
                            logger.info(f"Waiting {wait_time} seconds before retrying...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(f"Max retries exceeded for page {page}, moving to next page")
                            break
                    else:
                        logger.error(f"Failed to fetch leaderboard page {page}: {e}")
                        # Continue with the next page instead of failing completely
                        await asyncio.sleep(1)
                        break
            
            # If we hit rate limits, take a longer break before next page
            if rate_limited:
                logger.info("Taking a break after rate limit to allow limits to reset")
                await asyncio.sleep(120)  # 2 minutes cooldown
            
            # Break outer loop if we found zero scores
            if 'found_zero' in locals() and found_zero:
                break
        
        # Save any remaining cache entries to database
        try:
            if db_cache_entries_to_save:
                logger.info(f"Saving {len(db_cache_entries_to_save)} remaining cache entries to database")
                self.cache_repository.save_cache_entries(db_cache_entries_to_save)
        except Exception as e:
            logger.error(f"Error saving cache to database: {e}")
        
        # Mark cache as initialized
        self.is_cache_initialized = True
        total_time = asyncio.get_event_loop().time() - start_time
        logger.info(f"Cache initialization completed in {total_time:.2f}s")
        logger.info(f"Cached {len(self.leaderboard_cache)} contests with {len(self.user_cache)} unique users")
        logger.info(f"Successfully processed {len(processed_pages)}/{max_pages} pages")
        
    async def get_practice_score(self, handle: str) -> Dict[str, Any]:
        """Get practice score for a GeeksForGeeks handle
        
        Args:
            handle (str): GeeksForGeeks handle
            
        Returns:
            Dict[str, Any]: API response with practice score data
            
        Raises:
            UserNotFoundError: If user is not found
            ScraperError: For general errors
        """
        if not handle or handle == "#n/a":
            return {}
            
        url = f"{GFG_API_URL}{handle}"
        
        try:
            response = await self.request("GET", url, headers=self.headers)
            json_response = await response.json()

            if response.status in {400, 404} or not json_response.get("data"):
                message = json_response.get("message", "").lower()
                if "user not found!" in message.lower():
                    logger.error(f"User not found: {handle}")
                    raise UserNotFoundError(f"User not found: {handle}")
                else:
                    logger.error(f"Failed to get practice score for {handle}: {json_response}")
                    raise ScraperError(f"Failed to get practice score: {json_response}")
                
            return json_response
        except ScraperError as e:
            raise
        except (ClientError, json.JSONDecodeError) as e:
            if isinstance(e, aiohttp.ClientResponseError) and e.status == 429:
                logger.error("Rate limit exceeded", error=str(e), exc_info=True)
                raise RateLimitError(f"Rate limit exceeded: {e}")
            logger.error(f"Failed to get practice score for {handle}: {e}")
            raise ScraperError(f"Failed to get practice score: {e}")
    
    async def get_weekly_contest_scores(self, handle: str) -> Dict[str, Dict[str, Any]]:
        """Get weekly contest scores for a user from the cache
        
        Args:
            handle (str): GeeksForGeeks handle
            
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of contest entries keyed by contest ID
        """
        if not handle or handle == "#n/a":
            return {}
            
        # Ensure cache is initialized
        if not self.is_cache_initialized:
            await self.initialize_cache()
            
        # Look up user in cache
        handle = handle.lower()
        results = {}
        
        # Check for each contest if we have a fresh cache version
        if handle in self.user_cache:
            for contest_id, entry in self.user_cache[handle].items():
                # Verify this cache entry is fresh
                try:
                    cache_entry = self.cache_repository.get_cache_entry(
                        Platform.GEEKSFORGEEKS, 
                        contest_id,
                        check_freshness=True  # Only use if not stale
                    )
                    
                    if cache_entry:
                        # If we have a fresh cache, find the user in it
                        for user_entry in cache_entry.entries:
                            user_handle = user_entry.get("user_handle", "").lower()
                            if user_handle == handle:
                                results[contest_id] = user_entry
                                break
                    else:
                        # Otherwise use in-memory cache if it exists
                        # (but this might be stale)
                        results[contest_id] = entry
                except Exception as e:
                    logger.error(f"Error checking cache freshness for contest {contest_id}: {e}")
                    # Use in-memory cache as fallback
                    results[contest_id] = entry
        
        return results
        
    async def get_user_data(self, handle: str) -> Dict[str, Any]:
        """Get complete user data including practice and weekly contest scores
        
        Args:
            handle (str): GeeksForGeeks handle
            
        Returns:
            Dict[str, Any]: User data with practice and weekly contest scores
            
        Raises:
            UserNotFoundError: If user is not found
            ScraperError: For general errors
        """
        if not handle or handle == "#n/a":
            return {}
            
        try:
            # Get practice score
            practice_task = self.get_practice_score(handle)
            
            # Get weekly contest scores from cache
            weekly_task = self.get_weekly_contest_scores(handle)
            
            # Run both tasks concurrently
            practice_data, weekly_data = await asyncio.gather(practice_task, weekly_task)
            
            # Extract scores
            practice_score, practice_raw = extract_practice_score(practice_data)
            weekly_score, weekly_raw = extract_weekly_contest_score(weekly_data)
            
            # Combine the data
            return {
                "practice": {
                    "score": practice_score,
                    "raw_data": practice_raw
                },
                "weekly_contest": {
                    "score": weekly_score,
                    "raw_data": weekly_raw
                }
            }
            
        except UserNotFoundError:
            raise
        except RateLimitError:
            raise
        except Exception as e:
            logger.error(f"Failed to get user data for {handle}: {e}")
            raise ScraperError(f"Failed to get user data: {e}")
            
    async def verify_user_exists(self, handle: str) -> bool:
        """Verify if a user exists
        
        Args:
            handle (str): GeeksForGeeks handle
            
        Returns:
            bool: True if the user exists, False otherwise
        """
        if not handle or handle == "#n/a":
            return False
            
        # Check if user exists in contest cache first (faster)
        if self.is_cache_initialized:
            handle_lower = handle.lower()
            if handle_lower in self.user_cache and self.user_cache[handle_lower]:
                return True
                
        # If not in cache, check via API
        try:
            await self.get_practice_score(handle)
            return True
        except UserNotFoundError:
            return False
        except (ScraperError, RateLimitError):
            # Assume user exists if we get an error other than UserNotFoundError
            logger.warning(f"Error verifying user {handle}, assuming exists")
            return True 
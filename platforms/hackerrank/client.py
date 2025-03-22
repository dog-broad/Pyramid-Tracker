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
from utils.hackerrank_utils import extract_contest_id
from db.repositories import LeaderboardCacheRepository
from db.models import LeaderboardCache
from core.constants import Platform
from db.client import DatabaseClient

logger = get_logger(__name__)
settings = get_settings()

HACKERRANK_API_URL = settings.url.hackerrank_api_url
HACKERRANK_URL = settings.url.hackerrank_url

class HackerRankClient(BasePlatformClient):
    """HackerRank API client"""
    
    def __init__(self, cache_repository: Optional[LeaderboardCacheRepository] = None) -> None:
        """Initialize the client"""
        super().__init__(rate_limit=1, timeout=30)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "TE": "Trailers"
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
        
    async def verify_user_profile(self, username: str) -> bool:
        """Verify if a HackerRank profile exists
        
        Args:
            username (str): HackerRank username
            
        Returns:
            bool: True if profile exists, False otherwise
        """
        if not username or username == "#n/a" or "@" in username:
            return False
            
        url = f"{HACKERRANK_URL}/profile/{username}"
        
        try:
            response = await self.request("GET", url, headers=self.headers)
            html_content = await response.text()
            
            # Check if profile exists by looking for specific markers in the HTML
            if "community-content" in html_content:
                return True
                
            # Check for various error indicators
            error_indicators = [
                "class=\"error-title\"",
                "HTTP 404: Page Not Found | HackerRank",
                "class=\"e404-view\"",
                "class=\"page-not-found-container container\""
            ]
            
            for indicator in error_indicators:
                if indicator in html_content:
                    return False
                    
            # If none of the error indicators are found, assume the profile exists
            return True
            
        except (ClientError, json.JSONDecodeError) as e:
            logger.error("Failed to verify user profile", error=str(e), exc_info=True)
            return False
    
    async def initialize_cache(self, contest_urls: List[str], force_refresh: bool = False) -> None:
        """Initialize the cache by fetching all leaderboards for the given contests
        
        Args:
            contest_urls (List[str]): List of HackerRank contest URLs to cache
            force_refresh (bool): Force refresh the cache even if already initialized
        """
        if self.is_cache_initialized and not force_refresh:
            logger.debug("Cache already initialized, skipping initialization")
            return
            
        if not contest_urls:
            logger.warning("No contest URLs provided for cache initialization")
            return
            
        # Filter out duplicate contest URLs while maintaining order
        unique_contest_urls = list(dict.fromkeys(contest_urls))
        logger.info(f"Initializing HackerRank leaderboard cache for {len(unique_contest_urls)} contests...")
        start_time = asyncio.get_event_loop().time()
        
        # Check if we have cache in the database first
        if not force_refresh:
            try:
                # Get only fresh cache entries (not older than 1 day)
                db_cache_entries = self.cache_repository.get_platform_cache_entries(
                    Platform.HACKERRANK,
                    only_fresh=True
                )
                
                if db_cache_entries:
                    # Load from database cache
                    cache_entry_count = len(db_cache_entries)
                    logger.info(f"Loading HackerRank cache from database: {cache_entry_count} fresh entries")
                    loaded_contest_ids = set()
                    
                    for entry in db_cache_entries:
                        contest_id = entry.cache_id
                        loaded_contest_ids.add(contest_id)
                        
                        # Only load if not already in memory cache
                        if contest_id not in self.leaderboard_cache:
                            self.leaderboard_cache[contest_id] = entry.entries
                            
                            # Also index by user handle for faster lookups
                            for user_entry in entry.entries:
                                user_handle = user_entry.get("hacker", "").lower()
                                if user_handle:
                                    if user_handle not in self.user_cache:
                                        self.user_cache[user_handle] = {}
                                        
                                    self.user_cache[user_handle][contest_id] = user_entry
                    
                    # Extract contest IDs from URLs
                    contest_ids_to_fetch = []
                    for contest_url in unique_contest_urls:
                        contest_id = extract_contest_id(contest_url)
                        if contest_id and contest_id not in loaded_contest_ids:
                            contest_ids_to_fetch.append((contest_url, contest_id))
                    
                    if not contest_ids_to_fetch:
                        # All contests are already in cache
                        self.is_cache_initialized = True
                        logger.info(f"All requested contests are already cached. Cache contains {len(self.leaderboard_cache)} contests with {len(self.user_cache)} unique users")
                        return
                    
                    logger.info(f"Need to fetch {len(contest_ids_to_fetch)} additional contests not in database cache")
                    
                else:
                    logger.info("No fresh HackerRank cache entries found in database, will fetch fresh data")
                    # Continue with extracting contest IDs
                    contest_ids_to_fetch = []
                    for contest_url in unique_contest_urls:
                        contest_id = extract_contest_id(contest_url)
                        if contest_id:
                            contest_ids_to_fetch.append((contest_url, contest_id))
                        else:
                            logger.warning(f"Could not extract contest ID from URL: {contest_url}")
            except Exception as e:
                logger.error(f"Error loading HackerRank cache from database: {e}")
                # Continue with fetching fresh data for all contests
                contest_ids_to_fetch = []
                for contest_url in unique_contest_urls:
                    contest_id = extract_contest_id(contest_url)
                    if contest_id:
                        contest_ids_to_fetch.append((contest_url, contest_id))
                    else:
                        logger.warning(f"Could not extract contest ID from URL: {contest_url}")
        else:
            # If forcing refresh, process all contests
            contest_ids_to_fetch = []
            for contest_url in unique_contest_urls:
                contest_id = extract_contest_id(contest_url)
                if contest_id:
                    contest_ids_to_fetch.append((contest_url, contest_id))
                else:
                    logger.warning(f"Could not extract contest ID from URL: {contest_url}")
        
        # Track which contests we've successfully processed
        processed_contests = set()
        db_cache_entries_to_save = []
        
        max_retries = 3  # Maximum number of retries for rate-limited contests
        
        # Process each contest
        for contest_url, contest_id in contest_ids_to_fetch:
            # Skip if we've already processed this contest
            if contest_id in processed_contests or contest_id in self.leaderboard_cache:
                continue
                
            logger.info(f"Caching leaderboard for contest: {contest_id}")
                
            # Fetch all entries for this contest
            all_entries = []
            offset = 1
            limit = 100
            retry_count = 0
            rate_limited = False
            
            while True:
                try:
                    url = f"{HACKERRANK_API_URL}/{contest_id}/leaderboard"
                    params = {
                        "offset": offset,
                        "limit": limit
                    }
                    
                    response = await self.request("GET", url, headers=self.headers, params=params)
                    json_response = await response.json()
                    
                    models = json_response.get('models', [])
                    if not models:
                        break
                        
                    all_entries.extend(models)
                    logger.debug(f"Fetched {len(models)} entries from contest {contest_id}, total: {len(all_entries)}")
                    
                    offset += limit
                    
                    # Sleep to avoid hitting rate limits
                    await asyncio.sleep(1)
                    
                except (ClientError, json.JSONDecodeError) as e:
                    if isinstance(e, aiohttp.ClientResponseError) and e.status == 429:
                        rate_limited = True
                        retry_count += 1
                        logger.warning(f"Rate limit hit for contest {contest_id}, attempt {retry_count}/{max_retries}")
                        
                        if retry_count <= max_retries:
                            wait_time = 60 * retry_count  # Increase wait time with each retry
                            logger.info(f"Waiting {wait_time} seconds before retrying...")
                            await asyncio.sleep(wait_time)
                            continue  # Try again from the same offset
                        else:
                            # Save what we have so far if we've reached max retries
                            logger.error(f"Max retries exceeded for contest {contest_id}, saving partial data with {len(all_entries)} entries")
                            break
                    else:
                        logger.error(f"Failed to fetch leaderboard for contest {contest_id}", error=str(e), exc_info=True)
                        break
            
            if all_entries:
                # Record that we've processed this contest
                processed_contests.add(contest_id)
                
                # Store in cache
                self.leaderboard_cache[contest_id] = all_entries
                
                # Create database cache entry
                cache_entry = LeaderboardCache(
                    platform=Platform.HACKERRANK,
                    cache_id=contest_id,
                    entries=all_entries
                )
                db_cache_entries_to_save.append(cache_entry)
                
                # Index by user handle
                for entry in all_entries:
                    user_handle = entry.get('hacker', '').lower()
                    if user_handle:
                        if user_handle not in self.user_cache:
                            self.user_cache[user_handle] = {}
                            
                        self.user_cache[user_handle][contest_id] = entry
                
                logger.info(f"Cached {len(all_entries)} entries for contest {contest_id}")
                
                # Save entries to database periodically to preserve progress
                if rate_limited or len(db_cache_entries_to_save) >= 5:
                    try:
                        if db_cache_entries_to_save:
                            logger.info(f"Saving {len(db_cache_entries_to_save)} HackerRank cache entries to database (progress save)")
                            self.cache_repository.save_cache_entries(db_cache_entries_to_save)
                            db_cache_entries_to_save = []
                    except Exception as e:
                        logger.error(f"Error saving progress to database: {e}")
                
                # If we hit rate limits, take a longer break before next contest
                if rate_limited:
                    logger.info("Taking a break after rate limit to allow limits to reset")
                    await asyncio.sleep(120)  # 2 minutes cooldown
        
        # Save remaining cache entries to database
        try:
            if db_cache_entries_to_save:
                logger.info(f"Saving remaining {len(db_cache_entries_to_save)} HackerRank cache entries to database")
                self.cache_repository.save_cache_entries(db_cache_entries_to_save)
        except Exception as e:
            logger.error(f"Error saving cache to database: {e}")
        
        # Mark cache as initialized
        self.is_cache_initialized = True
        total_time = asyncio.get_event_loop().time() - start_time
        logger.info(f"HackerRank cache initialization completed in {total_time:.2f}s")
        logger.info(f"Cached {len(self.leaderboard_cache)} contests with {len(self.user_cache)} unique users")
        logger.info(f"Successfully processed {len(processed_contests)}/{len(contest_ids_to_fetch)} contests")
            
    async def get_contest_leaderboard(self, contest_url: str, handles: Set[str]) -> Dict[str, float]:
        """Get scores from a HackerRank contest leaderboard
        
        Args:
            contest_url (str): URL of the HackerRank contest
            handles (Set[str]): Set of HackerRank handles to look for
            
        Returns:
            Dict[str, float]: Dictionary mapping handles to scores
        """
        contest_id = extract_contest_id(contest_url)
        results = {}
        
        # Check if data exists in cache first
        if self.is_cache_initialized and contest_id in self.leaderboard_cache:
            # Check if this specific contest has fresh cache from database
            try:
                cache_entry = self.cache_repository.get_cache_entry(
                    Platform.HACKERRANK, 
                    contest_id,
                    check_freshness=True
                )
                
                # If we have a fresh cache entry from the database, use it
                if cache_entry:
                    logger.debug(f"Using fresh cache entry for contest {contest_id}")
                    entries = cache_entry.entries
                else:
                    # Otherwise use in-memory cache if available
                    logger.debug(f"Using in-memory cache for contest {contest_id}")
                    entries = self.leaderboard_cache[contest_id]
                    
                for entry in entries:
                    hacker_handle = entry.get('hacker', '').lower()
                    if hacker_handle in handles:
                        current_score = results.get(hacker_handle, 0)
                        results[hacker_handle] = current_score + entry.get('score', 0)
                        logger.debug(f"Found user {hacker_handle} with score {entry.get('score', 0)} in cached contest {contest_id}")

                if not results:
                    logger.debug(f"No results found in cache for contest {contest_id}")
                    return results

                if results:
                    return results
            except Exception as e:
                logger.error(f"Error checking cache freshness for contest {contest_id}: {e}")
                # Continue with API fetch if there's an error
        
        # If not in cache or no results from cache, fetch from API
        offset = 1
        limit = 100
        
        while True:
            url = f"{HACKERRANK_API_URL}/{contest_id}/leaderboard"
            params = {
                "offset": offset,
                "limit": limit
            }
            
            try:
                response = await self.request("GET", url, headers=self.headers, params=params)
                json_response = await response.json()
                
                models = json_response.get('models', [])
                if not models:
                    break
                    
                found_handles = False
                for entry in models:
                    hacker_handle = entry.get('hacker', '').lower()
                    
                    if hacker_handle in handles:
                        found_handles = True
                        current_score = results.get(hacker_handle, 0)
                        results[hacker_handle] = current_score + entry.get('score', 0)
                        logger.debug(f"Found user {hacker_handle} with score {entry.get('score', 0)} in contest {contest_id}")
                
                # If no handles were found in this batch, we might want to continue
                # looking through more pages if there are more results
                offset += limit
                
                # Sleep to avoid hitting rate limits
                await asyncio.sleep(1)
                
            except (ClientError, json.JSONDecodeError) as e:
                if isinstance(e, aiohttp.ClientResponseError) and e.status == 429:
                    logger.error("Rate limit exceeded", error=str(e), exc_info=True)
                    raise RateLimitError(f"Rate limit exceeded: {e}")
                logger.error(f"Failed to get contest leaderboard for {contest_id}", error=str(e), exc_info=True)
                break
                
        return results
    
    async def get_user_scores_from_cache(self, handle: str) -> Dict[str, float]:
        """Get scores for a user from cache across all contests
        
        Args:
            handle (str): HackerRank handle
            
        Returns:
            Dict[str, float]: Dictionary mapping contest IDs to scores
        """
        if not handle or handle == "#n/a" or "@" in handle:
            return {}
            
        # Ensure cache is initialized (cache should be initialized separately before calling this method)
        if not self.is_cache_initialized:
            logger.warning("Cache not initialized when trying to get user scores from cache")
            return {}
            
        # Look up user in cache
        handle = handle.lower()
        results = {}
        
        if handle in self.user_cache:
            # Get all contest IDs for this user
            contest_ids = list(self.user_cache[handle].keys())
            
            # Instead of checking each contest separately, preload cache entries for all contests
            # that need to be checked
            fresh_cache_entries = {}
            
            for contest_id in contest_ids:
                try:
                    cache_entry = self.cache_repository.get_cache_entry(
                        Platform.HACKERRANK, 
                        contest_id,
                        check_freshness=True  # Only use if not stale
                    )
                    
                    if cache_entry:
                        fresh_cache_entries[contest_id] = cache_entry
                except Exception as e:
                    logger.error(f"Error checking cache freshness for contest {contest_id}: {e}")
            
            # Now process all contests
            for contest_id, entry in self.user_cache[handle].items():
                if contest_id in fresh_cache_entries:
                    # If we have a fresh cache, find the user in it
                    found = False
                    for user_entry in fresh_cache_entries[contest_id].entries:
                        user_handle = user_entry.get("hacker", "").lower()
                        if user_handle == handle:
                            results[contest_id] = user_entry.get('score', 0)
                            found = True
                            break
                    
                    # If user not found in fresh cache, they might have been removed
                    if not found:
                        logger.debug(f"User {handle} not found in fresh cache for contest {contest_id}")
                else:
                    # Use in-memory cache as fallback
                    results[contest_id] = entry.get('score', 0)
                
        return results
        
    async def get_user_scores(self, handles: List[str], contest_urls: List[str]) -> Dict[str, float]:
        """Get scores for multiple users across multiple contests
        
        Args:
            handles (List[str]): List of HackerRank handles
            contest_urls (List[str]): List of HackerRank contest URLs
            
        Returns:
            Dict[str, float]: Dictionary mapping handles to total scores
        """
        if not handles or not contest_urls:
            return {}
            
        # Convert to lowercase for case-insensitive matching
        handles_set = {h.lower() for h in handles if h and h != "#n/a" and "@" not in h}
        if not handles_set:
            return {}
        
        # Initialize cache if not already done
        if not self.is_cache_initialized:
            await self.initialize_cache(contest_urls)
            
        total_scores = {handle: 0 for handle in handles_set}
        
        # First try to get scores from cache
        for handle in handles_set:
            cached_scores = await self.get_user_scores_from_cache(handle)
            total_scores[handle] = sum(cached_scores.values())
            
        # If we got scores for all users from cache, return
        if all(score > 0 for score in total_scores.values()):
            logger.info(f"Retrieved all scores from cache for {len(handles_set)} users")
            return total_scores
            
        # Otherwise, fetch any missing data from API
        for i, contest_url in enumerate(contest_urls):
            logger.debug(f"Processing contest: ({i+1}/{len(contest_urls)}) {contest_url}")
            
            try:
                contest_scores = await self.get_contest_leaderboard(contest_url, handles_set)
                
                # Add contest scores to total scores
                for handle, score in contest_scores.items():
                    total_scores[handle] += score
                    
            except RateLimitError:
                # Wait and try again
                logger.warning(f"Rate limit hit, waiting for 60 seconds before continuing")
                await asyncio.sleep(60)
                try:
                    contest_scores = await self.get_contest_leaderboard(contest_url, handles_set)
                    
                    # Add contest scores to total scores
                    for handle, score in contest_scores.items():
                        total_scores[handle] += score
                except Exception as e:
                    logger.error(f"Failed to process contest {contest_url} after retry", error=str(e), exc_info=True)
                    continue
            except Exception as e:
                logger.error(f"Failed to process contest {contest_url}", error=str(e), exc_info=True)
                continue
                
        return total_scores 
import time
import asyncio
from typing import List, Dict, Any, Optional

from core.exceptions import ScraperError, RateLimitError, UserNotFoundError
from core.logging import get_logger
from core.constants import Platform, College, Batch
from db.models import Participant, PlatformStatus
from platforms.base import BasePlatformService
from platforms.hackerrank.client import HackerRankClient
from utils.hackerrank_utils import get_contest_urls_for_college_batch, load_contests_config

logger = get_logger(__name__)

class HackerRankService(BasePlatformService):
    """HackerRank platform service for data retrieval and verification"""
    
    def __init__(self) -> None:
        """Initialize the service"""
        super().__init__()
        self.contests_config = load_contests_config()
        # Cache for contest URLs to avoid redundant lookups
        self.contest_urls_cache = {}  # Format: {(college.value, batch.value): contest_urls}
        # Flag to track if we've warmed up the cache
        self.cache_initialized = False
        
    def _create_client(self) -> HackerRankClient:
        """Create the HackerRank client"""
        return HackerRankClient()
    
    async def init_client(self):
        """Initialize the client and warm up the cache"""
        await super().init_client()
        
        # Warm up cache if not already done
        if not self.cache_initialized:
            await self._warm_up_cache()
            self.cache_initialized = True
    
    async def _warm_up_cache(self):
        """Warm up the cache with all contests"""
        # Get all college-batch combinations
        all_contest_urls = []
        
        for college in College:
            for batch in Batch:
                # Get contest URLs for this college and batch
                urls = self._get_contest_urls(college, batch)
                if urls:
                    all_contest_urls.extend(urls)
        
        # Remove duplicates while preserving order
        unique_urls = list(dict.fromkeys(all_contest_urls))
        
        if unique_urls:
            logger.info(f"Warming up HackerRank cache with {len(unique_urls)} unique contests")
            await self.client.initialize_cache(unique_urls)
            logger.info("Cache warmup complete")
        else:
            logger.warning("No contest URLs found for cache warmup")
        
    def _get_contest_urls(self, college: College, batch: Batch) -> List[str]:
        """Get contest URLs with caching
        
        Args:
            college (College): College enum value
            batch (Batch): Batch enum value
            
        Returns:
            List[str]: List of contest URLs
        """
        cache_key = (college.value, batch.value)
        
        # Check if URLs are in cache
        if cache_key in self.contest_urls_cache:
            return self.contest_urls_cache[cache_key]
            
        # Get from config and cache the result
        urls = get_contest_urls_for_college_batch(college, batch, self.contests_config)
        self.contest_urls_cache[cache_key] = urls
        return urls
        
    async def get_participant_data(self, participant: Participant) -> PlatformStatus:
        """Get data for a participant
        
        Args:
            participant (Participant): The participant to get data for
            
        Returns:
            PlatformStatus: The participant's status on HackerRank
        """
        username = participant.platforms[Platform.HACKERRANK.value].handle
        if not username or username == "#n/a":
            return PlatformStatus(handle=username, exists=False)
            
        try:
            # First verify if the profile exists
            profile_exists = await self.client.verify_user_profile(username)
            if not profile_exists:
                logger.error("User profile does not exist", 
                            username=username, 
                            hall_ticket_no=participant.hall_ticket_no)
                return PlatformStatus(handle=username, exists=False)
                
            # Get college and batch from participant
            college = College(participant.college)
            batch = Batch(participant.batch)
            
            # Get contest URLs for this college and batch using cached method
            contest_urls = self._get_contest_urls(college, batch)
            
            if not contest_urls:
                logger.warning(
                    "No contest URLs configured for college and batch",
                    college=college.value,
                    batch=batch.value
                )
                return PlatformStatus(handle=username, exists=True, rating=0)
                
            # Get scores from all configured contests
            scores = await self.client.get_user_scores([username], contest_urls)
            
            # Get the total score for this participant
            total_score = scores.get(username.lower(), 0)
            
            return PlatformStatus(
                handle=username,
                rating=total_score,
                exists=True
            )
            
        except RateLimitError as e:
            logger.error(
                "Rate limit exceeded. Waiting for 60 seconds.",
                error=str(e),
                exc_info=True,
            )
            await asyncio.sleep(60)
            return await self._retry_get_participant_data(participant, e)
            
        except ScraperError as e:
            logger.error("Failed to get participant data", 
                        error=str(e), 
                        exc_info=True)
            raise
            
    async def _retry_get_participant_data(self, participant: Participant, error: Exception) -> PlatformStatus:
        """Retry getting participant data after rate limit error
        
        Args:
            participant (Participant): The participant to get data for
            error (Exception): The error that caused the retry
            
        Returns:
            PlatformStatus: The participant's status
        """
        try:
            return await self.get_participant_data(participant)
        except RateLimitError:
            logger.error(
                "Rate limit exceeded again. Waiting for 60 seconds.",
                error=str(error),
                exc_info=True,
            )
            raise
            
    async def process_batch(self, participants: List[Participant]) -> List[Participant]:
        """Process a batch of participants
        
        Args:
            participants (List[Participant]): List of participants to process
            
        Returns:
            List[Participant]: Updated list of participants with HackerRank data
        """
        logger.info(f"Processing batch of {len(participants)} participants for HackerRank")
        start_time = time.time()
        results = []
        
        # Group participants by college and batch to efficiently process contests
        college_batch_groups = {}
        for participant in participants:
            college = participant.college.name
            batch = participant.batch.name
            key = f"{college}{batch}"
            
            if key not in college_batch_groups:
                college_batch_groups[key] = []
                
            college_batch_groups[key].append(participant)
            
        # Process each group
        for key, group_participants in college_batch_groups.items():
            college, batch_str = key.split('_')
            
            try:
                college_enum = College[college]
                batch_enum = Batch[f"_{batch_str}"] # Doing this because the batch enum is defined with an underscore (Example: _2025)
                
                # Get contest URLs for this college and batch using cached method
                contest_urls = self._get_contest_urls(college_enum, batch_enum)
                
                if not contest_urls:
                    logger.warning(
                        "No contest URLs configured for college and batch",
                        college=college,
                        batch=batch_str
                    )
                    # Still process participants individually to check profile existence
                    for participant in group_participants:
                        await self._process_single_participant(participant, results, start_time, len(participants))
                    continue
                    
                # Get all handles for this group
                handles = []
                for participant in group_participants:
                    handle = participant.platforms[Platform.HACKERRANK.value].handle
                    if handle and handle != "#n/a":
                        handles.append(handle)
                        
                if not handles:
                    # No valid handles in this group
                    continue
                    
                # Get scores for all participants in this group
                try:
                    scores = await self.client.get_user_scores(handles, contest_urls)
                    
                    # Update participants with their scores
                    for participant in group_participants:
                        handle = participant.platforms[Platform.HACKERRANK.value].handle
                        if handle and handle != "#n/a":
                            score = scores.get(handle.lower(), 0)

                            # If user is already verified, skip verification
                            if participant.platforms[Platform.HACKERRANK.value].exists:
                                profile_exists = True
                            else:
                                # First verify if the profile exists
                                profile_exists = await self.client.verify_user_profile(handle)
                            
                            platform_status = PlatformStatus(
                                handle=handle,
                                rating=score if profile_exists else 0,
                                exists=profile_exists
                            )
                            
                            participant.platforms[Platform.HACKERRANK.value] = platform_status
                            results.append(participant)
                            
                            # Log progress
                            self._log_progress(len(results), len(participants), start_time, participant)
                            
                except RateLimitError:
                    # If rate limited, process participants individually
                    await asyncio.sleep(60)
                    for participant in group_participants:
                        await self._process_single_participant(participant, results, start_time, len(participants))
                        
            except Exception as e:
                logger.error(
                    f"Failed to process college/batch group {key}",
                    error=str(e),
                    exc_info=True
                )
                # Still try to process participants individually
                for participant in group_participants:
                    await self._process_single_participant(participant, results, start_time, len(participants))
                    
        logger.info("Processed batch", count=len(results))
        return results
        
    async def _process_single_participant(self, participant: Participant, results: List[Participant], start_time: float, total_count: int) -> None:
        """Process a single participant
        
        Args:
            participant (Participant): Participant to process
            results (List[Participant]): List to add the processed participant to
            start_time (float): Processing start time
            total_count (int): Total number of participants
        """
        try:
            result = await self.get_participant_data(participant)
            participant.platforms[Platform.HACKERRANK.value] = result
            results.append(participant)
            
            # Log progress
            self._log_progress(len(results), total_count, start_time, participant)
            
        except RateLimitError:
            await asyncio.sleep(60)
            try:
                result = await self._retry_get_participant_data(participant, None)
                participant.platforms[Platform.HACKERRANK.value] = result
                results.append(participant)
                
                # Log progress
                self._log_progress(len(results), total_count, start_time, participant)
                
            except RateLimitError:
                logger.error(
                    "Rate limit exceeded after retry, skipping participant",
                    hall_ticket_no=participant.hall_ticket_no
                )
            except (ScraperError, UserNotFoundError):
                logger.error(
                    "Failed to process participant after retry",
                    hall_ticket_no=participant.hall_ticket_no
                )
        except (ScraperError, UserNotFoundError):
            logger.error(
                "Failed to process participant",
                hall_ticket_no=participant.hall_ticket_no
            )
            
    def _log_progress(self, processed_count: int, total_count: int, start_time: float, participant: Participant) -> None:
        """Log progress information
        
        Args:
            processed_count (int): Number of processed participants
            total_count (int): Total number of participants
            start_time (float): Processing start time
            participant (Participant): Current participant
        """
        elapsed_time = time.time() - start_time
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        expected_time = elapsed_time * total_count / processed_count if processed_count > 0 else 0
        expected_hours, expected_remainder = divmod(expected_time, 3600)
        expected_minutes, expected_seconds = divmod(expected_remainder, 60)
        
        logger.info(
            f"({processed_count}/{total_count})",
            handle=participant.platforms[Platform.HACKERRANK.value].handle,
            hall_ticket_no=participant.hall_ticket_no,
            rating=participant.platforms[Platform.HACKERRANK.value].rating,
            ETA=f"({int(hours):02d}:{int(minutes):02d}:{int(seconds):02d} / {int(expected_hours):02d}:{int(expected_minutes):02d}:{int(expected_seconds):02d})",
        )
        
    async def verify_participant(self, participant: Participant) -> bool:
        """Verify a participant's handle
        
        Args:
            participant (Participant): The participant to verify
            
        Returns:
            bool: True if the handle is valid, False otherwise
        """
        username = participant.platforms[Platform.HACKERRANK.value].handle
        if not username or username == "#n/a":
            return False
            
        try:
            # Simply check if the profile exists
            return await self.client.verify_user_profile(username)
        except Exception:
            return False 
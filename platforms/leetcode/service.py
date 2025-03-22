import time
import asyncio
from typing import List, Dict, Any, Optional

from core.exceptions import ScraperError, RateLimitError, UserNotFoundError
from core.logging import get_logger
from core.constants import Platform
from db.models import Participant, PlatformStatus
from platforms.base import BasePlatformService
from platforms.leetcode.client import LeetCodeClient
from utils.leetcode_utils import extract_leetcode_rating, extract_user_info

logger = get_logger(__name__)

class LeetCodeService(BasePlatformService):
    """LeetCode platform service for data retrieval and verification"""
    
    def _create_client(self) -> LeetCodeClient:
        """Create the LeetCode client"""
        return LeetCodeClient()
        
    async def get_participant_data(self, participant: Participant) -> PlatformStatus:
        """Get data for a participant
        
        Args:
            participant (Participant): The participant to get data for
            
        Returns:
            PlatformStatus: The participant's status on LeetCode
        """
        username = participant.platforms[Platform.LEETCODE.value].handle
        if not username or username == "#n/a":
            return PlatformStatus(handle=username, exists=False)
            
        try:
            # Get user data from LeetCode
            user_data = await self.client.get_user_contest_data(username)
            
            if not user_data:
                return PlatformStatus(handle=username, exists=False)
                
            # Extract rating and additional user info
            rating, raw_data = extract_leetcode_rating(user_data)
            
            # Create platform status
            status = PlatformStatus(
                handle=username,
                rating=rating,
                exists=True,
                raw_data=raw_data
            )
            
            return status
            
        except UserNotFoundError:
            logger.error(f"User not found: {username}")
            return PlatformStatus(handle=username, exists=False)
            
        except RateLimitError as e:
            logger.error(
                "Rate limit exceeded. Waiting for 60 seconds.",
                error=str(e),
                exc_info=True,
            )
            await asyncio.sleep(60)
            return await self._retry_get_participant_data(participant, e)
            
        except ScraperError as e:
            logger.error(
                "Failed to get participant data",
                error=str(e),
                exc_info=True,
            )
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
            List[Participant]: Updated list of participants with LeetCode data
        """
        logger.info(f"Processing batch of {len(participants)} participants for LeetCode")
        start_time = time.time()
        results = []
        
        logger.info(f"Starting batch processing for {len(participants)} participants")
        
        for i, participant in enumerate(participants, start=1):
            try:
                if Platform.LEETCODE.value not in participant.platforms:
                    logger.warning(f"No LeetCode handle for participant: {participant.hall_ticket_no}")
                    continue
                    
                result = await self.get_participant_data(participant)
                participant.platforms[Platform.LEETCODE.value] = result
                results.append(participant)
                
                # Log progress information
                elapsed_time = time.time() - start_time
                hours, remainder = divmod(elapsed_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                expected_time = elapsed_time * len(participants) / i
                expected_hours, expected_remainder = divmod(expected_time, 3600)
                expected_minutes, expected_seconds = divmod(expected_remainder, 60)
                
                log_fields = {
                    "handle": participant.platforms[Platform.LEETCODE.value].handle,
                    "hall_ticket_no": participant.hall_ticket_no,
                    "rating": participant.platforms[Platform.LEETCODE.value].rating,
                    "ETA": f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d} / {int(expected_hours):02d}:{int(expected_minutes):02d}:{int(expected_seconds):02d}"
                }
                
                logger.info("Processing participant", **log_fields)
                
                # Ensure we don't hit rate limits (1 req/s should be safe)
                await asyncio.sleep(1)
                
            except RateLimitError:
                logger.error(f"Rate limit hit, waiting 60 seconds before retry ({i}/{len(participants)})")
                await asyncio.sleep(60)
                try:
                    result = await self._retry_get_participant_data(participant, None)
                    participant.platforms[Platform.LEETCODE.value] = result
                    results.append(participant)
                except RateLimitError:
                    logger.error(f"Rate limit persists, skipping participant")
                    continue
                except (ScraperError, UserNotFoundError) as e:
                    logger.error(
                        f"Failed to process participant ({i}/{len(participants)})",
                        handle=participant.platforms[Platform.LEETCODE.value].handle,
                        error=str(e)
                    )
                    continue
            except (ScraperError, UserNotFoundError) as e:
                logger.error(
                    f"Failed to process participant ({i}/{len(participants)})",
                    handle=participant.platforms[Platform.LEETCODE.value].handle,
                    error=str(e)
                )
                continue
                
        elapsed_time = time.time() - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        
        logger.info(
            "Completed batch processing", 
            count=len(results),
            total_participants=len(participants),
            time_taken=f"{int(minutes)}m {int(seconds)}s"
        )
        
        return results
        
    async def verify_participant(self, participant: Participant) -> bool:
        """Verify a participant's handle
        
        Args:
            participant (Participant): The participant to verify
            
        Returns:
            bool: True if the handle is valid, False otherwise
        """
        if Platform.LEETCODE.value not in participant.platforms:
            return False
            
        username = participant.platforms[Platform.LEETCODE.value].handle
        if not username or username == "#n/a":
            return False
            
        try:
            return await self.client.verify_user_exists(username)
        except (ScraperError, RateLimitError):
            return False 
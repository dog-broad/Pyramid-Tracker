import time
import asyncio
from typing import List, Dict, Any, Optional

from core.exceptions import ScraperError, RateLimitError, UserNotFoundError
from core.logging import get_logger
from core.constants import Platform
from db.models import Participant, PlatformStatus
from platforms.base import BasePlatformService
from platforms.geeksforgeeks.client import GeeksForGeeksClient
from utils.gfg_utils import calculate_gfg_rating

logger = get_logger(__name__)

class GeeksForGeeksService(BasePlatformService):
    """GeeksForGeeks platform service for data retrieval and verification"""
    
    def __init__(self) -> None:
        """Initialize the service and start cache initialization"""
        super().__init__()
        # Start cache initialization as background task
        asyncio.create_task(self._initialize_cache())
        
    async def _initialize_cache(self) -> None:
        """Initialize the client cache"""
        try:
            await self.client.initialize_cache()
        except Exception as e:
            logger.error("Failed to initialize GeeksForGeeks cache", error=str(e), exc_info=True)
    
    def _create_client(self) -> GeeksForGeeksClient:
        """Create the GeeksForGeeks client"""
        return GeeksForGeeksClient()
        
    async def get_participant_data(self, participant: Participant) -> PlatformStatus:
        """Get data for a participant
        
        Args:
            participant (Participant): The participant to get data for
            
        Returns:
            PlatformStatus: The participant's status on GeeksForGeeks
        """
        username = participant.platforms[Platform.GEEKSFORGEEKS.value].handle
        if not username or username == "#n/a":
            return PlatformStatus(handle=username, exists=False)
            
        try:
            # Ensure cache is initialized
            if not self.client.is_cache_initialized:
                logger.info("Waiting for cache initialization to complete...")
                await self.client.initialize_cache()
                
            # Get user data from GeeksForGeeks
            user_data = await self.client.get_user_data(username)
            
            if not user_data:
                return PlatformStatus(handle=username, exists=False)
                
            # Extract scores
            practice_score = user_data.get("practice", {}).get("score", 0)
            weekly_score = user_data.get("weekly_contest", {}).get("score", 0)
            
            # Calculate weighted rating (75% weekly, 25% practice)
            weighted_rating = calculate_gfg_rating(weekly_score, practice_score, 0.75)
            
            return PlatformStatus(
                handle=username,
                rating=weighted_rating,
                exists=True,
                raw_data=user_data
            )
            
        except UserNotFoundError:
            logger.error("User not found", 
                        username=username, 
                        hall_ticket_no=participant.hall_ticket_no)
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
            List[Participant]: Updated list of participants with GeeksForGeeks data
        """
        start_time = time.time()
        results = []
        
        # Ensure cache is initialized before processing batch
        if not self.client.is_cache_initialized:
            logger.info("Initializing cache before batch processing...")
            await self.client.initialize_cache()
            logger.info("Cache initialization completed, proceeding with batch")
        
        for i, participant in enumerate(participants, start=1):
            try:
                result = await self.get_participant_data(participant)
                participant.platforms[Platform.GEEKSFORGEEKS.value] = result
                results.append(participant)
                
                # Log progress information
                elapsed_time = time.time() - start_time
                hours, remainder = divmod(elapsed_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                expected_time = elapsed_time * len(participants) / i
                expected_hours, expected_remainder = divmod(expected_time, 3600)
                expected_minutes, expected_seconds = divmod(expected_remainder, 60)
                
                logger.info(
                    f"({i}/{len(participants)})",
                    handle=participant.platforms[Platform.GEEKSFORGEEKS.value].handle,
                    hall_ticket_no=participant.hall_ticket_no,
                    rating=participant.platforms[Platform.GEEKSFORGEEKS.value].rating,
                    ETA=f"({int(hours):02d}:{int(minutes):02d}:{int(seconds):02d} / {int(expected_hours):02d}:{int(expected_minutes):02d}:{int(expected_seconds):02d})",
                )
                
            except RateLimitError:
                await asyncio.sleep(60)
                try:
                    result = await self._retry_get_participant_data(participant, None)
                    participant.platforms[Platform.GEEKSFORGEEKS.value] = result
                    results.append(participant)
                except RateLimitError:
                    continue
                except (ScraperError, UserNotFoundError):
                    logger.info(
                        f"Failed to process participant ({i}/{len(participants)})",
                        handle=participant.platforms[Platform.GEEKSFORGEEKS.value].handle,
                    )
                    continue
            except (ScraperError, UserNotFoundError):
                logger.error(
                    f"Failed to process participant ({i}/{len(participants)})",
                    handle=participant.platforms[Platform.GEEKSFORGEEKS.value].handle,
                )
                continue
            finally:
                # No need to sleep between participants now that we have a cache
                pass
                
        logger.info("Processed batch", count=len(results))
        return results
        
    async def verify_participant(self, participant: Participant) -> bool:
        """Verify a participant's handle
        
        Args:
            participant (Participant): The participant to verify
            
        Returns:
            bool: True if the handle is valid, False otherwise
        """
        username = participant.platforms[Platform.GEEKSFORGEEKS.value].handle
        if not username or username == "#n/a":
            return False
            
        try:
            return await self.client.verify_user_exists(username)
        except (ScraperError, RateLimitError):
            return False
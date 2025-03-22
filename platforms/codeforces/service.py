# platforms/codeforces/service.py
import time
import asyncio
from typing import List, Dict, Any, Optional

from core.exceptions import ScraperError, RateLimitError, UserNotFoundError
from core.logging import get_logger
from core.constants import Platform
from db.models import Participant, PlatformStatus
from platforms.base import BasePlatformService
from platforms.codeforces.client import CodeforcesClient

logger = get_logger(__name__)

class CodeforcesService(BasePlatformService):
    """Codeforces platform service for data retrieval and verification"""
    
    def _create_client(self) -> CodeforcesClient:
        """Create the Codeforces client"""
        return CodeforcesClient()
        
    async def get_participant_data(self, participant: Participant) -> PlatformStatus:
        """Get data for a participant
        
        Args:
            participant (Participant): The participant to get data for
            
        Returns:
            PlatformStatus: The participant's status on Codeforces
        """
        username = participant.platforms[Platform.CODEFORCES.value].handle
        if not username or username == "#n/a":
            return PlatformStatus(handle=username, exists=False)
            
        try:
            user_data = await self.client.get_single_user_info(username)
            if not user_data:
                return PlatformStatus(handle=username, exists=False)
                
            # Extract rating information
            rating = user_data.get("rating", 0)
            
            return PlatformStatus(
                handle=username,
                rating=rating,
                exists=True,
                raw_data=user_data
            )
            
        except UserNotFoundError:
            logger.error(" User not found", 
                        username=username, 
                        hall_ticket_no=participant.hall_ticket_no)
            return PlatformStatus(handle=username, exists=False)
            
        except RateLimitError as e:
            logger.error(
                " Rate limit exceeded. Waiting for 60 seconds.",
                error=str(e),
                exc_info=True,
            )
            await asyncio.sleep(60)
            return await self._retry_get_participant_data(participant, e)
            
        except ScraperError as e:
            logger.error(" Failed to get participant data", 
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
                " Rate limit exceeded again. Waiting for 60 seconds.",
                error=str(error),
                exc_info=True,
            )
            raise
            
    async def process_batch(self, participants: List[Participant]) -> List[Participant]:
        """Process a batch of participants
        
        Args:
            participants (List[Participant]): List of participants to process
            
        Returns:
            List[Participant]: Updated list of participants with Codeforces data
        """
        logger.info(f"Processing batch of {len(participants)} participants for Codeforces")
        start_time = time.time()
        results = []
        
        for i, participant in enumerate(participants, start=1):
            try:
                result = await self.get_participant_data(participant)
                participant.platforms[Platform.CODEFORCES.value] = result
                results.append(participant)
                
                # Log progress information
                elapsed_time = time.time() - start_time
                hours, remainder = divmod(elapsed_time, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                expected_time = elapsed_time * len(participants) / i
                expected_hours, expected_remainder = divmod(expected_time, 3600)
                expected_minutes, expected_seconds = divmod(expected_remainder, 60)
                
                logger.info(
                    f" ({i}/{len(participants)})",
                    handle=participant.platforms[Platform.CODEFORCES.value].handle,
                    hall_ticket_no=participant.hall_ticket_no,
                    rating=participant.platforms[Platform.CODEFORCES.value].rating,
                    ETA=f"({int(hours):02d}:{int(minutes):02d}:{int(seconds):02d} / {int(expected_hours):02d}:{int(expected_minutes):02d}:{int(expected_seconds):02d})",
                )
                
            except RateLimitError:
                await asyncio.sleep(60)
                try:
                    result = await self._retry_get_participant_data(participant, None)
                    participant.platforms[Platform.CODEFORCES.value] = result
                    results.append(participant)
                except RateLimitError:
                    continue
                except (ScraperError, UserNotFoundError):
                    logger.info(
                        f" Failed to process participant ({i}/{len(participants)})",
                        handle=participant.platforms[Platform.CODEFORCES.value].handle,
                    )
                    continue
            finally:
                await self.client.close()
                
        logger.info(" Processed batch", count=len(results))
        return results
        
    async def verify_participant(self, participant: Participant) -> bool:
        """Verify a participant's handle
        
        Args:
            participant (Participant): The participant to verify
            
        Returns:
            bool: True if the handle is valid, False otherwise
        """
        username = participant.platforms[Platform.CODEFORCES.value].handle
        if not username or username == "#n/a":
            return False
            
        try:
            user_data = await self.client.get_single_user_info(username)
            return user_data is not None
        except (UserNotFoundError, ScraperError, RateLimitError):
            return False 
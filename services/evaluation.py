from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd

from db.client import DatabaseClient
from db.models import Participant
from db.repositories import ParticipantRepository
from core.logging import get_logger
from core.constants import Platform, College, Batch

logger = get_logger(__name__)

class EvaluationService:
    """Service for evaluating participant performance"""
    
    def __init__(self, db_client: Optional[DatabaseClient] = None) -> None:
        """Initialize the service"""
        if db_client is None:
            logger.error("Database client is required")
            raise ValueError("Database client is required")
        self.db_client = db_client
        self.repository = ParticipantRepository(self.db_client)
    
    def calculate_total_rating(self, participant: Participant) -> float:
        """Calculate the total rating for a participant
        
        The total rating is the sum of ratings from all platforms.
        If a platform rating is not available, it is treated as 0.
        
        Args:
            participant (Participant): The participant to calculate total rating for
            
        Returns:
            float: The calculated total rating
        """
        total = 0.0
        for platform in Platform:
            rating = participant.platforms.get(platform.value)
            if rating and rating.rating is not None:
                total += rating.rating
        return total
        
    def evaluate_batch(self, college: College, batch: Batch) -> List[Participant]:
        """Evaluate all participants in a batch
        
        Args:
            college (College): The college name
            batch (Batch): The batch number
            
        Returns:
            List[Participant]: The updated list of participants
        """
        logger.info(f"Evaluating batch: {college.name}{batch.name}")

        # Get all participants
        participants = self.repository.get_all_participants(batch, college)
        logger.info(f"Retrieved {len(participants)} participants for evaluation")
        
        if not participants:
            logger.warning(f"No participants found for batch: {college.name}{batch.name}")
            return []
            
        # Calculate total ratings
        for participant in participants:
            participant.total_rating = self.calculate_total_rating(participant)
            
        # Extract non-zero ratings for percentile calculation
        valid_ratings = [p.total_rating for p in participants if p.total_rating > 0]
        
        if not valid_ratings:
            logger.warning("No valid ratings found for percentile calculation")
            return participants
            
        # Sort ratings for percentile calculation
        valid_ratings.sort()
        
        # Calculate percentiles for each participant with non-zero rating
        for participant in participants:
            if participant.total_rating > 0:
                # Find the position of this rating in the sorted list
                position = valid_ratings.index(participant.total_rating)
                # Calculate percentile (0-100 scale)
                participant.percentile = (position / len(valid_ratings)) * 100
            else:
                participant.percentile = 0.0
            
        # Update participants in database
        for participant in participants:
            self.repository.update_participant(participant)
            
        logger.info(f"Evaluation completed for {len(participants)} participants")
        return participants
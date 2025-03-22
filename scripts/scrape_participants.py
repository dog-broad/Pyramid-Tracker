from core.constants import Platform, Batch, College
from core.logging import get_logger

from db.client import DatabaseClient
from db.repositories import ParticipantRepository

from platforms.codechef import CodeChefService
from platforms.codeforces import CodeforcesService
from platforms.hackerrank import HackerRankService
from platforms.geeksforgeeks import GeeksForGeeksService
from platforms.leetcode import LeetCodeService

logger = get_logger(__name__)

async def scrape_participants(college: str, batch: str, platform: str, test: bool, sample: int) -> None:
    """Scrape participant data from a platform for a specific college and batch."""
    logger.info("Scraping users", college=college, batch=batch, platform=platform)
    batch_enum = Batch[batch]
    college_enum = College[college]
    db_client = DatabaseClient(college_enum.name)
    repo = ParticipantRepository(db_client)
    
    if test:
        logger.info("Test mode enabled", sample_size=sample)
        participants = repo.get_random_participants(batch_enum, college_enum, sample)
    else:
        participants = repo.get_all_participants(batch_enum, college_enum)
    
    platform_enum = Platform[platform]
    service = None
    
    try:
        # Select the appropriate service based on the platform
        if platform == Platform.CODECHEF.name:
            service = CodeChefService()
        elif platform == Platform.CODEFORCES.name:
            service = CodeforcesService()
        elif platform == Platform.HACKERRANK.name:
            service = HackerRankService()
        elif platform == Platform.GEEKSFORGEEKS.name:
            service = GeeksForGeeksService()
        elif platform == Platform.LEETCODE.name:
            service = LeetCodeService()
        
        if service:
            results = await service.process_batch(participants)
            repo.update_participants(results)
            logger.info("Scraping completed successfully", platform=platform, participant_count=len(results))
        else:
            logger.error("Unknown platform", platform=platform)
    finally:
        if service:
            await service.close()

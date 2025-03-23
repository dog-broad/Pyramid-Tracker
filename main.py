import asyncio
import os
import time
import click
from typing import List, Optional, Dict, Any, Callable, Coroutine

from core.constants import Platform, Batch, College
from core.logging import configure_logging, get_logger

from db.client import DatabaseClient
from db.repositories import ParticipantRepository

from platforms.codechef import CodeChefService
from platforms.codeforces import CodeforcesService
from platforms.hackerrank import HackerRankService
from platforms.geeksforgeeks import GeeksForGeeksService
from platforms.leetcode import LeetCodeService

from services.evaluation import EvaluationService
from services.leaderboard import LeaderboardService

from scripts.upload_participants import upload_participants

logger = get_logger(__name__)


#=======================================
# General option for setting up logging
#=======================================
@click.group()
@click.option("--debug", is_flag=True, help="Enable debug mode with verbose logging", default=False)
@click.option("--log-file", type=str, help="Path to the log file", default="logfile.log")
def cli(debug: bool, log_file: str) -> None:
    """🔥 Pyramid-Tracker CLI: Track competitive programming performance across platforms! 🚀
    
    This tool helps you track participants' performance on various coding platforms.
    Use the commands below to manage participants and scrape data.
    """
    configure_logging(debug, log_file)
    
#=======================================
# Users Upload CLI
#=======================================
@cli.command()
@click.option("--college", type=click.Choice([c.name for c in College]), help="College name (e.g., CMRIT)", required=True)
@click.option("--batch", type=click.Choice([b.name for b in Batch]), help="Batch number (e.g., _2025)", required=True)
def upload_users(college: str, batch: str) -> None:
    """📤 Upload participants from CSV files to the database.
    
    This command reads participant data from CSV files defined in user_details.yaml
    and uploads them to MongoDB. Each participant will be associated with the 
    specified college and batch.
    
    Example: python main.py upload-users --college CMRIT --batch _2025
    """
    logger.info("Uploading users", college=college, batch=batch)
    upload_participants(college, batch)

    
#=======================================
# Users Verification CLI
#=======================================
@cli.command()
@click.option("--college", type=str, help="College name (e.g., CMRIT)", required=True)
@click.option("--batch", type=str, help="Batch number (e.g., _2025)", required=True)
def verify_users(college: str, batch: str) -> None:
    """🔍 Verify that users exist in the database.
    
    This command checks if all users for the specified college and batch
    exist in the database. It's useful for validating data before scraping.
    
    Example: python main.py verify-users --college CMRIT --batch _2025
    """
    logger.info("Verifying users", college=college, batch=batch)
    db_client = DatabaseClient()
    repo = ParticipantRepository(db_client)
    repo.verify_users(college, batch)


def get_platform_service(platform: str):
    """Helper function to get the appropriate platform service."""
    platform_services = {
        Platform.CODECHEF.name: CodeChefService,
        Platform.CODEFORCES.name: CodeforcesService,
        Platform.HACKERRANK.name: HackerRankService,
        Platform.GEEKSFORGEEKS.name: GeeksForGeeksService,
        Platform.LEETCODE.name: LeetCodeService,
    }
    
    service_class = platform_services.get(platform)
    return service_class() if service_class else None


def get_participants(repo, batch_enum, college_enum, test=False, sample=20):
    """Helper function to get participants based on test mode."""
    if test:
        logger.info("Test mode enabled", sample_size=sample)
        return repo.get_random_participants(batch_enum, college_enum, sample)
    return repo.get_all_participants(batch_enum, college_enum)


# =======================================
# Scrape CLI
# =======================================
@cli.command()
@click.option("--college", type=click.Choice([c.name for c in College]), help="College name (e.g., CMRIT)", required=True)
@click.option("--batch", type=click.Choice([b.name for b in Batch]), help="Batch number (e.g., _2025)", required=True)
@click.option("--platform", type=click.Choice([p.name for p in Platform]), help="Platform name", required=True)
@click.option("--test", is_flag=True, help="Enable test mode with limited participants", default=False)
@click.option("--sample", type=int, help="Number of random participants to select in test mode", default=20)
def scrape(college: str, batch: str, platform: str, test: bool, sample: int) -> None:
    """🕸️ Scrape participant data from coding platforms.
    
    This command scrapes data from the specified platform for all participants 
    in the given college and batch. The data is then stored in the database.
    
    Example: python main.py scrape --college CMRIT --batch _2025 --platform CODECHEF
    """
    asyncio.run(_scrape(college, batch, platform, test, sample))


async def _scrape(college: str, batch: str, platform: str, test: bool, sample: int) -> None:
    logger.info("Scraping users", college=college, batch=batch, platform=platform)
    batch_enum = Batch[batch]
    college_enum = College[college]
    db_client = DatabaseClient(college_enum.name)
    repo = ParticipantRepository(db_client)
    
    participants = get_participants(repo, batch_enum, college_enum, test, sample)
    if not participants:
        logger.error("No participants found", college=college, batch=batch)
        return
    
    service = get_platform_service(platform)
    if not service:
        logger.error("Unknown platform", platform=platform)
        return
        
    try:
        results = await service.process_batch(participants)
        repo.update_participants(results)
        logger.info("Scraping completed successfully", platform=platform, participant_count=len(results))
    finally:
        await service.close()


# =======================================
# Multi-Platform Scrape CLI
# =======================================
@cli.command()
@click.option("--college", type=click.Choice([c.name for c in College]), help="College name (e.g., CMRIT)", required=True)
@click.option("--batch", type=click.Choice([b.name for b in Batch]), help="Batch number (e.g., _2025)", required=True)
@click.option("--platforms", type=click.Choice([p.name for p in Platform] + ["ALL"]), multiple=True, help="Platform names (can specify multiple)", required=True)
@click.option("--test", is_flag=True, help="Enable test mode with limited participants", default=False)
@click.option("--sample", type=int, help="Number of random participants to select in test mode", default=20)
def multi_scrape(college: str, batch: str, platforms: List[str], test: bool, sample: int) -> None:
    """🔄 Scrape participant data from multiple platforms at once.
    
    This command scrapes data from multiple platforms for all participants
    in the given college and batch. Use 'ALL' to scrape from all supported platforms.
    
    Example: python main.py multi-scrape --college CMRIT --batch _2025 --platforms CODECHEF CODEFORCES
    """
    asyncio.run(_multi_scrape(college, batch, platforms, test, sample))


async def process_platforms(platform_list: List[str], participants: List[Any]) -> Dict[str, Any]:
    """Process multiple platforms and return services and tasks."""
    services = {}
    tasks = {}
    
    for platform in platform_list:
        try:
            service = get_platform_service(platform)
            if service:
                tasks[platform] = service.process_batch(participants)
                services[platform] = service
        except Exception as e:
            logger.error(f"Error initializing {platform}", error=str(e), exc_info=True)
    
    return services, tasks


async def process_results(tasks: Dict[str, Coroutine], repo: ParticipantRepository) -> None:
    """Process the results from platform tasks and update the database."""
    if not tasks:
        return
        
    # Run tasks
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    
    # Process results and update database
    for platform, result in zip(tasks.keys(), results):
        if isinstance(result, Exception):
            logger.error(f"Error processing {platform}", error=str(result), exc_info=True)
            continue
            
        # Save to database
        logger.info(f"Updating {len(result)} participants with {platform} data")
        repo.update_participants(result)
        logger.info(f"Updated {len(result)} participants with {platform} data")


async def close_services(services: Dict[str, Any], start_time: float = None) -> None:
    """Close all platform services."""
    for service in services.values():
        if start_time:
            elapsed_time = time.time() - start_time
            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            logger.info(
                f"Service {service.__class__.__name__} took {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds to complete"
            )
        await service.close()


async def _multi_scrape(college: str, batch: str, platforms: List[str], test: bool, sample: int) -> None:
    """
    Helper function to run the multi-platform scrape.
    """
    logger.info("Running multi-platform scrape", college=college, batch=batch)
    batch_enum = Batch[batch]
    college_enum = College[college]
    db_client = DatabaseClient(college_enum.name)
    repo = ParticipantRepository(db_client)
    
    participants = get_participants(repo, batch_enum, college_enum, test, sample)
    if not participants:
        logger.error("No participants found", college=college, batch=batch)
        return
    
    platform_list = list(platforms)
    if "ALL" in platform_list:
        platform_list = [p.name for p in Platform]
        
    services, tasks = await process_platforms(platform_list, participants)
    
    try:
        await process_results(tasks, repo)
    finally:
        await close_services(services)
    
    logger.info("Multi-platform scrape completed", platforms=", ".join(platform_list))


# =======================================
# Evaluation CLI
# =======================================
@cli.command()
@click.option("--college", type=click.Choice([c.name for c in College]), help="College name (e.g., CMRIT)", required=True)
@click.option("--batch", type=click.Choice([b.name for b in Batch]), help="Batch number (e.g., _2025)", required=True)
def evaluate(college: str, batch: str) -> None:
    """📊 Evaluate participant performance across platforms.
    
    This command calculates total ratings and percentiles for all participants
    in the given college and batch based on their platform performance.
    
    Example: python main.py evaluate --college CMRIT --batch _2025
    """
    logger.info("Evaluating participants", college=college, batch=batch)
    batch_enum = Batch[batch]
    college_enum = College[college]
    
    try:
        db_client = DatabaseClient(college_enum.name)
        service = EvaluationService(db_client)
        participants = service.evaluate_batch(college_enum, batch_enum)
        logger.info("Evaluation completed successfully", participant_count=len(participants))
    except Exception as e:
        logger.error("Error during evaluation", error=str(e), exc_info=True)


# =======================================
# Leaderboard CLI
# =======================================
@cli.command()
@click.option("--college", type=click.Choice([c.name for c in College]), help="College name (e.g., CMRIT)", required=True)
@click.option("--batch", type=click.Choice([b.name for b in Batch]), help="Batch number (e.g., _2025)", required=True)
@click.option("--output", type=str, help="Output file path", default="leaderboard.xlsx")
@click.option("--charts", is_flag=True, help="Include charts in the leaderboard", default=True)
def generate_leaderboard(college: str, batch: str, output: str, charts: bool) -> None:
    """🏆 Generate a leaderboard for participants.
    
    This command generates an Excel leaderboard ranking participants
    by their total performance across all platforms for the given college and batch.
    
    Example: python main.py generate-leaderboard --college CMRIT --batch _2025 --output leaderboard.xlsx
    """
    logger.info("Generating leaderboard", college=college, batch=batch, output=output, charts=charts)
    
    try:
        batch_enum = Batch[batch]
        college_enum = College[college]
        db_client = DatabaseClient(college_enum.name)
        service = LeaderboardService(db_client)
        output_path = service.generate_leaderboard(batch_enum, college_enum, output, include_charts=charts)
        logger.info("Leaderboard generated successfully", output_path=output_path)
    except Exception as e:
        logger.error("Error generating leaderboard", error=str(e), exc_info=True)


# =======================================
# Complete Pipeline CLI
# =======================================
@cli.command()
@click.option("--college", type=click.Choice([c.name for c in College]), help="College name (e.g., CMRIT)", required=True)
@click.option("--batch", type=click.Choice([b.name for b in Batch]), help="Batch number (e.g., _2025)", required=True)
@click.option("--platforms", type=click.Choice([p.name for p in Platform] + ["ALL"]), multiple=True, help="Platform names (can specify multiple)", required=True)
@click.option("--output", type=str, help="Output leaderboard file path", default="leaderboard.xlsx")
@click.option("--charts", is_flag=True, help="Include charts in the leaderboard", default=True)
@click.option("--test", is_flag=True, help="Enable test mode with limited participants", default=False)
@click.option("--sample", type=int, help="Number of random participants to select in test mode", default=20)
def run_pipeline(college: str, batch: str, platforms: List[str], output: str, charts: bool, test: bool, sample: int) -> None:
    """🚀 Run the complete Pyramid-Tracker pipeline.

    This command executes the full pipeline:
    1. Scrape data from all selected platforms
    2. Evaluate participant performance
    3. Generate the leaderboard
    
    Example: python main.py run-pipeline --college CMRIT --batch _2025 --platforms ALL --output leaderboard.xlsx
    """
    logger.info("Running complete pipeline", college=college, batch=batch)
    asyncio.run(_run_pipeline(college, batch, platforms, output, charts, test, sample))


async def _run_pipeline(college: str, batch: str, platforms: List[str], output: str, charts: bool, test: bool, sample: int) -> None:
    """
    Helper function to run the complete pipeline.
    """
    logger.info("Running complete pipeline", college=college, batch=batch)
    start_time = time.time()
    
    # Initialize database client and repository
    batch_enum = Batch[batch]
    college_enum = College[college]
    db_client = DatabaseClient(college_enum.name)
    repo = ParticipantRepository(db_client)

    # 1. Run multi-platform scrape
    try:
        platform_list = list(platforms)
        if "ALL" in platform_list:
            platform_list = [p.name for p in Platform]
            
        logger.info("Step 1: Multi-platform scrape", platforms=", ".join(platform_list))
        
        # Get participants
        participants = get_participants(repo, batch_enum, college_enum, test, sample)
        if not participants:
            logger.error("No participants found", college=college, batch=batch)
            return
            
        logger.info(f"Retrieved {len(participants)} participants")
        
        # Setup services and tasks for each platform
        services, tasks = await process_platforms(platform_list, participants)
        
        # Process all platforms asynchronously
        await process_results(tasks, repo)
        
        # Close services
        await close_services(services, start_time)
            
    except Exception as e:
        logger.error("Error during multi-platform scrape", error=str(e), exc_info=True)
        return

    # 2. Run evaluation
    try:
        logger.info("Step 2: Evaluating participants")
        evaluation_service = EvaluationService(db_client)
        evaluation_service.evaluate_batch(college_enum, batch_enum)
        logger.info("Evaluation completed successfully")
    except Exception as e:
        logger.error("Error during evaluation", error=str(e), exc_info=True)
        return

    # 3. Generate leaderboard
    try:
        logger.info("Step 3: Generating leaderboard")
        leaderboard_service = LeaderboardService(db_client)
        output_path = leaderboard_service.generate_leaderboard(batch_enum, college_enum, output, include_charts=charts)
        logger.info("Leaderboard generated successfully", output_path=output_path)
    except Exception as e:
        logger.error("Error generating leaderboard", error=str(e), exc_info=True)
        return
        
    logger.info("Complete pipeline execution finished successfully")


if __name__ == "__main__":
    try:
        # For commands that need asyncio, we'll handle them specially
        # The scrape and run_pipeline commands are run directly via asyncio.run()
        if any(cmd in os.sys.argv for cmd in ["scrape", "run-pipeline"]):
            asyncio.run(cli())
        else:
            cli()
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
    except Exception as e:
        logger.error("An error occurred", error=str(e), exc_info=True)
from datetime import datetime, timedelta
import json
from typing import Collection, List, Optional, Dict, Any
import pandas as pd
import pymongo
from pymongo.errors import PyMongoError
import random

from db.client import DatabaseClient
from core.constants import College, Batch, Platform
from db.models import Participant, PlatformStatus, LeaderboardCache
from core.exceptions import DatabaseError
from core.logging import get_logger

logger = get_logger(__name__)

class ParticipantRepository:
    """Repository for participant data"""
    
    def __init__(self, db_client: Optional[DatabaseClient] = None) -> None:
        """Initialize the repository"""
        if db_client is None:
            logger.error("Database client is required")
            raise ValueError("Database client is required")
        self.db_client = db_client
        
    def get_collection_name(self, batch: Batch, college: College) -> str:
        """Get the collection name for a specific batch and college"""
        return f"{college.name}{batch.name}"
    
    def get_collection(self, batch: Batch, college: College) -> Collection:
        """Get the collection for a specific batch and college"""
        collection_name = self.get_collection_name(batch, college)
        return self.db_client.get_collection(collection_name)
    
    def get_or_create_collection(self, batch: Batch, college: College) -> Collection:
        """Get or create the collection for a specific batch and college"""
        collection_name = self.get_collection_name(batch, college)
        return self.db_client.get_or_create_collection(collection_name)
    
    def insert_participant(self, participant: Participant) -> None:
        """Insert a participant into the database"""
        try:
            collection = self.get_collection(participant.batch, participant.college)
            document = self._participant_to_document(participant)
            collection.insert_one(document)
            logger.info("Inserted participant", hall_ticket_no=participant.hall_ticket_no, batch=participant.batch, college=participant.college)
        except PyMongoError as e:
            logger.error("Failed to insert participant", error=str(e), hall_ticket_no=participant.hall_ticket_no, batch=participant.batch, college=participant.college, exc_info=True)
            raise DatabaseError(f"Failed to insert participant: {e}")
    
    def get_all_participants(self, batch: Batch, college: College) -> List[Participant]:
        """Get all participants for a batch and college"""
        try:
            collection = self.get_collection(batch, college)
            cursor = collection.find({})
            
            participants = []
            for doc in cursor:
                participant = self._document_to_participant(doc)
                participants.append(participant)
                
            logger.info("Retrieved participants", count=len(participants), batch=batch.name, college=college.name)
            return participants
        except PyMongoError as e:
            logger.error("Failed to retrieve participants", error=str(e), batch=batch.name, college=college.name, exc_info=True)
            raise DatabaseError(f"Failed to retrieve participants: {e}")
        
    def get_random_participants(self, batch: Batch, college: College, count: int = 10) -> List[Participant]:
        """Get random participants for a batch and college
        
        Args:
            batch (Batch): Batch
            college (College): College
            count (int): Number of participants to return
            
        Returns:
            List[Participant]: List of random participants
        """
        try:
            collection = self.get_collection(batch, college)
            
            # Use MongoDB's $sample aggregation to efficiently get random documents
            cursor = collection.aggregate([{"$sample": {"size": count}}])
            
            participants = []
            for doc in cursor:
                participant = self._document_to_participant(doc)
                participants.append(participant)
                
            actual_count = len(participants)
            if actual_count < count:
                logger.warning(f"Requested {count} random participants but only {actual_count} available.")
                if actual_count == 0:
                    logger.warning("No participants found in the database")
                    return []
                
            logger.info("Retrieved random participants", count=actual_count, batch=batch.name, college=college.name)
            return participants
            
        except PyMongoError as e:
            logger.error("Failed to retrieve random participants", error=str(e), batch=batch.name, college=college.name, exc_info=True)
            raise DatabaseError(f"Failed to retrieve random participants: {e}")
    
    def update_participant(self, participant: Participant) -> None:
        """Update a participant in the database"""
        try:
            collection = self.get_collection(participant.batch, participant.college)
            
            document = self._participant_to_document(participant)
            result = collection.update_one(
                {"hallTicketNo": participant.hall_ticket_no},
                {"$set": document},
                upsert=True
            )
            
            logger.info(
                "Updated participant",
                hall_ticket_no=participant.hall_ticket_no,
                modified=result.modified_count,
                upserted=result.upserted_id is not None
            )
        except PyMongoError as e:
            logger.error(
                "Failed to update participant",
                error=str(e),
                hall_ticket_no=participant.hall_ticket_no,
                exc_info=True
            )
            raise DatabaseError(f"Failed to update participant: {e}")
        
    def update_participants(self, participants: Collection[Participant]) -> None:
        """Update multiple participants in the database"""
        batches = set(participant.batch.name for participant in participants)
        colleges = set(participant.college.name for participant in participants)

        for participant in participants:
            self.update_participant(participant)
        
        logger.info(
            "Updated participants",
            count=len(participants),
            batches=", ".join(batches),
            colleges=", ".join(colleges)
        )
    
    def _document_to_participant(self, doc: Dict[str, Any]) -> Participant:
        """Convert a MongoDB document to a Participant object"""
        return Participant(
            hall_ticket_no=doc["hallTicketNo"],
            name=doc["name"],
            batch=Batch._value2member_map_[doc["batch"]],
            college=College._value2member_map_[doc["college"]],
            platforms={
                platform: self._document_to_platform_status(platform_doc)
                for platform, platform_doc in doc.get("platforms", {}).items()
            },
            total_rating=doc.get("totalRating", 0.0),
            percentile=doc.get("percentile", 0.0)
        )
        
    def _participant_to_document(self, participant: Participant) -> Dict[str, Any]:
        """Convert a Participant object to a MongoDB document"""
        # logger.debug("Converting participant to document", hall_ticket_no=participant.hall_ticket_no, batch=participant.batch, college=participant.college)
        return {
            "hallTicketNo": participant.hall_ticket_no,
            "name": participant.name,
            "batch": participant.batch.value,
            "college": participant.college.value,
            "platforms": {
                platform: self._platform_status_to_document(platform_status)
                for platform, platform_status in participant.platforms.items()
            },
            "totalRating": participant.total_rating,
            "percentile": participant.percentile
        }
    
    def _document_to_platform_status(self, doc: Optional[Dict[str, Any]]) -> Optional[PlatformStatus]:
        """Convert a MongoDB document to a PlatformStatus object"""
        if doc is None:
            return None
        return PlatformStatus(
            handle=doc["handle"],
            rating=doc.get("rating"),
            exists=doc.get("exists", False),
            last_updated=doc.get("lastUpdated", datetime.now()),
            raw_data=doc.get("rawData", {})
        )
    
    def _platform_status_to_document(self, status: Optional[PlatformStatus]) -> Optional[Dict[str, Any]]:
        """Convert a PlatformStatus object to a MongoDB document"""
        if status is None:
            return None
        return {
            "handle": status.handle,
            "rating": status.rating,
            "exists": status.exists,
            "lastUpdated": status.last_updated,
            "rawData": status.raw_data
        }
    
    def _dataframe_to_participants(self, df: pd.DataFrame) -> List[Participant]:
        """Convert a DataFrame to a list of Participant objects"""
        participants = []
        for _, row in df.iterrows():
            participant = Participant(
                hall_ticket_no=row.get("HallTicketNo"),
                name=row.get("Name", ""),
                batch=Batch._value2member_map_[row.get("Batch")],
                college=College._value2member_map_[row.get("College")],
                platforms={
                    Platform.CODECHEF.value: PlatformStatus(
                        handle=row.get("CodeChefHandle") if row.get("CodeChefHandle") != "" else None,
                        rating=row.get("CodeChefRating"),
                        exists=row.get("CodeChefExists"),
                        last_updated=row.get("CodeChefLastUpdated"),
                        raw_data=row.get("CodeChefRawData")
                    ),
                    Platform.CODEFORCES.value: PlatformStatus(
                        handle=row.get("CodeforcesHandle") if row.get("CodeforcesHandle") != "" else None,
                        rating=row.get("CodeforcesRating"),
                        exists=row.get("CodeforcesExists"),
                        last_updated=row.get("CodeforcesLastUpdated"),
                        raw_data=row.get("CodeforcesRawData")
                    ),
                    Platform.GEEKSFORGEEKS.value: PlatformStatus(
                        handle=row.get("GeeksForGeeksHandle") if row.get("GeeksForGeeksHandle") != "" else None,
                        rating=row.get("GeeksForGeeksRating"),
                        exists=row.get("GeeksForGeeksExists"),
                        last_updated=row.get("GeeksForGeeksLastUpdated"),
                        raw_data=row.get("GeeksForGeeksRawData")
                    ),
                    Platform.HACKERRANK.value: PlatformStatus(
                        handle=row.get("HackerRankHandle") if row.get("HackerRankHandle") != "" else None,
                        rating=row.get("HackerRankRating"),
                        exists=row.get("HackerRankExists"),
                        last_updated=row.get("HackerRankLastUpdated"),
                        raw_data=row.get("HackerRankRawData")
                    ),
                    Platform.LEETCODE.value: PlatformStatus(
                        handle=row.get("LeetCodeHandle") if row.get("LeetCodeHandle") != "" else None,
                        rating=row.get("LeetCodeRating"),
                        exists=row.get("LeetCodeExists"),
                        last_updated=row.get("LeetCodeLastUpdated"),
                        raw_data=row.get("LeetCodeRawData")
                    )
                }
            )
            participants.append(participant)
        return participants
    
    def bulk_upload_from_dataframe(self, df: pd.DataFrame, batch: Batch, college: College) -> None:
        """Upload participants from a DataFrame"""
        try:
            collection = self.get_collection(batch, college)
            participants = self._dataframe_to_participants(df)
            collection.insert_many([self._participant_to_document(p) for p in participants])
            logger.info("Bulk uploaded participants", count=len(participants), batch=batch.name, college=college.name)
            
        except PyMongoError as e:
            logger.error("Failed to bulk upload participants", error=str(e), batch=batch.name, college=college.name, exc_info=True)
            raise DatabaseError(f"Failed to bulk upload participants: {e}")
        
    def get_max_rating(self, platform: Platform, college: College, batch: Batch) -> int:
        """Get the maximum rating for a platform within a specific college and batch"""
        try:
            # Get the appropriate collection based on batch and college
            collection = self.get_collection(batch, college)
            
            # MongoDB aggregation pipeline to find max rating
            pipeline = [
                {
                    "$match": {
                        f"platforms.{platform.value}.rating": {"$exists": True, "$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "max_rating": {"$max": f"$platforms.{platform.value}.rating"}
                    }
                }
            ]
            
            # Execute the aggregation
            result = list(collection.aggregate(pipeline))
            
            # Return 0 if no results found, otherwise return the max rating
            return int(result[0]['max_rating']) if result else 0
        
        except Exception as e:
            logger.error(f"Error getting max rating for {platform.value}: {str(e)}")
            return 0

class LeaderboardCacheRepository:
    """Repository for platform leaderboard cache data"""
    
    COLLECTION_NAME = "leaderboard_cache"
    CACHE_MAX_AGE_DAYS = 1  # Maximum age of cache in days
    
    def __init__(self, db_client: Optional[DatabaseClient] = None) -> None:
        """Initialize the repository"""
        if db_client is None:
            logger.error("Database client is required")
            raise ValueError("Database client is required")
        self.db_client = db_client
        
    def get_collection(self) -> Collection:
        """Get the leaderboard cache collection"""
        return self.db_client.get_collection(self.COLLECTION_NAME)
    
    def get_or_create_collection(self) -> Collection:
        """Get or create the leaderboard cache collection"""
        return self.db_client.get_or_create_collection(self.COLLECTION_NAME)

    def is_cache_stale(self, cache_entry: LeaderboardCache) -> bool:
        """Check if a cache entry is stale (older than max allowed age)
        
        Args:
            cache_entry (LeaderboardCache): Cache entry to check
            
        Returns:
            bool: True if cache is stale, False otherwise
        """
        if not cache_entry:
            return True
            
        now = datetime.now()
        age = now - cache_entry.last_updated
        return age.days >= self.CACHE_MAX_AGE_DAYS
        
    def save_cache_entry(self, cache_entry: LeaderboardCache) -> None:
        """Save a leaderboard cache entry to the database
        
        Args:
            cache_entry (LeaderboardCache): Cache entry to save
        """
        try:
            collection = self.get_or_create_collection()
            document = self._cache_entry_to_document(cache_entry)
            
            # Use upsert to update existing entry or insert new one
            result = collection.update_one(
                {
                    "platform": cache_entry.platform.value,
                    "cacheId": cache_entry.cache_id
                },
                {"$set": document},
                upsert=True
            )
            
            logger.info(
                "Saved leaderboard cache entry",
                platform=cache_entry.platform.name,
                cache_id=cache_entry.cache_id,
                entries_count=len(cache_entry.entries),
                modified=result.modified_count,
                upserted=result.upserted_id is not None
            )
        except PyMongoError as e:
            logger.error(
                "Failed to save leaderboard cache entry",
                error=str(e),
                platform=cache_entry.platform.name,
                cache_id=cache_entry.cache_id,
                exc_info=True
            )
            raise DatabaseError(f"Failed to save leaderboard cache entry: {e}")
    
    def save_cache_entries(self, cache_entries: List[LeaderboardCache]) -> None:
        """Save multiple leaderboard cache entries to the database
        
        Args:
            cache_entries (List[LeaderboardCache]): List of cache entries to save
        """
        try:
            collection = self.get_or_create_collection()
            
            # Create bulk operations for efficient database access
            operations = []
            for entry in cache_entries:
                document = self._cache_entry_to_document(entry)
                operations.append(
                    pymongo.UpdateOne(
                        {
                            "platform": entry.platform.value,
                            "cacheId": entry.cache_id
                        },
                        {"$set": document},
                        upsert=True
                    )
                )
            
            if operations:
                result = collection.bulk_write(operations)
                logger.info(
                    "Saved multiple leaderboard cache entries",
                    count=len(cache_entries),
                    modified=result.modified_count,
                    upserted=len(result.upserted_ids)
                )
        except PyMongoError as e:
            logger.error(
                "Failed to save multiple leaderboard cache entries",
                error=str(e),
                count=len(cache_entries),
                exc_info=True
            )
            raise DatabaseError(f"Failed to save multiple leaderboard cache entries: {e}")
    
    def get_platform_cache_entries(self, platform: Platform, only_fresh: bool = True) -> List[LeaderboardCache]:
        """Get all cache entries for a platform
        
        Args:
            platform (Platform): Platform to get entries for
            only_fresh (bool): If True, only return fresh (non-stale) cache entries
            
        Returns:
            List[LeaderboardCache]: List of cache entries
        """
        try:
            collection = self.get_collection()
            
            # If only fresh entries are requested, add a time filter
            query = {"platform": platform.value}
            if only_fresh:
                max_age_date = datetime.now() - timedelta(days=self.CACHE_MAX_AGE_DAYS)
                query["lastUpdated"] = {"$gte": max_age_date}
                
            cursor = collection.find(query)
            
            entries = []
            for doc in cursor:
                cache_entry = self._document_to_cache_entry(doc)
                # Double-check freshness if needed
                if not only_fresh or not self.is_cache_stale(cache_entry):
                    entries.append(cache_entry)
                
            logger.info("Retrieved leaderboard cache entries", platform=platform.name, count=len(entries), only_fresh=only_fresh)
            return entries
        except PyMongoError as e:
            logger.error(
                "Failed to retrieve leaderboard cache entries",
                error=str(e),
                platform=platform.name,
                exc_info=True
            )
            raise DatabaseError(f"Failed to retrieve leaderboard cache entries: {e}")
    
    def get_cache_entry(self, platform: Platform, cache_id: str, check_freshness: bool = True) -> Optional[LeaderboardCache]:
        """Get a specific cache entry
        
        Args:
            platform (Platform): Platform
            cache_id (str): Cache ID (contest ID or page number)
            check_freshness (bool): If True, return None for stale cache entries
            
        Returns:
            Optional[LeaderboardCache]: Cache entry if found and not stale, None otherwise
        """
        try:
            collection = self.get_collection()
            doc = collection.find_one({
                "platform": platform.value,
                "cacheId": cache_id
            })
            
            if doc:
                cache_entry = self._document_to_cache_entry(doc)
                
                # Check if cache is fresh if required
                if check_freshness and self.is_cache_stale(cache_entry):
                    logger.info(
                        "Found stale leaderboard cache entry, treating as not found",
                        platform=platform.name,
                        cache_id=cache_id
                    )
                    return None
                    
                logger.info(
                    "Retrieved leaderboard cache entry",
                    platform=platform.name,
                    cache_id=cache_id,
                    entries_count=len(cache_entry.entries)
                )
                return cache_entry
            else:
                logger.info("Leaderboard cache entry not found", platform=platform.name, cache_id=cache_id)
                return None
                
        except PyMongoError as e:
            logger.error(
                "Failed to retrieve leaderboard cache entry",
                error=str(e),
                platform=platform.name,
                cache_id=cache_id,
                exc_info=True
            )
            raise DatabaseError(f"Failed to retrieve leaderboard cache entry: {e}")
    
    def _document_to_cache_entry(self, doc: Dict[str, Any]) -> LeaderboardCache:
        """Convert a MongoDB document to a LeaderboardCache object"""
        return LeaderboardCache(
            platform=Platform._value2member_map_[doc["platform"]],
            cache_id=doc["cacheId"],
            entries=doc.get("entries", []),
            last_updated=doc.get("lastUpdated", datetime.now())
        )
    
    def _cache_entry_to_document(self, cache_entry: LeaderboardCache) -> Dict[str, Any]:
        """Convert a LeaderboardCache object to a MongoDB document"""
        return {
            "platform": cache_entry.platform.value,
            "cacheId": cache_entry.cache_id,
            "entries": cache_entry.entries,
            "lastUpdated": cache_entry.last_updated
        }
    
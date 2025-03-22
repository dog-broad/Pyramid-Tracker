from typing import Optional, Dict, Any
import pymongo
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import PyMongoError, CollectionInvalid

from core.config import get_settings
from core.exceptions import DatabaseError, DatabaseDoesNotExistError
from core.logging import get_logger

logger = get_logger(__name__)

class DatabaseClient:
    """MongoDB client wrapper with connection pooling"""
    
    _instance: Optional["DatabaseClient"] = None
    
    def __new__(cls, db_name: str) -> "DatabaseClient":
        """Singleton pattern to ensure single connection pool"""
        if cls._instance is None:
            cls._instance = super(DatabaseClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_name: str) -> None:
        """Initialize the database connection"""
        if getattr(self, "_initialized", False):
            return
            
        settings = get_settings()
        
        try:
            # Use the MongoDB URI and password from the settings
            self._client = pymongo.MongoClient(
                settings.db.mongodb_uri,
                username=settings.db.mongodb_username,
                password=settings.db.mongodb_password,
                maxPoolSize=10,
                minPoolSize=1,
                retryWrites=True
            )
            self._db = self._client[db_name]
            logger.info(f"Database connection established to {db_name} with username {settings.db.mongodb_username}")
            self._initialized = True
        except PyMongoError as e:
            logger.error("Failed to connect to database", error=str(e), exc_info=True)
            raise DatabaseError(f"Database connection failed: {e}")
        
    def get_collection(self, name: str) -> Collection:
        """Get a collection by name"""
        return self._db[name]
    
    def get_database(self) -> Database:
        """Get the database instance"""
        return self._db
        
    def create_collection(self, name: str, **kwargs: Dict[str, Any]) -> Collection:
        """Create a new collection"""
        try:
            return self._db.create_collection(name, **kwargs)
        except CollectionInvalid as e:
            logger.error(f"Failed to create collection {name}: {e}", exc_info=True)
            raise DatabaseError(f"Failed to create collection {name}: {e}")
        
    def get_or_create_collection(self, name: str, **kwargs: Dict[str, Any]) -> Collection:
        """Get an existing collection or create a new one if it doesn't exist"""
        try:
            return self._db[name]
        except KeyError:
            return self.create_collection(name, **kwargs)
    
    def close(self) -> None:
        """Close the database connection"""
        if getattr(self, "_client", None) is not None:
            self._client.close()
            logger.info("Database connection closed")



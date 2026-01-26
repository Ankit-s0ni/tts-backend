"""MongoDB connection module."""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Async MongoDB client (for async operations)
_async_client: AsyncIOMotorClient = None
_async_db = None

# Sync MongoDB client (for sync operations)
_sync_client: MongoClient = None
_sync_db = None


def get_async_database():
    """Get async MongoDB database instance."""
    global _async_client, _async_db
    
    if _async_db is None:
        _async_client = AsyncIOMotorClient(settings.MONGODB_URI)
        _async_db = _async_client[settings.MONGODB_DB_NAME]
        logger.info(f"Connected to async MongoDB database: {settings.MONGODB_DB_NAME}")
    
    return _async_db


def get_sync_database():
    """Get sync MongoDB database instance."""
    global _sync_client, _sync_db
    
    if _sync_db is None:
        _sync_client = MongoClient(settings.MONGODB_URI)
        _sync_db = _sync_client[settings.MONGODB_DB_NAME]
        
        # Test connection
        try:
            _sync_client.admin.command('ping')
            logger.info(f"Connected to sync MongoDB database: {settings.MONGODB_DB_NAME}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    return _sync_db


def close_mongodb_connections():
    """Close MongoDB connections."""
    global _async_client, _sync_client, _async_db, _sync_db
    
    if _async_client:
        _async_client.close()
        _async_client = None
        _async_db = None
        logger.info("Closed async MongoDB connection")
    
    if _sync_client:
        _sync_client.close()
        _sync_client = None
        _sync_db = None
        logger.info("Closed sync MongoDB connection")


# Initialize collections and indexes
def init_mongodb():
    """Initialize MongoDB collections and create indexes."""
    db = get_sync_database()
    
    # Create collections if they don't exist
    collections = db.list_collection_names()
    
    if "jobs" not in collections:
        db.create_collection("jobs")
    
    if "voices" not in collections:
        db.create_collection("voices")
    
    if "counters" not in collections:
        db.create_collection("counters")
    
    if "temp_audio" not in collections:
        db.create_collection("temp_audio")
    
    # Create indexes
    try:
        # Jobs indexes
        db.jobs.create_index("job_id", unique=True)
        db.jobs.create_index("user_id")
        db.jobs.create_index([("created_at", -1)])
        
        # Voices indexes
        db.voices.create_index("voice_id", unique=True)
        db.voices.create_index("available")
        
        # Counters index
        db.counters.create_index("name", unique=True)
        
        # Temp audio indexes
        db.temp_audio.create_index("audio_id", unique=True)
        db.temp_audio.create_index("created_at", expireAfterSeconds=86400)  # 24 hours TTL
        
        logger.info("MongoDB indexes created successfully")
    except Exception as e:
        logger.warning(f"Some indexes may already exist: {e}")

"""MongoDB data layer - replaces DynamoDB implementation.

This module provides all database operations using MongoDB instead of DynamoDB.
Compatible with both dynamo_simple.py and dynamo.py interfaces.
"""
from datetime import datetime
from typing import Dict, List, Optional, Union
import uuid
from .mongodb import get_sync_database, init_mongodb
from bson import ObjectId

# Initialize MongoDB on module load
try:
    init_mongodb()
except Exception as e:
    print(f"Warning: MongoDB initialization error (will retry on first use): {e}")


def _get_db():
    """Get MongoDB database instance."""
    return get_sync_database()


def _next_id(counter_name: str) -> int:
    """Atomically increments and returns next numeric id for counter_name."""
    db = _get_db()
    result = db.counters.find_one_and_update(
        {"name": counter_name},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=True
    )
    return result.get("value", 1) if result else 1


# ============================================================================
# JOB OPERATIONS
# ============================================================================

def create_job_item(
    job_id: str = None,
    user_id: Union[str, int] = "anonymous",
    text: str = "",
    voice_id: str = "",
    status: str = "pending",
    audio_url: str = None,
    **kwargs
) -> dict:
    """Create a new job item in MongoDB.
    
    Args:
        job_id: Optional job ID (will generate UUID if not provided)
        user_id: User ID (string or int)
        text: Text to convert to speech
        voice_id: Voice ID to use
        status: Job status (default: "pending")
        audio_url: URL to audio file (optional)
        **kwargs: Additional fields to store
    
    Returns:
        Created job document
    """
    db = _get_db()
    
    # Generate job_id if not provided
    if job_id is None:
        job_id = str(uuid.uuid4())
    
    now = datetime.utcnow()
    job_item = {
        "job_id": job_id,
        "user_id": str(user_id) if user_id is not None else "anonymous",
        "text": text,
        "voice_id": voice_id or "en_US-lessac-medium",
        "status": status,
        "audio_url": audio_url,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        **kwargs
    }
    
    result = db.jobs.insert_one(job_item)
    job_item["_id"] = str(result.inserted_id)
    
    return job_item


def get_job_item(job_id: Union[str, int]) -> Optional[dict]:
    """Get a job item by ID.
    
    Args:
        job_id: Job ID (string UUID or int)
    
    Returns:
        Job document or None
    """
    db = _get_db()
    
    # Try to find by job_id first (string UUID)
    job = db.jobs.find_one({"job_id": str(job_id)})
    
    # If not found and job_id is numeric, try finding by numeric id field
    if not job and isinstance(job_id, int):
        job = db.jobs.find_one({"id": job_id})
    
    if job and "_id" in job:
        job["_id"] = str(job["_id"])
    
    return job


def update_job_item(job_id: Union[str, int], **updates) -> Optional[dict]:
    """Update a job item.
    
    Args:
        job_id: Job ID (string UUID or int)
        **updates: Fields to update
    
    Returns:
        Updated job document or None
    """
    db = _get_db()
    
    updates["updated_at"] = datetime.utcnow().isoformat()
    
    # Try to update by job_id first
    result = db.jobs.find_one_and_update(
        {"job_id": str(job_id)},
        {"$set": updates},
        return_document=True
    )
    
    # If not found and job_id is numeric, try numeric id
    if not result and isinstance(job_id, int):
        result = db.jobs.find_one_and_update(
            {"id": job_id},
            {"$set": updates},
            return_document=True
        )
    
    if result and "_id" in result:
        result["_id"] = str(result["_id"])
    
    return result


def get_user_jobs(user_id: Union[str, int] = "anonymous", limit: int = 50) -> List[dict]:
    """Get all jobs for a user.
    
    Args:
        user_id: User ID
        limit: Maximum number of jobs to return
    
    Returns:
        List of job documents
    """
    db = _get_db()
    
    jobs = list(db.jobs.find(
        {"user_id": str(user_id)}
    ).sort("created_at", -1).limit(limit))
    
    # Convert ObjectId to string
    for job in jobs:
        if "_id" in job:
            job["_id"] = str(job["_id"])
    
    return jobs


def list_all_jobs() -> List[dict]:
    """Get all jobs.
    
    Returns:
        List of all job documents
    """
    db = _get_db()
    
    jobs = list(db.jobs.find().sort("created_at", -1))
    
    for job in jobs:
        if "_id" in job:
            job["_id"] = str(job["_id"])
    
    return jobs


def delete_job_item(job_id: Union[str, int]) -> bool:
    """Delete a job item.
    
    Args:
        job_id: Job ID
    
    Returns:
        True if deleted, False otherwise
    """
    db = _get_db()
    
    # Try to delete by job_id first
    result = db.jobs.delete_one({"job_id": str(job_id)})
    
    if result.deleted_count == 0 and isinstance(job_id, int):
        # Try numeric id
        result = db.jobs.delete_one({"id": job_id})
    
    return result.deleted_count > 0


# ============================================================================
# VOICE OPERATIONS
# ============================================================================

def list_voices() -> list:
    """Get all voices.
    
    Returns:
        List of all voice documents
    """
    db = _get_db()
    
    voices = list(db.voices.find())
    
    for voice in voices:
        if "_id" in voice:
            voice["_id"] = str(voice["_id"])
    
    return voices


def list_available_voices() -> list:
    """Get all available voices.
    
    Returns:
        List of available voice documents
    """
    db = _get_db()
    
    voices = list(db.voices.find({"available": True}))
    
    for voice in voices:
        if "_id" in voice:
            voice["_id"] = str(voice["_id"])
    
    return voices


def get_voice(voice_id: str) -> Optional[dict]:
    """Get a voice by ID.
    
    Args:
        voice_id: Voice ID
    
    Returns:
        Voice document or None
    """
    db = _get_db()
    
    voice = db.voices.find_one({"id": voice_id})
    
    if voice and "_id" in voice:
        voice["_id"] = str(voice["_id"])
    
    return voice


def put_voice(voice: dict) -> dict:
    """Create or update a voice.
    
    Args:
        voice: Voice document (must have 'id' field)
    
    Returns:
        Voice document
    """
    db = _get_db()
    
    voice_id = voice.get("id")
    if not voice_id:
        raise ValueError("Voice must have an 'id' field")
    
    # Upsert voice
    db.voices.update_one(
        {"id": voice_id},
        {"$set": voice},
        upsert=True
    )
    
    return voice


# ============================================================================
# TEMP AUDIO OPERATIONS
# ============================================================================

def create_temp_audio_item(
    audio_id: str,
    s3_key: str,
    user_id: Union[str, int] = "anonymous",
    ttl: int = None,
    **kwargs
) -> dict:
    """Create a temporary audio item.
    
    Args:
        audio_id: Unique audio ID
        s3_key: S3 object key
        user_id: User ID
        ttl: Time to live (seconds from now)
        **kwargs: Additional fields
    
    Returns:
        Created temp audio document
    """
    db = _get_db()
    
    now = datetime.utcnow()
    item = {
        "audio_id": audio_id,
        "s3_key": s3_key,
        "user_id": str(user_id),
        "created_at": now,
        **kwargs
    }
    
    # MongoDB TTL index will auto-delete after expiry
    if ttl:
        item["ttl"] = ttl
    
    result = db.temp_audio.insert_one(item)
    item["_id"] = str(result.inserted_id)
    
    return item


def get_temp_audio_item(audio_id: str) -> Optional[dict]:
    """Get a temporary audio item.
    
    Args:
        audio_id: Audio ID
    
    Returns:
        Temp audio document or None
    """
    db = _get_db()
    
    item = db.temp_audio.find_one({"audio_id": audio_id})
    
    if item and "_id" in item:
        item["_id"] = str(item["_id"])
    
    return item


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_job_id() -> str:
    """Generate a unique job ID.
    
    Returns:
        UUID string
    """
    return str(uuid.uuid4())


def get_all_jobs_for_user(user_id: Union[str, int] = "anonymous") -> List[dict]:
    """Alias for get_user_jobs.
    
    Args:
        user_id: User ID
    
    Returns:
        List of job documents
    """
    return get_user_jobs(user_id)

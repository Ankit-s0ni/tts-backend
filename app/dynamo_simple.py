"""Simple in-memory storage system.

This module provides a simple in-memory storage system for development.
Replaces AWS DynamoDB dependencies.
"""
from datetime import datetime
from typing import Dict, List, Optional
import uuid
import json


# In-memory storage
_JOBS_STORE: Dict[str, dict] = {}
_USERS_STORE: Dict[str, dict] = {}


def create_job_item(
    job_id: str,
    user_id: str = "anonymous",
    text: str = "",
    voice_id: str = "",
    status: str = "pending",
    audio_url: str = None,
    **kwargs
) -> dict:
    """Create a new job item in memory."""
    job_item = {
        "job_id": job_id,
        "user_id": user_id,
        "text": text,
        "voice_id": voice_id,
        "status": status,
        "audio_url": audio_url,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        **kwargs
    }
    _JOBS_STORE[job_id] = job_item
    return job_item


def get_job_item(job_id: str) -> Optional[dict]:
    """Get a job item by ID."""
    return _JOBS_STORE.get(job_id)


def update_job_item(job_id: str, **updates) -> Optional[dict]:
    """Update a job item."""
    if job_id not in _JOBS_STORE:
        return None
    
    _JOBS_STORE[job_id].update(updates)
    _JOBS_STORE[job_id]["updated_at"] = datetime.utcnow().isoformat()
    return _JOBS_STORE[job_id]


def get_user_jobs(user_id: str = "anonymous", limit: int = 50) -> List[dict]:
    """Get all jobs for a user."""
    jobs = [job for job in _JOBS_STORE.values() if job.get("user_id") == user_id]
    return jobs[:limit] if limit else jobs


def list_all_jobs() -> List[dict]:
    """Get all jobs."""
    return list(_JOBS_STORE.values())


def delete_job_item(job_id: str) -> bool:
    """Delete a job item."""
    if job_id in _JOBS_STORE:
        del _JOBS_STORE[job_id]
        return True
    return False


# Helper functions for compatibility
def create_job_id() -> str:
    """Generate a unique job ID."""
    return str(uuid.uuid4())


def get_all_jobs_for_user(user_id: str = "anonymous") -> List[dict]:
    """Alias for get_user_jobs."""
    return get_user_jobs(user_id)
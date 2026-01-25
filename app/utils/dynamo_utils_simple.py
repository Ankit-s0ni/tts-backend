"""Simple dynamo utilities for local storage.

This module provides simple utilities for job updates without AWS dependencies.
"""
from datetime import datetime
from ..dynamo_simple import update_job_item


def update_job_s3(job_id: str, s3_key: str, s3_url: str):
    """Update job with file info (simplified for local storage)."""
    update_data = {
        "audio_s3_key": s3_key,
        "audio_s3_url": s3_url,
        "audio_url": s3_url,  # For compatibility
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat()
    }
    
    return update_job_item(job_id, **update_data)
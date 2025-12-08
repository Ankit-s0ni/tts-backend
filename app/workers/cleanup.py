"""Celery task for cleaning up temporary audio files from S3."""

import os
from datetime import datetime, timedelta
from celery import Celery
from app.utils.s3_temp_audio import cleanup_yesterday_s3

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Create Celery app for this module
celery_app = Celery("cleanup_tasks", broker=REDIS_URL, backend=REDIS_URL)


@celery_app.task
def cleanup_yesterday_temp_audio():
    """
    Delete yesterday's temporary audio files from S3.
    This task runs daily at 12:00 PM UTC.
    
    DynamoDB records are auto-deleted via TTL (24 hours after creation).
    S3 files need manual deletion which this task handles.
    """
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    try:
        deleted_count = cleanup_yesterday_s3(yesterday)
        print(f"✓ Cleanup completed: Deleted {deleted_count} files from S3 for {yesterday}")
        return {
            "status": "success",
            "date": yesterday,
            "files_deleted": deleted_count
        }
    except Exception as e:
        print(f"✗ Cleanup failed for {yesterday}: {str(e)}")
        return {
            "status": "failed",
            "date": yesterday,
            "error": str(e)
        }

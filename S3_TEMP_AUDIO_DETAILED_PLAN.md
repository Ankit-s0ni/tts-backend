# S3 Temp Audio Storage - Detailed Implementation Plan

## 1. DynamoDB Table: `tts_temp_audio`

### Table Configuration
```
Table Name: tts_temp_audio
Billing Mode: PAY_PER_REQUEST (on-demand)
Region: Same as your AWS region (e.g., us-east-1)
```

### Partition Key & Sort Key
```
Partition Key (PK): date
  Type: String
  Format: YYYY-MM-DD
  Example: "2025-12-08"
  
Sort Key (SK): audio_id
  Type: String
  Format: UUID v4
  Example: "550e8400-e29b-41d4-a716-446655440000"
```

### All Table Attributes

| Attribute Name | Type | Required | Description | Example |
|---|---|---|---|---|
| **date** | String | ✅ Yes (PK) | Partition key - Date of generation | "2025-12-08" |
| **audio_id** | String | ✅ Yes (SK) | Sort key - Unique UUID for each audio | "550e8400-e29b-41d4-a716-446655440000" |
| **s3_key** | String | ✅ Yes | S3 path to audio file | "temp-audio/2025-12-08/550e8400-e29b-41d4-a716-446655440000.wav" |
| **s3_url** | String | ✅ Yes | S3 signed URL (valid 24h) | "https://bucket.s3.amazonaws.com/temp-audio/..." |
| **text** | String | ✅ Yes | Text that was converted to speech | "Hello world test" |
| **voice_id** | String | ✅ Yes | Voice model used | "en_US-lessac-medium" |
| **duration** | Number | ✅ Yes | Audio length in seconds | 1.32 |
| **file_size_bytes** | Number | ✅ Yes | Size of WAV file in bytes | 45000 |
| **ip_address** | String | ✅ Yes | Guest IP address (for rate limiting) | "192.168.1.100" |
| **created_at** | String | ✅ Yes | ISO 8601 timestamp | "2025-12-08T13:02:19.123Z" |
| **created_at_unix** | Number | ✅ Yes | Unix timestamp (for sorting/filtering) | 1733721739 |
| **ttl** | Number | ✅ Yes | DynamoDB TTL attribute (unix timestamp) | 1733808139 |
| **status** | String | ❌ Optional | Processing status | "completed", "failed", "expired" |
| **error_message** | String | ❌ Optional | Error details if generation failed | "Voice not found" |

---

## 2. DynamoDB TTL Configuration

### Enable TTL for Auto-Deletion
```
TTL Attribute Name: ttl
Expiration Time: 24 hours after creation
```

### How It Works:
```
Created At:    2025-12-08 13:02:19 (Unix: 1733721739)
TTL Value:     1733808139 (Created + 86400 seconds)
Expires At:    2025-12-09 13:02:19
Auto-Deleted:  Within 48 hours (DynamoDB guarantee)
```

### TTL Calculation (Backend Code):
```python
from datetime import datetime, timedelta
import time

created_at = datetime.utcnow()
ttl = int((created_at + timedelta(days=1)).timestamp())

# Example:
# created_at = 2025-12-08 13:02:19
# ttl = 1733808139 (24 hours later)
```

---

## 3. S3 Bucket Structure

### Folder Organization by Date
```
s3://tts-bucket/
└── temp-audio/
    ├── 2025-12-10/          ← Today's files (kept)
    │   ├── 550e8400-e29b-41d4-a716-446655440000.wav
    │   ├── a1b2c3d4-e5f6-7890-abcd-ef1234567890.wav
    │   └── c9d8e7f6-a5b4-c3d2-e1f0-a9b8c7d6e5f4.wav
    │
    ├── 2025-12-09/          ← Yesterday's files (will be deleted at 12 PM)
    │   ├── f1e2d3c4-b5a6-9798-9691-827374656463.wav
    │   └── (multiple files)
    │
    └── 2025-12-08/          ← 2 days old (already deleted)
        └── (empty - deleted by worker)
```

---

## 4. Cleanup Worker Schedule & Logic

### Daily Cleanup Worker
```
Name: cleanup_temp_audio_worker
Trigger: Celery Beat Scheduler
Schedule: Every day at 12:00 PM UTC
Task: cleanup_yesterday_temp_audio()
```

### Cleanup Logic (Pseudo-code)
```python
@celery_app.task
def cleanup_yesterday_temp_audio():
    """
    SCHEDULED TASK: Runs every day at 12:00 PM UTC
    
    Purpose: Delete all temp audio files & records from YESTERDAY
    
    Process:
    1. Calculate yesterday's date (YYYY-MM-DD format)
    2. Query DynamoDB table for all records with date = yesterday
    3. For each record:
       - Delete file from S3 (using s3_key)
       - Record is auto-deleted by DynamoDB TTL (no manual delete)
    4. Log deletion summary
    5. Send notification (optional)
    """
    
    from datetime import datetime, timedelta
    from .utils.s3_utils import delete_s3_file
    from .dynamo import query_temp_audio_by_date
    
    # Calculate yesterday's date
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"[CLEANUP WORKER] Starting cleanup for date: {yesterday}")
    
    try:
        # Query all records from yesterday
        records = query_temp_audio_by_date(date=yesterday)
        
        deleted_count = 0
        failed_count = 0
        
        for record in records:
            try:
                # Delete from S3
                delete_s3_file(record['s3_key'])
                deleted_count += 1
                
                # DynamoDB record auto-deleted by TTL after 24h
                # No manual deletion needed
                
            except Exception as e:
                print(f"[CLEANUP ERROR] Failed to delete {record['audio_id']}: {str(e)}")
                failed_count += 1
        
        # Log results
        print(f"[CLEANUP COMPLETE] Deleted: {deleted_count}, Failed: {failed_count}")
        
        # Optional: Send to monitoring service (Datadog, CloudWatch, etc.)
        log_cleanup_metrics(date=yesterday, deleted=deleted_count, failed=failed_count)
        
    except Exception as e:
        print(f"[CLEANUP FAILED] Worker error: {str(e)}")
        # Send alert notification
        send_alert(f"Cleanup worker failed: {str(e)}")
```

---

## 5. Celery Beat Configuration

### `celerybeat_schedule` in settings
```python
from celery.schedules import crontab
from app.workers.cleanup import cleanup_yesterday_temp_audio

# In settings or config file
CELERY_BEAT_SCHEDULE = {
    'cleanup-temp-audio-daily': {
        'task': 'app.workers.cleanup.cleanup_yesterday_temp_audio',
        'schedule': crontab(hour=12, minute=0),  # 12:00 PM UTC every day
        'options': {'queue': 'celery'}
    },
}
```

### Alternative: In `celery_config.py`
```python
app.conf.beat_schedule = {
    'cleanup-temp-audio-daily': {
        'task': 'app.celery_worker.cleanup_yesterday_temp_audio',
        'schedule': crontab(hour=12, minute=0),  # 12 PM UTC
    },
}
```

---

## 6. Timeline Example

### Scenario: Daily Operations

```
2025-12-08 (Day 1)
  13:02:19 - User generates audio #1
    ✅ Saved to S3: temp-audio/2025-12-08/uuid1.wav
    ✅ Created in DynamoDB: date="2025-12-08", ttl=1733808139
  
  14:30:00 - User generates audio #2
    ✅ Saved to S3: temp-audio/2025-12-08/uuid2.wav
    ✅ Created in DynamoDB: date="2025-12-08", ttl=1733808139

2025-12-09 (Day 2)
  09:00:00 - More users generate audio
    ✅ Saved to S3: temp-audio/2025-12-09/uuid3.wav
    ✅ Created in DynamoDB: date="2025-12-09", ttl=1733894539

  12:00:00 PM (CLEANUP WORKER RUNS)
    🚀 Celery task: cleanup_yesterday_temp_audio()
    📝 Query DynamoDB: date="2025-12-08"
    🗑️ Delete from S3: temp-audio/2025-12-08/uuid1.wav
    🗑️ Delete from S3: temp-audio/2025-12-08/uuid2.wav
    ✅ DynamoDB records for 2025-12-08 still exist
    📊 Log: "Deleted 2 files, 0 failed"

2025-12-10 (Day 3)
  00:00:00 - DynamoDB TTL Background Job
    ⏰ Records from 2025-12-08 reach 24h expiry (ttl timestamp)
    🗑️ DynamoDB auto-deletes all records from 2025-12-08
    (No manual action needed - automatic)

  12:00:00 PM (CLEANUP WORKER RUNS AGAIN)
    🚀 Celery task: cleanup_yesterday_temp_audio()
    📝 Query DynamoDB: date="2025-12-09"
    🗑️ Delete from S3: temp-audio/2025-12-09/uuid3.wav
    ✅ DynamoDB records for 2025-12-09 still exist
    📊 Log: "Deleted 1 file, 0 failed"

2025-12-11 (Day 4)
  00:00:00 - DynamoDB TTL Background Job
    ⏰ Records from 2025-12-09 reach 24h expiry
    🗑️ DynamoDB auto-deletes all records from 2025-12-09
```

---

## 7. Implementation Files Needed

```
backend/
├── app/
│   ├── models/
│   │   └── temp_audio.py          (Pydantic schemas)
│   │
│   ├── utils/
│   │   ├── s3_temp_audio.py       (S3 upload/delete functions)
│   │   └── dynamo_temp_audio.py   (DynamoDB queries)
│   │
│   ├── workers/
│   │   └── cleanup.py             (Celery cleanup task)
│   │
│   ├── routers/
│   │   └── public_tts.py          (Updated /public/tts/sync endpoint)
│   │
│   ├── config.py                  (Updated with S3 config)
│   ├── celery_config.py           (Updated beat schedule)
│   └── main.py                    (Register new router)
│
└── requirements.txt               (boto3 already included)
```

---

## 8. Worker Deletion Summary

### What Gets Deleted at 12 PM UTC Daily:
```
Deletion Target: All files from YESTERDAY
├── S3 Files: temp-audio/{YESTERDAY_DATE}/*.wav
│   ├── Deleted via: delete_s3_file(s3_key)
│   ├── Count: All files from that date folder
│   └── Timing: Executed at 12:00 PM UTC
│
└── DynamoDB Records: date = {YESTERDAY_DATE}
    ├── Deleted via: DynamoDB TTL (automatic)
    ├── Timing: Auto-deletes 24h after creation
    └── No manual cleanup needed
```

### What Gets Kept:
```
✅ Today's files: temp-audio/{TODAY_DATE}/*.wav
✅ Today's records: date = {TODAY_DATE}
✅ 23 hours 59 minutes of data retention minimum
```

### Failure Handling:
```
If S3 deletion fails:
  - Worker continues processing other files
  - Failed file logged with error
  - DynamoDB TTL will auto-delete record anyway after 24h
  - Alert sent to monitoring system

If worker doesn't run:
  - DynamoDB TTL still auto-deletes records after 24h
  - S3 files remain (requires manual cleanup)
  - Alert sent (task missed)
```

---

## 9. Configuration (.env)

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-tts-bucket

# S3 Paths
AWS_S3_TEMP_AUDIO_PREFIX=temp-audio
SIGNED_URL_EXPIRY_SECONDS=86400  # 24 hours

# DynamoDB
DYNAMODB_TEMP_AUDIO_TABLE=tts_temp_audio
DYNAMODB_REGION=us-east-1

# Celery Schedule
CELERY_TIMEZONE=UTC
CELERY_BEAT_SCHEDULE_CLEANUP_HOUR=12
CELERY_BEAT_SCHEDULE_CLEANUP_MINUTE=0
```

---

## 10. Cost Breakdown

### Monthly Costs (Example)
```
Scenario: 10,000 audio files/month (average 500KB each)

S3 Storage:
  - Daily max storage: ~5GB (only keeps 2 days)
  - Monthly cost: ~$0.12

S3 Operations:
  - PUT: 10,000 uploads = ~$0.05
  - GET: 10,000 downloads = ~$0.04
  - DELETE: 5,000 daily deletes = ~$0.025

DynamoDB:
  - On-demand: ~$1.25 (on-demand read/write)
  - TTL cleanup: FREE (automatic)

Celery Task:
  - 1 task/day = negligible cost

Total Monthly: ~$1.50 (very cheap!)
```

---

## Ready to Implement?

**Next Steps (in order):**
1. ✅ Create DynamoDB table with exact schema above
2. ✅ Configure S3 bucket (optional lifecycle policy)
3. ✅ Create `models/temp_audio.py`
4. ✅ Create `utils/s3_temp_audio.py` and `utils/dynamo_temp_audio.py`
5. ✅ Create `workers/cleanup.py` with Celery task
6. ✅ Update `/api/tts/sync` or create new `/public/tts/sync` endpoint
7. ✅ Configure Celery beat schedule
8. ✅ Test cleanup job
9. ✅ Deploy to production

Want me to start implementing these files?

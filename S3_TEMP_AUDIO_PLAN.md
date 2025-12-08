# Temporary Audio Storage & Auto-Cleanup Plan

## Overview
Store guest-generated TTS audio files in AWS S3 with automatic daily cleanup. Files are organized by date and deleted 24 hours after creation.

---

## 1. Database Schema

### DynamoDB Table: `tts_temp_audio`
Store metadata for temporary audio files with auto-expiry.

```
Table Name: tts_temp_audio
Partition Key: date (String) - Format: YYYY-MM-DD (e.g., "2025-12-08")
Sort Key: audio_id (String) - UUID v4 (e.g., "abc123-def456-...")

Attributes:
- date (PK): "2025-12-08"
- audio_id (SK): "f47ac10b-58cc-4372-a567-0e02b2c3d479"
- s3_key: "temp-audio/2025-12-08/f47ac10b-58cc-4372-a567-0e02b2c3d479.wav"
- s3_url: "https://bucket.s3.amazonaws.com/temp-audio/2025-12-08/f47ac10b.wav"
- text: "Hello world test"
- voice_id: "en_US-lessac-medium"
- duration: 1.32
- created_at: "2025-12-08T13:02:19Z" (ISO 8601)
- ip_address: "192.168.1.100" (for rate limiting)
- ttl: 1733721739 (Unix timestamp for 24h expiry) ← DynamoDB TTL attribute
```

**TTL Configuration:**
- Enable TTL on `ttl` attribute
- DynamoDB automatically deletes items after 24 hours
- No manual cleanup needed for the table!

---

## 2. S3 Storage Structure

### Bucket Organization
```
bucket-name/
└── temp-audio/
    ├── 2025-12-08/
    │   ├── f47ac10b-58cc-4372-a567-0e02b2c3d479.wav
    │   ├── a1b2c3d4-e5f6-7890-abcd-ef1234567890.wav
    │   └── ...
    ├── 2025-12-07/
    │   ├── (deleted by cleanup job)
    │   └── ...
    └── 2025-12-06/
        └── (deleted by cleanup job)
```

### S3 Lifecycle Policy
```json
{
  "Rules": [
    {
      "Id": "DeleteTempAudioAfter1Day",
      "Status": "Enabled",
      "Prefix": "temp-audio/",
      "Expiration": {
        "Days": 2  // Keep for 2 days to be safe, then S3 auto-deletes
      }
    }
  ]
}
```

---

## 3. Implementation Changes

### A. Backend Updates

#### 1. Update `.env` Configuration
```bash
# S3 Configuration
AWS_S3_BUCKET=your-bucket-name
AWS_S3_TEMP_AUDIO_PREFIX=temp-audio
AWS_S3_REGION=us-east-1
TEMP_AUDIO_TABLE_NAME=tts_temp_audio
```

#### 2. Create `app/models/temp_audio.py`
```python
from datetime import datetime, timedelta
from pydantic import BaseModel

class TempAudioRecord(BaseModel):
    audio_id: str
    date: str  # YYYY-MM-DD
    s3_key: str
    s3_url: str
    text: str
    voice_id: str
    duration: float
    ip_address: str
    created_at: str

class TempAudioCreate(BaseModel):
    text: str
    voice_id: str
    ip_address: str
```

#### 3. Create `app/utils/s3_temp_audio.py` Module
```python
# Functions:
- upload_temp_audio_to_s3(audio_bytes, audio_id, date) -> s3_url
- save_temp_audio_metadata(metadata) -> DynamoDB entry
- get_temp_audio_metadata(audio_id, date)
- list_today_audio_files(date)
- delete_temp_audio(audio_id, date) -> removes from S3 + DynamoDB
```

#### 4. Create `app/routers/public_tts.py` (New Router)
```python
@router.post("/public/tts/sync")
async def tts_sync_public(request: Request):
    """
    Public TTS endpoint (no auth required) for guests.
    - Generates audio
    - Uploads to S3
    - Saves metadata to DynamoDB with TTL
    - Returns signed URL valid for 24 hours
    """
    # Get client IP for rate limiting
    ip_address = request.client.host
    
    # Rate limit by IP (optional but recommended)
    # check_rate_limit(ip_address)
    
    # Generate audio (same as before)
    # Upload to S3
    # Save metadata to DynamoDB
    # Return JSON with signed S3 URL
```

#### 5. Update `app/main.py`
```python
from .routers import public_tts
app.include_router(public_tts.router, tags=["public-tts"])
```

---

## 4. Cleanup Strategy

### Option A: Lambda Function (Recommended for AWS)
- **Trigger**: Daily at 12 PM UTC
- **Action**: 
  - Query DynamoDB for records with `date < today - 1`
  - Delete corresponding S3 files
  - No need to delete DynamoDB items (TTL handles it)
- **Cost**: Minimal (serverless)

**Lambda Handler:**
```python
def lambda_handler(event, context):
    """
    Daily cleanup job - runs at 12 PM UTC
    Deletes S3 files for dates older than yesterday
    DynamoDB TTL handles automatic record deletion
    """
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # List all folders in temp-audio/
    # Delete folders with date < yesterday
    # Log deleted files
```

### Option B: Celery Task (If using existing Celery)
- **Trigger**: Celery beat scheduler at 12 PM UTC daily
- **Task**: `cleanup_temp_audio_daily()`
- **Cost**: Uses existing Celery infrastructure

**Celery Task:**
```python
@celery_app.task
def cleanup_temp_audio_daily():
    """Daily cleanup of temp audio files older than 1 day"""
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Query DynamoDB: date < yesterday
    # Delete from S3
    # TTL handles DynamoDB cleanup
```

### Option C: Cron Job (Simple but requires always-on server)
- **Trigger**: Cron at 0 12 * * * (12 PM daily)
- **Cost**: Runs on existing backend server

---

## 5. API Response Example

### Request
```bash
POST https://api.example.com/public/tts/sync
Content-Type: application/json

{
  "text": "Hello world",
  "voice": "en_US-lessac-medium"
}
```

### Response (200 OK)
```json
{
  "audio_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "audio_url": "https://bucket.s3.amazonaws.com/temp-audio/2025-12-08/f47ac10b-58cc-4372-a567-0e02b2c3d479.wav?X-Amz-Signature=...",
  "duration": 1.32,
  "expires_at": "2025-12-09T13:02:19Z",
  "text": "Hello world",
  "voice_id": "en_US-lessac-medium"
}
```

---

## 6. Implementation Timeline

| Phase | Tasks | Duration |
|-------|-------|----------|
| **Phase 1: Setup** | Create DynamoDB table, S3 lifecycle policy, configure .env | 30 mins |
| **Phase 2: Core Logic** | Create models, S3 utils module, update `/tts/sync` endpoint | 1 hour |
| **Phase 3: Cleanup Job** | Implement Lambda/Celery/Cron cleanup task | 30 mins |
| **Phase 4: Testing** | Test upload, verify S3 storage, test auto-cleanup | 1 hour |
| **Phase 5: Deployment** | Deploy to production, configure schedule | 30 mins |

**Total**: ~4 hours

---

## 7. Cost Estimation (Monthly)

### AWS Services
| Service | Estimate | Notes |
|---------|----------|-------|
| **S3 Storage** | ~$2-5 | 1GB = 2000 audio files (assuming 500KB avg) |
| **S3 GET** | ~$1 | 100,000 downloads per month |
| **S3 PUT** | <$1 | 10,000 uploads per month |
| **DynamoDB** | ~$2-5 | On-demand pricing, TTL cleanup free |
| **Lambda** | <$1 | Daily cleanup job (very fast) |
| **Total** | ~$7-15 | Scales with usage |

---

## 8. Security Considerations

✅ **Signed URLs**: S3 URLs expire after 24 hours  
✅ **Rate Limiting**: Limit uploads per IP  
✅ **Auto-Deletion**: No manual cleanup = no forgotten files  
✅ **Access Control**: Private S3 bucket, only via signed URLs  
✅ **Logging**: Log all uploads/downloads for auditing  

---

## 9. Migration from Current Implementation

### Before (Local Server Storage)
```
/app/output/tts_*.wav  (on server)
/tts/audio/{filename}  (endpoint serves from disk)
```

### After (S3 Storage)
```
s3://bucket/temp-audio/2025-12-08/uuid.wav  (on S3)
Signed URL returned directly to client
No local file serving needed
```

**Migration Steps:**
1. Create S3 bucket + DynamoDB table
2. Deploy new endpoint code
3. Optionally migrate existing local files to S3
4. Update Flutter app to use new response format (already compatible)
5. Set up cleanup job
6. Monitor S3 storage and costs

---

## 10. Decision: Which Cleanup Method?

**Recommendation: Lambda + DynamoDB TTL** ✅

**Why:**
- ✅ Cheapest ($0 if under Lambda free tier)
- ✅ Fully serverless, no maintenance
- ✅ Scales automatically
- ✅ DynamoDB TTL handles table cleanup (no manual queries)
- ✅ Can add S3 lifecycle policy as backup
- ✅ Clear, simple to understand and debug

**Alternative: Celery Task** (if Lambda not available)
- Uses existing infrastructure
- Good if you already have Celery configured
- Slightly higher operational overhead

---

## Next Steps

Ready to implement? Let me know:

1. ✅ Create DynamoDB table `tts_temp_audio`
2. ✅ Configure S3 bucket + lifecycle policy
3. ✅ Create utility modules for S3 + DynamoDB
4. ✅ Update `/tts/sync` endpoint to use S3
5. ✅ Create Lambda cleanup function
6. ✅ Test end-to-end flow
7. ✅ Deploy to production

Which would you like to start with?

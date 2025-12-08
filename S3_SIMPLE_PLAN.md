# S3 Temp Audio Storage - SIMPLE Plan

## 1. DynamoDB Table: `tts_temp_audio` (MINIMAL)

### Table Configuration
```
Table Name: tts_temp_audio
Billing Mode: PAY_PER_REQUEST
```

### Keys
```
Partition Key: date (String)
  Format: YYYY-MM-DD
  Example: "2025-12-08"

Sort Key: audio_id (String)
  Format: UUID v4
  Example: "550e8400-e29b-41d4-a716-446655440000"
```

### Only 7 Required Fields

| Field | Type | Description |
|-------|------|-------------|
| **date** | String | PK - "2025-12-08" |
| **audio_id** | String | SK - UUID |
| **s3_url** | String | Signed URL from S3 |
| **text** | String | Text that was converted |
| **voice_id** | String | Voice model used |
| **duration** | Number | Audio length in seconds |
| **ttl** | Number | Unix timestamp (auto-delete 24h) |

**That's it! 7 fields only.**

---

## 2. S3 Folder Structure (SIMPLE)

```
s3://bucket/
└── temp-audio/
    ├── 2025-12-10/
    │   ├── uuid1.wav
    │   ├── uuid2.wav
    │   └── uuid3.wav
    │
    └── 2025-12-09/
        ├── uuid4.wav
        └── uuid5.wav
```

---

## 3. Daily Cleanup Worker (SIMPLE)

### When: 12:00 PM UTC Every Day

```python
@celery_app.task
def cleanup_yesterday_temp_audio():
    """Delete yesterday's temp audio files"""
    
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Delete folder: temp-audio/{yesterday}/ from S3
    # DynamoDB records auto-delete by TTL (no manual action)
    
    # That's it!
```

---

## 4. API Response (SIMPLE)

### Response from `/tts/sync`
```json
{
  "audio_id": "550e8400-e29b-41d4-a716-446655440000",
  "s3_url": "https://bucket.s3.amazonaws.com/temp-audio/2025-12-08/550e8400.wav?X-Amz-Signature=...",
  "duration": 1.32,
  "text": "Hello world",
  "voice_id": "en_US-lessac-medium"
}
```

---

## 5. Files to Create (SIMPLE)

```
backend/app/
├── utils/
│   └── s3_temp_audio.py          (3 functions only)
│
├── workers/
│   └── cleanup.py                (1 function)
│
└── routers/
    └── update api.py             (modify /tts/sync endpoint)
```

---

## 6. Three Simple Functions

### Function 1: Upload to S3
```python
def upload_to_s3(audio_bytes, audio_id, date):
    """Upload WAV to S3 and return signed URL"""
    s3_key = f"temp-audio/{date}/{audio_id}.wav"
    s3.put_object(Bucket=bucket, Key=s3_key, Body=audio_bytes)
    signed_url = s3.generate_presigned_url(s3_key, ExpiresIn=86400)  # 24h
    return signed_url, s3_key
```

### Function 2: Save to DynamoDB
```python
def save_to_dynamodb(date, audio_id, s3_url, text, voice_id, duration):
    """Save metadata to DynamoDB"""
    ttl = int((datetime.utcnow() + timedelta(days=1)).timestamp())
    
    table.put_item(Item={
        'date': date,
        'audio_id': audio_id,
        's3_url': s3_url,
        'text': text,
        'voice_id': voice_id,
        'duration': duration,
        'ttl': ttl
    })
```

### Function 3: Cleanup Worker
```python
@celery_app.task
def cleanup_yesterday_temp_audio():
    """Delete yesterday's files from S3"""
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # List all files in temp-audio/{yesterday}/
    response = s3.list_objects_v2(
        Bucket=bucket,
        Prefix=f"temp-audio/{yesterday}/"
    )
    
    # Delete each file
    for obj in response.get('Contents', []):
        s3.delete_object(Bucket=bucket, Key=obj['Key'])
```

---

## 7. Timeline Example

```
2025-12-08 @ 13:02 - User generates audio
  ✅ Upload to S3: temp-audio/2025-12-08/uuid1.wav
  ✅ Save to DynamoDB with ttl = (now + 24h)

2025-12-09 @ 12:00 PM - WORKER RUNS
  🗑️ Delete all files from temp-audio/2025-12-08/
  ⏳ DynamoDB will auto-delete records when ttl expires

2025-12-09 @ 24:00+ - TTL AUTO-DELETE
  🗑️ DynamoDB auto-deletes records (no manual action)
```

---

## 8. Configuration (.env) - SIMPLE

```bash
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bucket-name
DYNAMODB_TABLE_NAME=tts_temp_audio
CELERY_BEAT_CLEANUP_HOUR=12
CELERY_BEAT_CLEANUP_MINUTE=0
```

---

## 9. Implementation Steps

1. Create `app/utils/s3_temp_audio.py` (upload + save + cleanup functions)
2. Create `app/workers/cleanup.py` (1 celery task)
3. Update `app/api.py` - modify `/tts/sync` to use S3 instead of local storage
4. Update `celery_config.py` - add daily cleanup schedule
5. Update `.env` with S3 config

---

## That's it! Super simple. Ready to implement?

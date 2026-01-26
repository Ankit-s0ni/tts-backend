# ACTUAL SOLUTION - What's Really Happening

## 1. THE REAL ISSUE WITH CLOUDINARY

**Problem:** Cloudinary authentication credentials are **not working** (`Invalid cloud_name voicetexta`)

**Root Cause Discovered:**
- Cloud name: `voicetexta`
- API Key and Secret are configured in `.env`
- BUT Cloudinary account is either:
  - Deleted or suspended
  - Credentials are invalid
  - Account never existed

**Current Workaround (ACTUAL SOLUTION):**
The API **falls back to returning Base64-encoded audio** directly in the JSON response:

```json
{
  "duration": 3.92,
  "text": "Hello...",
  "voice_id": "en_US-lessac-high",
  "status": "success",
  "audio_base64": "UklGRi8AAAA..." // Full WAV file as base64
}
```

This is **working fine** for Flutter apps - they decode the base64 and use the audio.

---

## 2. DATABASE SAVING ANALYSIS

### What IS Being Saved:

#### **For Job Requests** (`POST /jobs`):
```python
create_job_item(
    job_id=uuid,
    user_id=current_user.id,
    text="your text here",
    voice_id="en_US-lessac-high",
    status="queued",  # Later: "processing", "completed", "failed"
    audio_url=None,   # Would be filled after processing
)
```

**Stored in MongoDB `jobs` collection:**
```json
{
  "_id": ObjectId,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123",
  "text": "Your full text",
  "voice_id": "en_US-lessac-high",
  "status": "queued",
  "audio_url": null,  // Gets filled when job completes
  "created_at": "2026-01-27T10:30:00",
  "updated_at": "2026-01-27T10:30:00"
}
```

#### **For Synchronous `/tts/sync` Requests:**
```
NO JOB IS CREATED
NO DATABASE SAVE OCCURS
```

**Instead:**
- Audio is generated in-memory
- Encoded as base64
- Sent directly in response
- **Nothing stored** - user's device must save it

---

## 3. DATABASE MODELS

### Job Table Schema:
```python
class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    language = Column(String)
    voice_id = Column(String)
    text = Column(Text)  # The input text
    include_alignments = Column(Boolean, default=False)
    status = Column(String, default="queued")
    s3_final_url = Column(String, nullable=True)  # Where audio is stored
    alignments_s3_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
```

### Chunk Table Schema:
```python
class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    index = Column(Integer)
    text_excerpt = Column(Text)  # Part of the full text
    s3_temp_path = Column(String, nullable=True)  # Temp audio location
    alignments_json = Column(Text, nullable=True)
    status = Column(String, default="pending")
    duration_seconds = Column(Integer, default=0)
    attempts = Column(Integer, default=0)
```

---

## 4. WHAT GETS SAVED FOR EACH ENDPOINT

| Endpoint | Saves to DB? | What's Saved | Where Audio Goes |
|----------|------------|------------|------------------|
| `POST /tts/sync` | ❌ NO | Nothing | Base64 in response only |
| `POST /jobs` | ✅ YES | Job + text | MongoDB `jobs` table |
| `GET /jobs/{id}` | ❌ NO | (Reads only) | Returns stored audio_url |
| `/tts/audio/{file}` | ❌ NO | (Serves file) | From disk `/output/` folder |

---

## 5. CURRENT AUDIO FLOW

### Synchronous Request (`/tts/sync`):
```
Request → Piper generates audio → Base64 encode → JSON response
                                                       ↓
                                              Flutter app decodes & uses
                                              Nothing stored anywhere
```

### Asynchronous Request (`/jobs`):
```
Request → Saved to MongoDB → Celery worker picks it up → 
Piper generates audio → Saves to `/output/` folder → 
Updates MongoDB with audio_url → Returns to user
```

---

## 6. THE REAL SOLUTION SUMMARY

### Problem:
- Trying to use Cloudinary for file hosting → **FAILING**
- Auth error: "Invalid cloud_name voicetexta"

### Current Working Solution:
- **For `/tts/sync`**: Return audio as **base64 in JSON**
  - Simple, works immediately
  - Suitable for Flutter apps
  - No external dependencies

- **For `/jobs` (async)**: Save to **local filesystem** (`/output/` folder)
  - User can fetch via `/tts/audio/{filename}`
  - Stored temporarily on disk
  - Can be uploaded to S3/Cloudinary later

### What Needs to Be Done:
1. **Verify Cloudinary account** - Check if account exists and is active
2. **OR** - Remove Cloudinary entirely, use S3 for persistent storage
3. **OR** - Keep current solution (works fine for MVP)

---

## 7. DATABASE DETAILS

### MongoDB Collections:
- **`jobs`** - Stores job requests, text, voice, status
- **`chunks`** - Stores chunked text for large documents
- **`users`** - User accounts
- **`verification_codes`** - Email verification

### What's NOT Being Saved:
- ❌ Generated audio (not stored in DB, only disk or Cloudinary)
- ❌ Base64 audio blobs (response only, not persisted)
- ❌ Audio metadata beyond duration (no waveform, visualization data)

### What IS Being Saved:
- ✅ Job ID
- ✅ User ID
- ✅ Input text
- ✅ Voice ID used
- ✅ Job status (queued/processing/completed/failed)
- ✅ Audio URL (once generated)
- ✅ Created/updated timestamps
- ✅ Audio duration

---

## 8. RECOMMENDED ACTION

**Option A (Current MVP - Working):**
- Keep `/tts/sync` returning base64 audio
- Accept local file storage for `/jobs`
- Works perfectly for Flutter app

**Option B (Production):**
1. Fix Cloudinary credentials OR
2. Switch to AWS S3 for file storage
3. Keep database saving job metadata

**Option C (Simplest):**
- Remove Cloudinary attempts entirely
- Always return base64 for `/tts/sync`
- Save async jobs to S3 directly

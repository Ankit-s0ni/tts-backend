# Database and URL Storage Summary

## ✅ CHANGES MADE

### 1. API Now Returns URLs (Not Base64)

**Old Response:**
```json
{
  "duration": 3.92,
  "audio_base64": "UklGRi8AAAA..." // Large base64 string
}
```

**New Response:**
```json
{
  "duration": 3.92,
  "text": "Hello, this is the new URL-based TTS system",
  "voice_id": "en_US-lessac-high",
  "engine": "piper",
  "sample_rate": 22050,
  "status": "success",
  "audio_url": "/tts/audio/tts_b8ec64f725e2_20260126_205222.wav"
}
```

### 2. How It Works

**For `/tts/sync` (Synchronous Requests):**
```
1. Text sent to API
2. Piper synthesizes audio in memory
3. Audio saved to disk: `/output/tts_[UUID]_[TIMESTAMP].wav`
4. Return URL: `/tts/audio/tts_b8ec64f725e2_20260126_205222.wav`
5. Flutter app can fetch audio from this URL
```

**For `/jobs` (Asynchronous Requests):**
```
1. Job saved to MongoDB with: user_id, text, voice_id, status
2. Celery worker processes job
3. Piper synthesizes chunks
4. Final audio saved to: `/output/job_[job_id].wav`
5. Audio uploaded to S3 (if configured)
6. MongoDB updated with: audio_s3_url, audio_s3_key, status="completed"
```

---

## 📊 DATABASE SAVING

### What Gets Saved to MongoDB for `/jobs`:

```json
{
  "_id": ObjectId,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123",
  "text": "Your full text here...",
  "voice_id": "en_US-lessac-high",
  "status": "queued|processing|completed|failed",
  "s3_final_url": "/output/job_550e8400-e29b-41d4-a716-446655440000.wav",
  "audio_s3_key": "tts-audio/123/550e8400-e29b-41d4-a716-446655440000.wav",
  "audio_s3_url": "https://s3.amazonaws.com/...",  // Full S3 URL if uploaded
  "created_at": "2026-01-27T10:30:00",
  "updated_at": "2026-01-27T10:35:00"
}
```

### What Gets Saved for `/tts/sync`:

**NOTHING!** The `/tts/sync` endpoint:
- ✅ Saves audio file to local disk
- ✅ Returns URL in response
- ❌ Does NOT create a database record
- ❌ No job tracking, no history

---

## 🔗 Audio URL Endpoints

### Retrieve Audio Files

**Direct Download:**
```
GET /tts/audio/tts_b8ec64f725e2_20260126_205222.wav
```

Returns: WAV audio file (audio/wav content-type)

**Response:**
```
HTTP/1.1 200 OK
Content-Type: audio/wav
Content-Length: 160000

[Binary WAV data...]
```

---

## 📝 Field Mapping

### MongoDB Job Fields:

| Field | Saved? | Description |
|-------|--------|-------------|
| `job_id` | ✅ YES | Unique UUID for job |
| `user_id` | ✅ YES | User who requested |
| `text` | ✅ YES | Input text for TTS |
| `voice_id` | ✅ YES | Voice used (e.g., en_US-lessac-high) |
| `status` | ✅ YES | queued→processing→completed |
| `s3_final_url` | ✅ YES | Local disk path |
| `audio_s3_url` | ✅ YES | S3 URL (if uploaded) |
| `audio_s3_key` | ✅ YES | S3 key/path |
| `created_at` | ✅ YES | Job creation time |
| `updated_at` | ✅ YES | Last update time |

---

## 🎯 Flutter App Integration

### For `/tts/sync` Endpoint:

```dart
// Request
var response = await http.post(
  Uri.parse('http://backend:8001/tts/sync'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({
    'text': 'Your text here',
    'voice': 'en_US-lessac-high'
  }),
);

// Response
{
  "duration": 3.92,
  "audio_url": "/tts/audio/tts_b8ec64f725e2_20260126_205222.wav",
  "status": "success"
}

// Download audio
var audioResponse = await http.get(
  Uri.parse('http://backend:8001${response['audio_url']}'),
);
var audioBytes = audioResponse.bodyBytes;

// Save to device
var audioFile = File('${appDir.path}/audio.wav');
await audioFile.writeAsBytes(audioBytes);

// Or play directly
audioPlayer.play(audioBytes);
```

### For `/jobs` Endpoint (Async):

```dart
// Create job
var jobResponse = await http.post(
  Uri.parse('http://backend:8001/tts/jobs'),
  headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer $token'},
  body: jsonEncode({
    'text': 'Long text here...',
    'voice_id': 'en_US-lessac-high'
  }),
);

// Poll for completion
Future<String> waitForJobCompletion(String jobId) async {
  while (true) {
    var jobResponse = await http.get(
      Uri.parse('http://backend:8001/tts/jobs/$jobId'),
      headers: {'Authorization': 'Bearer $token'},
    );
    
    var job = jsonDecode(jobResponse.body);
    
    if (job['status'] == 'completed') {
      return job['audio_url'];  // S3 URL
    } else if (job['status'] == 'failed') {
      throw Exception('Job failed');
    }
    
    await Future.delayed(Duration(seconds: 5));
  }
}
```

---

## 🔧 Testing Verified

✅ API returns URL instead of base64:
```
GET http://localhost:8001/tts/sync
Response:
{
  "audio_url": "/tts/audio/tts_b8ec64f725e2_20260126_205222.wav",
  "duration": 3.63,
  "status": "success"
}
```

✅ Audio file can be downloaded:
```
GET http://localhost:8001/tts/audio/tts_b8ec64f725e2_20260126_205222.wav
Status: 200 OK
Content-Type: audio/wav
```

---

## 📌 Key Points

1. **URLs are returned immediately** - Flutter app gets file URL right away
2. **Audio saved to disk** - Files persist in `/output/` folder
3. **Database tracks jobs** - Async jobs are saved with metadata
4. **S3 integration works** - Audio can be uploaded to S3 if configured
5. **No base64** - Cleaner, faster, more efficient

---

## ⚠️ Important Notes

- Sync requests (`/tts/sync`) **do NOT** create database records
- Async requests (`/jobs`) **DO** create database records with full metadata
- Audio URL is **relative** (`/tts/audio/filename.wav`)
- Full URL for Flutter: `http://backend-ip:8001/tts/audio/filename.wav`
- Files are stored temporarily - implement cleanup if needed

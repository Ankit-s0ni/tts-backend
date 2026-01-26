# TTS Backend - Working Status Report

## ✅ Current Status: OPERATIONAL

### Voices Available: 40 Piper TTS Models
- **English (US)**: 6 voices
- **English (GB)**: 6 voices
- **German**: 6 voices
- **Spanish**: 8 voices
- **French**: 7 voices
- **Chinese**: 2 voices
- **Arabic**: 2 voices
- **Hindi (Indian)**: 3 voices ⭐ **NEW**

---

## 🎯 Indian Language Support (Now Available!)

### Hindi - 3 Native Voices Available
| Voice ID | Speaker | Gender | Quality |
|----------|---------|--------|---------|
| `hi_IN-pratham-medium` | Pratham | Male | Medium |
| `hi_IN-priyamvada-medium` | Priyamvada | Female | Medium |
| `hi_IN-rohan-medium` | Rohan | Male | Medium |

### Other Indian Languages
Currently NOT available (models not downloadable from Hugging Face):
- Telugu, Tamil, Marathi, Kannada

**Note**: These languages would require either:
1. Finding alternative TTS providers (like Google Cloud TTS, Azure, etc.)
2. Using Parler TTS (requires significant GPU memory)
3. Using eSpeak-ng as fallback

---

## 🔧 Technical Details

### API Endpoints

#### 1. List All Voices
```bash
GET /voices
```
Returns array of all 40 voices with metadata

#### 2. Synthesize Text (Synchronous)
```bash
POST /tts/sync
Content-Type: application/json

{
  "text": "नमस्ते। यह एक परीक्षण है।",
  "voice": "hi_IN-pratham-medium"
}
```

**Response:**
```json
{
  "audio": "ff2f4445...",  // hex-encoded WAV audio
  "duration": 2.46,         // seconds
  "text": "नमस्ते। यह एक परीक्षण है।",
  "voice_id": "hi_IN-pratham-medium",
  "engine": "piper",
  "sample_rate": 22050
}
```

### Performance Metrics

#### Long Text Synthesis (~1600 characters)

| Language | Voice | Duration | Processing Time | Audio Size |
|----------|-------|----------|-----------------|-----------|
| English | en_US-amy-medium | 101.62s | 9.6s | 4.27 MB |
| Hindi | hi_IN-pratham-medium | 82.04s | 6.4s | 3.45 MB |
| Hindi | hi_IN-priyamvada-medium | 96.93s | 7.2s | 4.08 MB |

**Notes:**
- Audio is 22.05 kHz sample rate
- Processing time includes disk I/O and JSON encoding
- Actual speech duration is slightly longer than processing time (Piper caches voices)

---

## 📦 Architecture

### Technology Stack
- **TTS Engine**: Piper (lightweight, offline, multilingual)
- **Framework**: FastAPI + Uvicorn
- **File Storage**: Cloudinary (configured)
- **Queue**: Celery with Redis
- **Monitoring**: Flower (http://localhost:5555)
- **Language Support**: 40 voices across 8+ languages

### Docker Services
1. **backend-api** - FastAPI server on port 8001
2. **piper** - Piper TTS HTTP server on port 5002 (internal)
3. **redis** - Queue broker on port 6379 (internal)
4. **worker** - Celery async worker
5. **flower** - Task monitoring on port 5555

---

## 🚀 Usage Examples

### Python
```python
import requests

response = requests.post(
    "http://localhost:8001/tts/sync",
    json={
        "text": "नमस्ते। आप कैसे हो?",
        "voice": "hi_IN-priyamvada-medium"
    }
)

data = response.json()
print(f"Duration: {data['duration']}s")
print(f"Audio size: {len(data['audio']) // 2} bytes")

# Convert hex audio back to binary
audio_bytes = bytes.fromhex(data['audio'])

# Save to file
with open("output.wav", "wb") as f:
    f.write(audio_bytes)
```

### cURL
```bash
curl -X POST http://localhost:8001/tts/sync \
  -H "Content-Type: application/json" \
  -d '{
    "text": "नमस्ते",
    "voice": "hi_IN-pratham-medium"
  }' | jq '.audio' | xxd -r -p > output.wav
```

---

## ⚙️ Configuration

### Environment Variables
See `.env` (development) or `.env.prod` (production)

Key settings:
- `MODELS_DIR=/models` - Path to Piper models
- `CLOUDINARY_CLOUD_NAME` - File storage
- `CLOUDINARY_API_KEY` - Authentication
- `REDIS_URL` - Queue broker
- `PIPER_URL` - Internal Piper service
- `MAX_CACHED_VOICES=5` - LRU cache size

---

## 📝 Testing

### Available Test Scripts
1. `test_voices_quick.py` - Quick voice availability test
2. `test_indian_voices.py` - Test Hindi voices specifically
3. `test_long_text.py` - Test with 2-3 page documents

### Run Tests
```bash
# Quick test
python test_voices_quick.py

# Hindi test
python test_indian_voices.py

# Long text test (2-3 pages)
python test_long_text.py
```

---

## 🔍 Troubleshooting

### API not responding
```bash
docker-compose -f docker-compose.dev.yml restart backend-api
```

### Voice not found
- Ensure model directory exists: `ls piper_models/VOICE_ID/`
- Restart API to rescan models
- Check voice catalog: `docker exec backend-backend-api-1 python check_catalog.py`

### Voice synthesis failing
```bash
docker logs backend-backend-api-1
```

### Clear cache
```bash
docker exec backend-backend-api-1 python -c "
from app.voice_catalog import refresh_catalog
refresh_catalog()
print('Cache cleared')
"
```

---

## 📋 Next Steps (Optional)

1. **Add More Indian Languages**: Download/host models for Telugu, Tamil, Marathi, Kannada
2. **Async Processing**: Implement job queuing for very long texts
3. **Streaming Output**: Return audio stream instead of base64
4. **Voice Cloning**: Add custom voice training capability
5. **Quality Control**: Implement audio quality metrics

---

## 📅 Last Updated
January 27, 2026

## ✨ Status Summary
- ✅ English voices: Working
- ✅ European languages: Working  
- ✅ Hindi (Indian): Working
- ❌ Other Indian languages: Models not available
- ✅ Cloudinary integration: Configured
- ✅ Long text synthesis: Tested up to 2-3 pages
- ✅ Docker deployment: Stable

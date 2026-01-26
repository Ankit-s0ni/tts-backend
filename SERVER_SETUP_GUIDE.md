# TTS App - Complete Server Setup Guide

This guide walks through setting up the entire TTS application on a server from scratch.

## Prerequisites

- **OS:** Linux (Ubuntu 20.04+ recommended) or Windows with Docker Desktop
- **Docker & Docker Compose:** Latest versions installed
- **Git:** For cloning the repository
- **Hardware:** Minimum 4GB RAM, 20GB storage (for voice models)
- **Network:** Port 8001 (API), 5000 (Piper), 6379 (Redis), 27017 (MongoDB) accessible

---

## Step 1: Clone Repository

```bash
cd /opt  # or your preferred location
git clone https://github.com/your-org/TTS-app-.git
cd TTS-app-/backend
```

---

## Step 2: Configure Environment Variables

Create `.env` file in the backend directory:

```bash
cat > .env << 'EOF'
# Backend environment variables for the TTS app

# --- AWS Cognito (required for authentication) ---
COGNITO_USER_POOL_ID=ap-south-1_l83RwflUR
COGNITO_APP_CLIENT_ID=93msebuj6quogjq6cgtkerl3f
AWS_REGION=ap-south-1

# Optional test token for local testing
TEST_COGNITO_TOKEN=

# --- Database / Storage / Services ---
# MongoDB connection (primary database for jobs, audio metadata, users)
# Default: MongoDB container from docker-compose
MONGODB_URL=mongodb://localhost:27017/tts_production

# Piper TTS server URL
PIPER_URL=http://piper-service:5000/

# --- Cloudinary Configuration (Optional) ---
# Update with your actual Cloudinary credentials
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# --- DynamoDB Configuration (Optional) ---
DYNAMODB_REGION=ap-south-1
# DYNAMODB_ENDPOINT_URL=

# --- AWS Credentials (if using AWS services) ---
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
EOF
```

**Replace the following values:**
- `COGNITO_USER_POOL_ID` - Your AWS Cognito user pool ID
- `COGNITO_APP_CLIENT_ID` - Your Cognito app client ID
- `CLOUDINARY_CLOUD_NAME` - Your Cloudinary account name (optional, system works without it)
- `CLOUDINARY_API_KEY` - Your Cloudinary API key (optional)
- `CLOUDINARY_API_SECRET` - Your Cloudinary API secret (optional)

---

## Step 3: Build and Start Docker Containers

### Option A: Development Environment

```bash
# Build all images
docker-compose -f docker-compose.dev.yml build

# Start all services in background
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f
```

### Option B: Production Environment

```bash
# Build all images
docker-compose -f docker-compose.prod.yml build

# Start all services in background
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## Step 4: Verify All Services Are Running

```bash
# Check all containers
docker ps

# Expected output should show 5 containers:
# - backend-api (FastAPI)
# - piper (TTS engine)
# - redis (cache)
# - celery-worker (task queue)
# - flower (Celery monitoring)
```

Expected containers:
- `backend-backend-api-1` - REST API
- `backend-piper-1` - Piper TTS service
- `backend-redis-1` - Redis cache
- `backend-celery-worker-1` - Celery task worker
- `backend-flower-1` - Celery monitoring

---

## Step 5: Initialize Database

### MongoDB Setup

```bash
# MongoDB is included in docker-compose
# It automatically initializes on first run

# Verify MongoDB is running
docker exec backend-mongodb mongosh --eval "db.adminCommand('ping')"

# Expected output: { ok: 1 }
```

### Create Initial Collections (Optional)

```bash
docker exec backend-mongodb mongosh << 'EOF'
use tts_production
db.createCollection("jobs")
db.createCollection("users")
db.createCollection("voices")
db.createCollection("chunks")
db.createCollection("verification_codes")
EOF
```

---

## Step 6: Download Piper Voice Models

Voice models are automatically downloaded on first TTS request. However, you can pre-download them:

```bash
# Access the backend container
docker exec -it backend-backend-api-1 bash

# Pre-download voices (optional, reduces first-request latency)
python /models/download_voices.py

# Exit container
exit
```

---

## Step 7: Verify API Endpoints

### Test TTS Sync Endpoint

```bash
curl -X POST http://localhost:8001/tts/sync \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test",
    "voice": "en_US-lessac-high"
  }' | jq .
```

**Expected response:**
```json
{
  "duration": 2.5,
  "text": "Hello, this is a test",
  "voice_id": "en_US-lessac-high",
  "engine": "piper",
  "sample_rate": 22050,
  "status": "success",
  "audio_url": "/tts/audio/tts_abc123_20260127_123456.wav"
}
```

### Test Voices List Endpoint

```bash
curl -X GET http://localhost:8001/voices | jq . | head -50
```

**Expected:** JSON array with 45 voices including:
- English voices (en_US, en_GB, en_AU)
- Spanish voices
- French voices
- German voices
- **NEW:** Malayalam voices (ml_IN-arjun, ml_IN-meera)
- **NEW:** Telugu voices (te_IN-maya, te_IN-padmavathi, te_IN-venkatesh)

### Test Health Check

```bash
curl -X GET http://localhost:8001/health
```

---

## Step 8: Download Audio from URL

Once you get an audio URL from `/tts/sync`:

```bash
# Download audio file
curl -X GET "http://localhost:8001/tts/audio/tts_abc123_20260127_123456.wav" \
  -o audio.wav

# Verify file
ls -lh audio.wav
ffprobe audio.wav  # If ffmpeg installed
```

---

## Step 9: Configure Reverse Proxy (Production)

### Nginx Configuration

Create `/etc/nginx/sites-available/tts-app`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # API proxy
    location /api/ {
        proxy_pass http://localhost:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # File serving
    location /tts/audio/ {
        proxy_pass http://localhost:8001/tts/audio/;
        proxy_cache_valid 200 7d;
        add_header Cache-Control "public, max-age=604800";
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/tts-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Step 10: Monitor Services

### Check API Logs

```bash
docker logs -f backend-backend-api-1
```

### Check Celery Worker Logs

```bash
docker logs -f backend-celery-worker-1
```

### Access Celery Flower Dashboard

```
http://localhost:5555
```

(No authentication by default, secure with reverse proxy)

---

## Step 11: Backup and Maintenance

### Backup Database

```bash
# Backup MongoDB
docker exec backend-mongodb mongodump --out /backup

# Copy to host
docker cp backend-mongodb:/backup /path/to/backup/location
```

### Backup Generated Audio Files

```bash
# Audio files location
docker exec backend-backend-api-1 ls -lah /app/output/

# Copy files to host
docker cp backend-backend-api-1:/app/output /path/to/backup/audio
```

### Clean Old Audio Files

```bash
# Remove audio files older than 7 days
docker exec backend-backend-api-1 bash -c 'find /app/output -name "*.wav" -mtime +7 -delete'
```

---

## Step 12: Environment-Specific Setup

### For Production

1. **Use remote MongoDB:**
   ```bash
   MONGODB_URL=mongodb://user:password@mongo-server:27017/tts_production
   ```

2. **Enable Cloudinary for CDN:**
   ```bash
   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_key
   CLOUDINARY_API_SECRET=your_secret
   ```

3. **Increase worker count:**
   ```bash
   # In docker-compose.prod.yml, scale workers:
   docker-compose -f docker-compose.prod.yml up --scale celery-worker=3
   ```

4. **Enable rate limiting and authentication**
   - Configure API keys in `/app/config.py`
   - Enable JWT token validation

---

## Troubleshooting

### Issue: API not responding

```bash
# Check if container is running
docker ps | grep backend-api

# If not running, check logs
docker logs backend-backend-api-1

# Restart container
docker restart backend-backend-api-1
```

### Issue: Cloudinary upload failing

```bash
# Check logs for Cloudinary errors
docker logs backend-backend-api-1 | grep -i cloudinary

# Verify credentials in .env
cat .env | grep CLOUDINARY

# System falls back to local URLs automatically
# This is not critical for operation
```

### Issue: Piper TTS not responding

```bash
# Check Piper service
docker logs backend-piper-1

# Verify it's listening
docker exec backend-piper-1 curl http://localhost:5000/

# Restart Piper
docker restart backend-piper-1
```

### Issue: MongoDB connection failed

```bash
# Check MongoDB logs
docker logs backend-mongodb

# Verify connection string in .env
cat .env | grep MONGODB_URL

# Test connection
docker exec backend-mongodb mongosh --eval "db.adminCommand('ping')"
```

### Issue: Out of memory

```bash
# Check Docker resource usage
docker stats

# Increase Docker memory limit
# Edit docker-compose.yml and add:
# mem_limit: 4g
# mem_reservation: 2g

# Restart containers
docker-compose restart
```

---

## Performance Tuning

### Increase Celery Worker Concurrency

```bash
# In docker-compose.yml, update celery-worker command:
command: celery -A celery_worker worker --loglevel=info --concurrency=4
```

### Enable Redis Persistence

```bash
# In docker-compose.yml, add volume:
volumes:
  - redis_data:/data
```

### Cache Voice Models

```bash
# In .env, increase cache size:
MAX_CACHED_VOICES=10
```

---

## Daily Operations

### Start Services

```bash
cd /opt/TTS-app-/backend
docker-compose -f docker-compose.prod.yml up -d
```

### Stop Services

```bash
docker-compose -f docker-compose.prod.yml down
```

### View Logs

```bash
# Last 100 lines
docker-compose logs -n 100 -f

# Specific service
docker-compose logs -f backend-api
```

### Update Code

```bash
git pull origin main
docker-compose build
docker-compose up -d
```

---

## API Reference

### POST /tts/sync (Synchronous)

```bash
curl -X POST http://localhost:8001/tts/sync \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your text here",
    "voice": "en_US-lessac-high"
  }'
```

**Response:**
```json
{
  "duration": 3.5,
  "text": "Your text here",
  "voice_id": "en_US-lessac-high",
  "engine": "piper",
  "sample_rate": 22050,
  "status": "success",
  "audio_url": "/tts/audio/tts_xyz.wav"
}
```

### GET /voices

```bash
curl -X GET http://localhost:8001/voices
```

Returns list of 45 available voices.

### GET /tts/audio/{filename}

```bash
curl -X GET http://localhost:8001/tts/audio/tts_xyz.wav -o audio.wav
```

Downloads WAV audio file.

### POST /jobs (Asynchronous)

```bash
curl -X POST http://localhost:8001/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "text": "Your long text...",
    "voice_id": "en_US-lessac-high"
  }'
```

**Response:**
```json
{
  "id": "job_uuid",
  "status": "queued",
  "created_at": "2026-01-27T10:00:00"
}
```

### GET /jobs/{job_id}

```bash
curl -X GET http://localhost:8001/jobs/job_uuid \
  -H "Authorization: Bearer $JWT_TOKEN"
```

Returns job status and `audio_url` when complete.

---

## Firewall Rules

Open these ports:

```bash
# Public API
sudo ufw allow 443/tcp    # HTTPS
sudo ufw allow 80/tcp     # HTTP (redirect)

# Internal services (if exposing)
sudo ufw allow 5555/tcp   # Flower (Celery monitoring)

# Do NOT expose these to public:
# 5000 - Piper (internal only)
# 6379 - Redis (internal only)
# 27017 - MongoDB (internal only)
```

---

## Security Checklist

- [ ] Update Cognito credentials
- [ ] Set strong Cloudinary API key
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure firewall to restrict ports
- [ ] Enable authentication on all endpoints
- [ ] Set up log rotation
- [ ] Enable MongoDB authentication
- [ ] Use environment-specific .env files
- [ ] Implement API rate limiting
- [ ] Regular database backups

---

## Support & Debugging

### Enable Debug Logging

```bash
# Edit docker-compose.yml and add:
environment:
  - LOG_LEVEL=DEBUG

# Restart services
docker-compose restart
```

### Check System Health

```bash
# All services
docker-compose ps

# Resource usage
docker stats

# Logs from all services
docker-compose logs --tail=50
```

### Common Ports

- **8001** - API
- **5000** - Piper TTS
- **6379** - Redis
- **27017** - MongoDB
- **5555** - Flower dashboard

---

## Version Information

- **Python:** 3.11
- **FastAPI:** Latest
- **Piper:** Latest
- **MongoDB:** 5.x
- **Redis:** 7.x
- **Celery:** 5.x

---

## Next Steps

1. Deploy to your server
2. Configure SSL/TLS certificates
3. Set up monitoring (Prometheus, Grafana)
4. Configure backups
5. Test with your Flutter app
6. Scale horizontally if needed

Happy TTS! 🎵

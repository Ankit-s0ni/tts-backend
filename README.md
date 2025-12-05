# TTS Backend

This folder contains the FastAPI backend for the TTS application with AWS DynamoDB, S3, and Celery worker integration.

## Prerequisites

- Python 3.8+
- Docker and Docker Compose
- AWS Account with DynamoDB and S3 configured

## How to Run (Development)

### 1. Install Dependencies

First, install all required Python packages:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the backend directory with the following variables:

```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-south-1
AWS_S3_BUCKET=your_s3_bucket_name

# DynamoDB Tables
DYNAMODB_TABLE_USERS=users
DYNAMODB_TABLE_NAME=jobs

# Redis
REDIS_URL=redis://redis:6379/0

# Application
DATABASE_URL=sqlite:///./dev.db
PIPER_URL=http://piper-service:5000/
```

### 3. Start All Services with Docker Compose

Run the following command to start all services (Redis, Backend, Worker, and Piper):

```powershell
docker compose -f docker-compose.dev.yml up -d
```

This will start:
- **Redis** - Message broker for Celery
- **Backend** - FastAPI application (accessible at `http://localhost:8002`)
- **Worker** - Celery worker for processing TTS jobs
- **Piper Service** - TTS engine (optional, can be enabled in docker-compose.dev.yml)

### 4. Check Service Status

```powershell
docker compose -f docker-compose.dev.yml ps
```

### 5. View Logs

```powershell
# All services
docker compose -f docker-compose.dev.yml logs -f

# Specific service
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f worker
```

### 6. Stop Services

```powershell
docker compose -f docker-compose.dev.yml down
```

## Alternative: Local Development (Without Docker)

If you prefer to run services locally:

### 1. Start Redis

```powershell
docker compose -f docker-compose.dev.yml up -d redis
```

### 2. Start Backend

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start Celery Worker

```powershell
celery -A celery_worker.celery_app worker --loglevel=info -Q celery,default,parler_gpu_queue --concurrency=1
```

## API Endpoints

- `GET /` - Health check
- `POST /tts/create` - Create TTS job
- `GET /jobs/{job_id}` - Get job status
- `GET /jobs` - List user jobs
- `GET /audio/{job_id}` - Stream audio file

## Notes

- The backend uses **AWS DynamoDB** for job storage (not local SQLite for production)
- Audio files are stored in **AWS S3** and served via pre-signed URLs
- Piper models are mounted from `../piper_models` directory
- The worker processes jobs asynchronously using Celery

## Troubleshooting

### Reset Local Database

```powershell
Remove-Item .\dev.db -Force
```

### Check AWS Credentials

```powershell
aws sts get-caller-identity
```

### Test DynamoDB Connection

```powershell
python test_aws_dynamo.py
```

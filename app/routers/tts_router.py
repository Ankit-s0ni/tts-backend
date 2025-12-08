from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import Response, JSONResponse
from .. import schemas
from ..dynamo import create_job_item, get_job_item, get_user_jobs
from ..voice_catalog import get_voice
from ..utils.s3_utils import generate_presigned_url
import httpx
from ..config import settings
from ..auth import get_current_user
import os
import wave
import uuid
from pathlib import Path
from datetime import datetime

router = APIRouter(prefix="/tts", tags=["tts"])


@router.post("/sync")
async def tts_sync(request: Request):
    """
    Synchronous TTS endpoint that returns JSON with audio URL and duration.
    Saves audio to a public directory and returns the URL.
    """
    payload = await request.json()

    # If a voice id is provided and we have a DynamoDB entry with a concrete
    # `model_path`, inject that into the Piper request as `model` so Piper will
    # use the exact ONNX file instead of falling back to the server default.
    try:
        voice_id = payload.get("voice")
        if voice_id:
            v = get_voice(voice_id)
            if v and v.get("model_path"):
                # Forward a voice id (model name) rather than a filesystem
                # `model` path — Piper will look for <model_id>.onnx in the
                # mounted data directories and load it.
                from pathlib import Path

                model_id = Path(v["model_path"]).stem
                payload["voice"] = model_id
                try:
                    payload.pop("model", None)
                except Exception:
                    pass
    except Exception:
        # non-fatal: if lookups fail, continue and let Piper decide
        pass

    # Normalize PIPER_URL: may be root (http://host:port/) or include path
    piper_url = str(settings.PIPER_URL)
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # If PIPER_URL ends with '/', post to root; else post to the configured URL
            if piper_url.rstrip("/").endswith("/synthesize"):
                target = piper_url
            else:
                # try posting to root first
                target = piper_url
            # Log the model being requested for easier debugging and show if
            # a 'voice' key is accidentally being forwarded.
            if payload.get("model") or payload.get("voice"):
                print(f"[tts_sync] Posting to Piper with keys={list(payload.keys())} voice={payload.get('voice')} model={payload.get('model')}")
            resp = await client.post(target, json=payload)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Piper request failed: {exc}")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    # Get audio bytes from Piper
    audio_bytes = resp.content
    
    # Calculate duration from WAV file
    try:
        import io
        wav_io = io.BytesIO(audio_bytes)
        with wave.open(wav_io, 'rb') as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            duration = frames / rate if rate > 0 else 0.0
    except Exception:
        duration = 0.0
    
    # Create output directory if it doesn't exist
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    filename = f"tts_{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    filepath = output_dir / filename
    
    # Save audio file
    try:
        with open(filepath, 'wb') as f:
            f.write(audio_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save audio file: {str(e)}")
    
    # Return JSON response with audio URL and duration
    # The URL path should be accessible via the backend server
    audio_url = f"/tts/audio/{filename}"
    
    return JSONResponse({
        "audio_url": audio_url,
        "duration": duration,
        "filename": filename,
    })


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    """
    Serve generated audio files.
    """
    # Security: only allow serving .wav files and prevent directory traversal
    if not filename.endswith(".wav") or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    output_dir = Path(__file__).parent.parent / "output"
    filepath = output_dir / filename
    
    # Check if file exists
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Return the audio file
    with open(filepath, 'rb') as f:
        audio_bytes = f.read()
    
    return Response(content=audio_bytes, media_type="audio/wav")


@router.post("/jobs", response_model=schemas.JobOut)
def create_job(job_in: schemas.JobCreate, current_user=Depends(get_current_user)):
    # create job in DynamoDB. `current_user.id` may be a Cognito `sub` string.
    job = create_job_item(current_user.id if hasattr(current_user, "id") else None, job_in.dict())
    # enqueue celery task to process job (import locally to avoid circular/import issues)
    try:
        import celery_worker
        celery_worker.process_job.delay(int(job["id"]))
    except Exception:
        pass
    # convert to JobOut-compatible dict
    return {
        "id": int(job["id"]),
        "status": job.get("status", "queued"),
        "created_at": job.get("created_at"),
        "audio_url": job.get("audio_s3_url") or job.get("s3_final_url")
    }


@router.get("/jobs/{job_id}")
@router.get("/jobs/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: int, current_user=Depends(get_current_user)):
    job = get_job_item(job_id)
    # job['user_id'] may be numeric (legacy) or a Cognito sub string. Compare
    # by string representation if present.
    job_user = job.get("user_id") if job else None
    current_id = getattr(current_user, "id", None)
    if not job or (job_user is None) or (str(job_user) != str(current_id)):
        raise HTTPException(status_code=404, detail="Job not found")

    # Return job info with proxy URL for audio streaming
    audio_url = None
    if job.get("status") == "completed" and job.get("audio_s3_key"):
        audio_url = f"/tts/jobs/{job_id}/audio"
    
    return {
        "id": int(job["id"]),
        "status": job.get("status", "unknown"),
        "created_at": job.get("created_at"),
        "audio_url": audio_url
    }


@router.get("/jobs/{job_id}/audio")
async def stream_job_audio(job_id: int, current_user=Depends(get_current_user)):
    """Stream audio file for a job. Acts as a proxy to handle S3 authentication."""
    job = get_job_item(job_id)
    job_user = job.get("user_id") if job else None
    current_id = getattr(current_user, "id", None)
    
    if not job or (job_user is None) or (str(job_user) != str(current_id)):
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    s3_key = job.get("audio_s3_key")
    if not s3_key:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # Stream from S3 using backend credentials
    import boto3
    import os
    from botocore.exceptions import ClientError
    
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        bucket = os.getenv("AWS_S3_BUCKET")
        
        # Get object from S3
        response = s3.get_object(Bucket=bucket, Key=s3_key)
        audio_data = response['Body'].read()
        
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"inline; filename=job_{job_id}.wav",
                "Content-Length": str(len(audio_data)),
                "Accept-Ranges": "bytes",
            }
        )
    except ClientError as e:
        print(f"S3 Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve audio from storage")


@router.get("/jobs")
def list_user_jobs(current_user=Depends(get_current_user), limit: int = 50):
    """Get all jobs for the authenticated user."""
    current_id = getattr(current_user, "id", None)
    if not current_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    jobs = get_user_jobs(current_id, limit=limit)
    
    # Convert to JobOut format - use proxy endpoint for audio streaming
    result = []
    for job in jobs:
        audio_url = None
        
        # Use proxy endpoint for completed jobs instead of direct S3 URLs
        # Check for audio_s3_key OR s3_final_url (both are used in different parts of the code)
        if job.get("status") == "completed" and (job.get("audio_s3_key") or job.get("s3_final_url")):
            # Use backend proxy endpoint which will stream from S3
            audio_url = f"/tts/jobs/{job['id']}/audio"
        
        result.append({
            "id": int(job["id"]),
            "status": job.get("status", "unknown"),
            "created_at": job.get("created_at"),
            "audio_url": audio_url,
            "text": job.get("text", "")[:100],  # First 100 chars as preview
            "voice_id": job.get("voice_id"),
        })
    
    return result

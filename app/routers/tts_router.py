from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import Response, JSONResponse
from .. import schemas
from ..mongo_db import create_job_item, get_job_item, get_user_jobs
from ..voice_catalog import get_voice, engine_for_voice
from ..utils.s3_utils_simple import generate_presigned_url
import httpx
from ..config import settings
from ..auth_email import get_current_user
import os
import wave
import uuid
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tts", tags=["tts"])


@router.post("/sync")
async def tts_sync(request: Request):
    """
    Synchronous TTS endpoint that returns JSON with audio URL and duration.
    Routes to either Piper or Parler based on voice engine.
    """
    payload = await request.json()
    voice_id = payload.get("voice")
    
    # Get voice metadata
    voice = get_voice(voice_id) if voice_id else None
    engine = voice.get("engine") if voice else "piper"
    
    # Route to appropriate engine
    if engine == "parler":
        return await _tts_sync_parler(payload, voice)
    else:
        return await _tts_sync_piper(payload, voice)


async def _tts_sync_parler(payload: dict, voice: dict):
    """Handle Parler TTS synthesis."""
    text = payload.get("text", "")
    voice_id = payload.get("voice")
    
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    if not voice_id:
        raise HTTPException(status_code=400, detail="Voice is required")
    
    try:
        # Import synthesis function
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from parler_worker import synthesize_parler
        
        # Call Parler synthesis directly (synchronous)
        result = synthesize_parler(
            job_id=0,  # Dummy job_id for sync call
            text=text,
            voice_id=voice_id
        )
        
        if result.get("status") != "success":
            error_msg = result.get("error", "Unknown error")
            raise HTTPException(status_code=500, detail=f"Parler synthesis failed: {error_msg}")
        
        # Get audio file
        filename = result.get("audio_file")
        output_dir = Path(__file__).parent.parent / "output"
        filepath = output_dir / filename
        
        with open(filepath, 'rb') as f:
            audio_bytes = f.read()
        
        # Calculate duration
        try:
            import io
            wav_io = io.BytesIO(audio_bytes)
            with wave.open(wav_io, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / rate if rate > 0 else 0.0
        except Exception:
            duration = 0.0
        
        audio_url = f"/tts/audio/{filename}"
        
        return JSONResponse({
            "audio_url": audio_url,
            "duration": duration,
            "filename": filename,
            "engine": "parler"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Parler synthesis error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def _tts_sync_piper(payload: dict, voice: dict = None):
    """Handle Piper TTS synthesis."""
    # If a voice id is provided and we have a DynamoDB entry with a concrete
    # `model_path`, inject that into the Piper request as `model` so Piper will
    # use the exact ONNX file instead of falling back to the server default.
    try:
        voice_id = payload.get("voice")
        if voice_id and voice and voice.get("model_path"):
            model_id = Path(voice["model_path"]).stem
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
                logger.info(f"[tts_sync_piper] Posting to Piper with keys={list(payload.keys())} voice={payload.get('voice')} model={payload.get('model')}")
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
        "engine": "piper"
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
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    user_id = str(current_user.id) if hasattr(current_user, "id") else "anonymous"
    
    # Create job in simple storage
    job_data = job_in.dict()
    job = create_job_item(
        job_id=job_id,
        user_id=user_id,
        text=job_data.get("text", ""),
        voice_id=job_data.get("voice_id", ""),
        status="queued"
    )
    
    logger.info(f"[create_job] Job created with user_id: {job.get('user_id')}")
    
    # enqueue celery task to process job (import locally to avoid circular/import issues)
    try:
        import celery_worker
        celery_worker.process_job.delay(job_id)
    except Exception:
        pass
    
    # convert to JobOut-compatible dict
    return {
        "id": job["job_id"],
        "status": job.get("status", "queued"),
        "created_at": job.get("created_at"),
        "audio_url": job.get("audio_url")
    }


@router.get("/jobs/{job_id}")
@router.get("/jobs/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: str, current_user=Depends(get_current_user)):
    job = get_job_item(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check authorization: ensure user owns this job
    job_user_id = job.get("user_id")
    current_id = getattr(current_user, "id", None)
    
    # Convert both to strings for comparison
    job_user_id_str = str(job_user_id) if job_user_id else None
    current_id_str = str(current_id) if current_id else None
    
    # Access control: Allow access only if:
    # 1. User owns the job (user_id matches), OR
    # 2. Job has no user_id (anonymous/public)
    if job_user_id_str is not None:  # Job has a user_id set
        if job_user_id_str != "anonymous" and job_user_id_str != current_id_str:
            raise HTTPException(status_code=403, detail="Access denied")

    # Return job info with audio URL
    audio_url = None
    if job.get("status") == "completed":
        # Return direct audio_url if available (Cloudinary URL)
        # Otherwise generate proxy URL if we have s3_final_url
        if job.get("audio_url"):
            audio_url = job.get("audio_url")
        elif job.get("audio_s3_key") or job.get("s3_final_url"):
            # Generate proxy endpoint URL for local audio streaming
            audio_url = f"/tts/jobs/{job_id}/audio"
    
    return {
        "id": job["job_id"],
        "status": job.get("status", "unknown"),
        "created_at": job.get("created_at"),
        "audio_url": audio_url
    }


@router.get("/jobs/{job_id}/audio")
async def stream_job_audio(job_id: str, current_user=Depends(get_current_user)):
    """Stream audio file for a job. Acts as a proxy to handle authentication."""
    job = get_job_item(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check authorization: ensure user owns this job
    job_user_id = job.get("user_id")
    current_id = getattr(current_user, "id", None)
    
    # Convert both to strings for comparison
    job_user_id_str = str(job_user_id) if job_user_id else None
    current_id_str = str(current_id) if current_id else None
    
    # Access control: Allow access only if:
    # 1. User owns the job (user_id matches), OR
    # 2. Job has no user_id (anonymous/public)
    if job_user_id_str is not None:  # Job has a user_id set
        if job_user_id_str != "anonymous" and job_user_id_str != current_id_str:
            raise HTTPException(status_code=403, detail="Access denied")
    
    if job.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    audio_url = job.get("audio_url")
    if not audio_url:
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # If audio_url is a Cloudinary URL, redirect to it
    if audio_url.startswith("https://"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=audio_url, status_code=307)
    
    # If it's a local path, serve it
    if os.path.exists(audio_url):
        with open(audio_url, "rb") as f:
            audio_data = f.read()
        return Response(
            content=audio_data,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"inline; filename=job_{job_id}.wav",
                "Content-Length": str(len(audio_data)),
            }
        )
    
    raise HTTPException(status_code=404, detail="Audio file not accessible")


@router.get("/jobs")
def list_user_jobs(current_user=Depends(get_current_user), limit: int = 50):
    """Get all jobs for the authenticated user."""
    current_id = getattr(current_user, "id", None)
    if not current_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # Ensure user_id is a string for consistent filtering
    user_id_str = str(current_id)
    jobs = get_user_jobs(user_id_str, limit=limit)
    
    # Convert to JobOut format - return direct Cloudinary URLs or proxy endpoint
    result = []
    for job in jobs:
        audio_url = None
        job_id = job.get("job_id") or job.get("id")
        
        # For completed jobs, return audio URL
        if job.get("status") == "completed":
            # Prefer direct Cloudinary URL if available
            if job.get("audio_url"):
                audio_url = job.get("audio_url")
            elif job.get("audio_s3_key") or job.get("s3_final_url"):
                # Fallback to proxy endpoint for local files
                audio_url = f"/tts/jobs/{job_id}/audio"
        
        result.append({
            "id": job_id,
            "status": job.get("status", "unknown"),
            "created_at": job.get("created_at"),
            "audio_url": audio_url,
            "text": job.get("text", "")[:100],  # First 100 chars as preview
            "voice_id": job.get("voice_id"),
        })
    
    return result

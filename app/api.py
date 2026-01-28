from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response, JSONResponse
import io
import wave
import os
import uuid
import tempfile
import cloudinary
import cloudinary.uploader
from pathlib import Path
from datetime import datetime
from .config import settings
from .voice_catalog import list_available_voices, get_voice
from .voice_manager import get_voice_manager

router = APIRouter()

# Configure Cloudinary at module level if credentials are available
if settings.CLOUDINARY_URL:
    # CLOUDINARY_URL is in format: cloudinary://api_key:api_secret@cloud_name
    cloudinary.config(cloudinary_url=settings.CLOUDINARY_URL)
elif settings.CLOUDINARY_CLOUD_NAME:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET
    )


@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify API is running and latest changes are deployed.
    Returns status of all critical services.
    """
    try:
        # Check Piper TTS availability
        piper_available = False
        try:
            import httpx
            async with httpx.AsyncClient(timeout=2) as client:
                resp = await client.get(f"{settings.PIPER_URL}/")
                piper_available = resp.status_code < 500
        except:
            piper_available = False
        
        # Check Cloudinary configuration
        cloudinary_configured = bool(settings.CLOUDINARY_URL or settings.CLOUDINARY_CLOUD_NAME)
        
        # Check output directory exists
        output_dir = Path(__file__).parent.parent / "output"
        output_dir_exists = output_dir.exists()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0",
            "services": {
                "api": "running",
                "piper_tts": "available" if piper_available else "unavailable",
                "cloudinary": "configured" if cloudinary_configured else "not_configured",
                "file_storage": "ready" if output_dir_exists else "not_ready"
            },
            "features": {
                "tts_sync": True,
                "tts_async": True,
                "voice_list": True,
                "auth_email": True,
                "cloudinary_upload": cloudinary_configured,
                "audio_serving": output_dir_exists
            },
            "recent_changes": {
                "cloudinary_url_support": "✅ CLOUDINARY_URL environment variable support",
                "auth_link_profile": "✅ POST /auth/link-profile endpoint added",
                "auth_me_put": "✅ PUT /auth/me endpoint for profile updates",
                "profile_update": "✅ User profile update (full_name, phone, age, profile_image)",
                "optional_age": "✅ Age field is optional during registration"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/voices")
async def list_voices_api():
    voices = list_available_voices()
    # sort by language then display name (or id)
    voices_sorted = sorted(
        voices, key=lambda v: (v.get("language", ""), v.get("display_name") or v.get("id"))
    )
    return voices_sorted


@router.post("/tts/sync")
async def tts_sync(request: Request):
    """Synchronous TTS using Piper for all voices.

    Expects JSON body: { "text": "...", "voice": "..." }
    Returns JSON with audio URL and duration.
    """
    payload = await request.json()
    text = payload.get("text", "")
    voice_id = payload.get("voice", "en_US-lessac-medium")
    
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    try:
        # Get voice metadata
        voice_meta = get_voice(voice_id)
        if not voice_meta:
            raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' not found")
        
        # Use Piper for synthesis
        return await _tts_sync_piper(text, voice_id, voice_meta)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")


async def _tts_sync_piper(text: str, voice_id: str, voice_meta: dict):
    """Handle Piper TTS synthesis."""
    model_path = voice_meta.get("model_path")
    if not model_path:
        raise HTTPException(status_code=500, detail=f"No model_path for voice '{voice_id}'")
    
    try:
        # Load voice with caching
        voice_manager = get_voice_manager()
        voice = voice_manager.get_voice(model_path)
        
        if voice is None:
            raise HTTPException(status_code=500, detail="Failed to load Piper voice model")
        
        # Synthesize audio using Piper Python API
        audio_chunks = []
        sample_rate = None
        sample_width = None
        sample_channels = None
        
        for audio_chunk in voice.synthesize(text):
            if sample_rate is None:
                sample_rate = audio_chunk.sample_rate
                sample_width = audio_chunk.sample_width
                sample_channels = audio_chunk.sample_channels
            audio_chunks.append(audio_chunk.audio_int16_bytes)
        
        if not audio_chunks:
            raise HTTPException(status_code=500, detail="No audio generated")
        
        # Combine all audio chunks
        audio_data = b''.join(audio_chunks)
        
        # Create WAV file in memory
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(sample_channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data)
        
        wav_bytes = wav_io.getvalue()
        
        # Calculate duration
        frames = len(audio_data) // (sample_width * sample_channels)
        duration = frames / sample_rate if sample_rate > 0 else 0.0
        
        # Create output directory for temporary storage
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save audio file to disk temporarily
        filename = f"tts_{uuid.uuid4().hex[:12]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        filepath = output_dir / filename
        
        try:
            with open(filepath, 'wb') as f:
                f.write(wav_bytes)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save audio file: {str(e)}")
        
        # Upload to Cloudinary
        audio_url = None
        try:
            if settings.CLOUDINARY_URL or settings.CLOUDINARY_CLOUD_NAME:
                print(f"DEBUG: Uploading to Cloudinary...")
                # Create a unique public_id
                public_id = f"tts/{voice_id}/{uuid.uuid4().hex[:12]}"
                
                # Upload the WAV file to Cloudinary
                result = cloudinary.uploader.upload(
                    str(filepath),
                    resource_type="video",
                    public_id=public_id,
                    overwrite=False
                )
                
                audio_url = result.get("secure_url")
                if audio_url:
                    print(f"✅ Successfully uploaded to Cloudinary: {audio_url}")
                else:
                    print(f"Cloudinary upload result: {result}")
        except Exception as e:
            print(f"Cloudinary upload failed: {e}")
            import traceback
            traceback.print_exc()
        
        # If Cloudinary upload fails, fall back to local URL
        if not audio_url:
            audio_url = f"/tts/audio/{filename}"
            print(f"Using fallback local URL: {audio_url}")
        
        # Return response with audio URL
        response = {
            "duration": duration,
            "text": text,
            "voice_id": voice_id,
            "engine": "piper",
            "sample_rate": sample_rate,
            "status": "success",
            "audio_url": audio_url
        }
        
        return JSONResponse(response)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Piper synthesis failed: {str(e)}")


@router.get("/tts/audio/{filename}")
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

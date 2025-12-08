from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response, JSONResponse
import io
import wave
import os
import uuid
import boto3
from pathlib import Path
from datetime import datetime
from .config import settings
from .voice_catalog import list_available_voices, get_voice
from .voice_manager import get_voice_manager
from .utils.s3_temp_audio import upload_to_s3, save_to_dynamodb

router = APIRouter()


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
    """Synchronous TTS using Piper Python API with VoiceManager cache.

    Expects JSON body: { "text": "...", "voice": "...", ... }
    Returns JSON with S3 audio URL and duration.
    """
    payload = await request.json()
    text = payload.get("text", "")
    voice_id = payload.get("voice", "en_US-lessac-medium")
    
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    try:
        # Get voice metadata from DynamoDB
        voice_meta = get_voice(voice_id)
        if not voice_meta:
            raise HTTPException(status_code=404, detail=f"Voice '{voice_id}' not found")
        
        model_path = voice_meta.get("model_path")
        if not model_path:
            raise HTTPException(status_code=500, detail=f"No model_path for voice '{voice_id}'")
        
        # Load voice with caching
        voice_manager = get_voice_manager()
        voice = voice_manager.get_voice(model_path)
        
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
        
        # Generate unique audio_id
        audio_id = str(uuid.uuid4())
        today_date = datetime.utcnow().strftime('%Y-%m-%d')
        
        # Upload to S3 and get signed URL
        s3_url, s3_key = upload_to_s3(wav_bytes, audio_id, today_date)
        
        # Save metadata to DynamoDB
        dynamodb = boto3.resource(
            'dynamodb',
            region_name=settings.AWS_REGION
        )
        temp_audio_table = dynamodb.Table(settings.DYNAMODB_TABLE_TEMP_AUDIO)
        save_to_dynamodb(
            temp_audio_table,
            date=today_date,
            audio_id=audio_id,
            s3_url=s3_url,
            text=text,
            voice_id=voice_id,
            duration=duration
        )
        
        # Return JSON response with S3 URL and metadata
        return JSONResponse({
            "audio_id": audio_id,
            "s3_url": s3_url,
            "duration": duration,
            "text": text,
            "voice_id": voice_id,
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


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

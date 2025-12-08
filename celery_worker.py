from celery import Celery
import os
import subprocess
import shutil
import wave
import contextlib
import traceback
import logging
from datetime import datetime
from celery.schedules import crontab
from app.dynamo import get_job_item, update_job_item
from app.voice_catalog import get_voice
from app.config import settings
from app.utils.chunker import chunk_text
from app.voice_manager import get_voice_manager
from typing import List
import io
from app.utils.s3_utils import upload_audio
from app.utils.dynamo_utils import update_job_s3


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery("backend_tasks", broker=REDIS_URL, backend=REDIS_URL)

# Configure Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-temp-audio': {
        'task': 'app.workers.cleanup.cleanup_yesterday_temp_audio',
        'schedule': crontab(hour=12, minute=0),  # Run at 12:00 PM UTC daily
        'options': {'queue': 'default'}
    },
}


def _ensure_dirs(job_id: int):
    # Use current working directory as base so running the worker from
    # the `backend` folder doesn't create a nested backend/backend path.
    base = os.getcwd()
    tmp = os.path.join(base, "tmp_chunks", str(job_id))
    out = os.path.join(base, "output")
    os.makedirs(tmp, exist_ok=True)
    os.makedirs(out, exist_ok=True)
    return tmp, out


def _merge_wavs(wav_paths: List[str], out_path: str) -> None:
    """Merge WAV files using ffmpeg concat demuxer."""
    # create a temporary list file
    list_file = out_path + ".txt"
    with open(list_file, "w", encoding="utf8") as fh:
        for p in wav_paths:
            fh.write(f"file '{p}'\n")
    # locate ffmpeg binary (allow override via FFMPEG_PATH env var)
    ffmpeg_override = os.getenv("FFMPEG_PATH")
    if ffmpeg_override and os.path.isfile(ffmpeg_override):
        ffmpeg_bin = ffmpeg_override
    else:
        ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin:
        # run ffmpeg
        cmd = [
            ffmpeg_bin,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_file,
            "-c",
            "copy",
            out_path,
        ]
        subprocess.check_call(cmd)
        try:
            os.remove(list_file)
        except Exception:
            pass
        return

    # fallback: if ffmpeg is not available, try a pure-Python WAV concat
    try:
        if os.path.exists(list_file):
            try:
                os.remove(list_file)
            except Exception:
                pass
        # Ensure there is at least one wav
        if not wav_paths:
            raise ValueError("No wav files to merge")

        # Read params from first file and ensure all files match
        with contextlib.ExitStack() as stack:
            readers = [stack.enter_context(wave.open(p, "rb")) for p in wav_paths]
            params = readers[0].getparams()
            frames = []
            for r in readers:
                if r.getparams()[:4] != params[:4]:
                    # (nchannels, sampwidth, framerate, comptype) must match
                    raise ValueError("WAV files have different audio parameters and cannot be concatenated without ffmpeg.")
                frames.append(r.readframes(r.getnframes()))

        # write output
        with wave.open(out_path, "wb") as out_f:
            out_f.setparams(params)
            for f in frames:
                out_f.writeframes(f)
        return
    except Exception as e:
        # If fallback fails, raise a clear error similar to before
        raise FileNotFoundError(
            "ffmpeg not found on PATH and Python WAV fallback failed: " + str(e) + ". Install ffmpeg or set FFMPEG_PATH to its executable."
        )


@celery_app.task(name="backend.process_job")
def process_job(job_id: int):
    """Process a queued job: chunk text, call Piper per chunk, save chunk wavs,
    merge them, and update DB status.
    """
    logger = logging.getLogger("celery_worker")
    logger.info(f"process_job called for job_id={job_id}")
    try:
        job = get_job_item(job_id)
        if not job:
            return {"job_id": job_id, "status": "not_found"}

        # set processing
        update_job_item(job_id, {"status": "processing", "updated_at": datetime.utcnow().isoformat()})

        text = job.get("text", "") or ""
        if not text:
            update_job_item(job_id, {"status": "failed", "updated_at": datetime.utcnow().isoformat()})
            return {"job_id": job_id, "status": "no_text"}

        tmp_dir, out_dir = _ensure_dirs(job_id)

        chunks = chunk_text(text, max_chars=500)
        # Preserve voice/model information from the job so the worker
        # forwards the intended voice or model to Piper for each chunk.
        voice_id = job.get("voice_id")
        model_path = None
        if voice_id:
            try:
                v = get_voice(voice_id)
                if v and v.get("model_path"):
                    model_path = v.get("model_path")
            except Exception:
                model_path = None

        # Record total chunks for progress tracking
        try:
            update_job_item(job_id, {"total_chunks": len(chunks)})
        except Exception:
            pass
        wav_paths: List[str] = []

        # Get voice manager for dynamic model loading
        voice_manager = get_voice_manager()

        # Log which model will be used (or None)
        if model_path:
            logger.info(f"Loading voice model: {model_path}")
        else:
            logger.info("No explicit model_path provided for this job; cannot synthesize.")
            update_job_item(job_id, {"status": "failed", "updated_at": datetime.utcnow().isoformat()})
            return {"job_id": job_id, "status": "no_model"}

        # Load voice once (cached for subsequent chunks)
        voice = voice_manager.get_voice(model_path)
        if not voice:
            logger.error(f"Failed to load voice model: {model_path}")
            update_job_item(job_id, {"status": "failed", "updated_at": datetime.utcnow().isoformat()})
            return {"job_id": job_id, "status": "voice_load_failed"}

        logger.info(f"Voice loaded successfully. Processing {len(chunks)} chunks...")

        # Process each chunk using Piper Python API
        for idx, chunk in enumerate(chunks):
            try:
                logger.info(f"Synthesizing chunk {idx+1}/{len(chunks)} (length: {len(chunk)} chars)")
                
                # Save chunk WAV file directly
                wav_path = os.path.join(tmp_dir, f"chunk_{idx}.wav")
                
                # Synthesize using Piper Python API - voice.synthesize() yields AudioChunk objects
                # We collect them and write to a WAV file manually
                audio_chunks = []
                sample_rate = None
                sample_width = None
                sample_channels = None
                
                for audio_chunk in voice.synthesize(chunk):
                    if sample_rate is None:
                        sample_rate = audio_chunk.sample_rate
                        sample_width = audio_chunk.sample_width
                        sample_channels = audio_chunk.sample_channels
                    audio_chunks.append(audio_chunk.audio_int16_bytes)
                
                # Write collected audio to WAV file
                with wave.open(wav_path, "wb") as wav_file:
                    wav_file.setnchannels(sample_channels)
                    wav_file.setsampwidth(sample_width)
                    wav_file.setframerate(sample_rate)
                    for audio_bytes in audio_chunks:
                        wav_file.writeframes(audio_bytes)
                
                wav_paths.append(wav_path)
                logger.debug(f"Chunk {idx+1} saved: {wav_path} ({os.path.getsize(wav_path)} bytes)")
                
            except Exception as chunk_error:
                logger.error(f"Failed to synthesize chunk {idx+1}: {chunk_error}", exc_info=True)
                # Continue with next chunk instead of failing entire job
                continue

        if not wav_paths:
            update_job_item(job_id, {"status": "failed", "updated_at": datetime.utcnow().isoformat()})
            return {"job_id": job_id, "status": "no_audio"}

        out_path = os.path.join(out_dir, f"job_{job_id}.wav")
        _merge_wavs(wav_paths, out_path)

        # update job record (local DB / cache)
        update_job_item(job_id, {
            "s3_final_url": out_path,
            "status": "completed",
            "completed_chunks": len(wav_paths),
            "updated_at": datetime.utcnow().isoformat(),
        })

        # Upload final audio to S3 and update DynamoDB record
        try:
            user_id = job.get("user_id") or job.get("owner") or "unknown"
            s3_key, s3_url = upload_audio(out_path, str(user_id), str(job_id))
            # update the DynamoDB record with S3 metadata
            try:
                update_job_s3(job_id, s3_key, s3_url)
            except Exception:
                logger.exception("Failed to update DynamoDB with S3 info")
            # also update local DB with S3 info for parity
            try:
                update_job_item(job_id, {"audio_s3_key": s3_key, "audio_s3_url": s3_url})
            except Exception:
                logger.exception("Failed to update local DB with S3 info")
        except Exception:
            logger.exception("Failed to upload audio to S3")

        # cleanup tmp
        try:
            shutil.rmtree(tmp_dir)
        except Exception:
            pass

        return {"job_id": job_id, "status": "completed", "output": out_path}
    except Exception as exc:
        # write full traceback to a log file to aid debugging
        tb = traceback.format_exc()
        try:
            logs_dir = os.path.join(os.getcwd(), "backend", "logs")
            os.makedirs(logs_dir, exist_ok=True)
            log_path = os.path.join(logs_dir, f"worker_job_{job_id}.log")
            with open(log_path, "a", encoding="utf8") as lf:
                lf.write(f"[{datetime.utcnow().isoformat()}] Exception while processing job {job_id}\n")
                lf.write(tb + "\n")
        except Exception:
            logger.exception("Failed to write worker log file")

        try:
            job = get_job_item(job_id)
            if job:
                update_job_item(job_id, {"status": "failed", "updated_at": datetime.utcnow().isoformat()})
        except Exception:
            logger.exception("Failed to update job status on exception")

        logger.exception("process_job raised an exception")
        return {"job_id": job_id, "status": "error", "error": str(exc)}
    finally:
        pass

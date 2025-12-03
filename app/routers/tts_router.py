from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import Response, JSONResponse
from .. import schemas
from ..dynamo import create_job_item, get_job_item
from ..voice_catalog import get_voice
import httpx
from ..config import settings
from ..auth import get_current_user

router = APIRouter(prefix="/tts", tags=["tts"])


@router.post("/sync")
async def tts_sync(request: Request):
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

    content_type = resp.headers.get("content-type", "audio/wav")
    return Response(content=resp.content, media_type=content_type)


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
        "audio_url": job.get("s3_final_url")
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

    # Return job info including audio_url (populated by worker as s3_final_url)
    return {
        "id": int(job["id"]),
        "status": job.get("status", "unknown"),
        "created_at": job.get("created_at"),
        "audio_url": job.get("s3_final_url")
    }

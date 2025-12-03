from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, JSONResponse
from .config import settings
from .api import router as api_router
from .routers import auth_router, voices_router, tts_router
from .db import Base, engine
# Use a hard-coded voice catalog for dev; do not auto-sync Piper models.
from .voice_catalog import list_voices as _list_voices  # imported to ensure module available


app = FastAPI(title="TTS App - Backend")
app.include_router(api_router)
app.include_router(auth_router.router)
app.include_router(auth_router.public_router)
app.include_router(voices_router.router)
app.include_router(tts_router.router)


@app.on_event("startup")
def startup_event():
    # create DB tables for dev (SQLite)
    Base.metadata.create_all(bind=engine)
    # Do NOT seed or sync Piper models/voices during startup for this mode.
    # Voices are provided by the hard-coded `voice_catalog` module.


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/config")
async def get_config():
    # expose limited config for debugging
    return {"PIPER_URL": str(settings.PIPER_URL)}

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, JSONResponse
from .config import settings
from .api import router as api_router
from .routers import voices_router, tts_router
# Import new email-based auth router
from .routers import auth_router_email
# Old Cognito auth router (keep for backward compatibility during migration)
# from .routers import auth_router
from .db import Base, engine
# Use a hard-coded voice catalog for dev; do not auto-sync Piper models.
from .voice_catalog import list_voices as _list_voices  # imported to ensure module available
# Import MongoDB initialization
from .mongodb import init_mongodb, close_mongodb_connections
import logging

logger = logging.getLogger(__name__)


app = FastAPI(title="TTS App - Backend")
app.include_router(api_router)

# New email-based authentication
app.include_router(auth_router_email.router)
app.include_router(auth_router_email.public_router)

# Old Cognito auth (uncomment if you want to run both in parallel)
# app.include_router(auth_router.router, prefix="/auth-cognito")
# app.include_router(auth_router.public_router)

app.include_router(voices_router.router)
app.include_router(tts_router.router)


@app.on_event("startup")
def startup_event():
    # create DB tables for dev (SQLite)
    Base.metadata.create_all(bind=engine)
    
    # Initialize MongoDB connection and indexes
    try:
        init_mongodb()
        logger.info("MongoDB initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}")
        # Continue startup even if MongoDB fails (will retry on first use)
    
    # Do NOT seed or sync Piper models/voices during startup for this mode.
    # Voices are provided by the hard-coded `voice_catalog` module.


@app.on_event("shutdown")
def shutdown_event():
    # Close MongoDB connections
    close_mongodb_connections()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/config")
async def get_config():
    # expose limited config for debugging
    return {"PIPER_URL": str(settings.PIPER_URL)}


from fastapi import APIRouter
from ..voice_catalog import list_voices

router = APIRouter(prefix="/voices", tags=["voices"])


@router.get("/")
async def list_voices_endpoint():
    return list_voices()

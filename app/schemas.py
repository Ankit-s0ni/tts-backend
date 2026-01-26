from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class VoiceOut(BaseModel):
    id: str
    engine: str
    language: str
    display_name: Optional[str]


class JobCreate(BaseModel):
    text: str
    language: Optional[str] = "en_US"
    voice_id: Optional[str] = None
    include_alignments: Optional[bool] = False


class JobOut(BaseModel):
    id: str  # Changed to str to support UUID job IDs
    status: str
    created_at: str  # Changed to str for ISO format datetime
    audio_url: str | None = None

    class Config:
        orm_mode = True


from typing import Optional


class UserProfileUpdate(BaseModel):
    full_name: Optional[str]
    phone: Optional[str]
    age: Optional[int]
    profile_image: Optional[str]


class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    age: Optional[int]
    profile_image: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]

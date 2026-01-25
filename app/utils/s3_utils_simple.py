"""Simple file storage utilities.

This module provides simple file storage without external dependencies.
Replaces S3/Cloudinary functionality for development.
"""
import os
import uuid
from pathlib import Path
from typing import Optional


# Simple local file storage directory
STORAGE_DIR = Path("/tmp/tts_audio_files")
STORAGE_DIR.mkdir(exist_ok=True)


def upload_audio(audio_data: bytes, filename: str = None) -> str:
    """Save audio file locally and return a local URL."""
    if filename is None:
        filename = f"{uuid.uuid4()}.wav"
    
    # Ensure the filename has proper extension
    if not filename.endswith(('.wav', '.mp3', '.ogg')):
        filename += '.wav'
    
    file_path = STORAGE_DIR / filename
    
    # Write the audio data to file
    with open(file_path, 'wb') as f:
        f.write(audio_data)
    
    # Return a local URL
    return f"file://{file_path.absolute()}"


def generate_presigned_url(file_key: str) -> str:
    """Generate a simple file:// URL for local files."""
    if file_key.startswith("file://"):
        return file_key
    
    # If it's just a filename, construct the full path
    file_path = STORAGE_DIR / file_key
    if file_path.exists():
        return f"file://{file_path.absolute()}"
    
    # Return the original if it doesn't exist locally
    return file_key


def save_audio_file(audio_content: bytes, filename: str = None) -> str:
    """Save audio file and return the URL (alias for upload_audio)."""
    return upload_audio(audio_content, filename)


def get_file_url(filename: str) -> str:
    """Get URL for a stored file (alias for generate_presigned_url)."""
    return generate_presigned_url(filename)
"""
Cloudinary uploader utility to replace S3 uploads.
Uploads audio files to Cloudinary and returns URLs.
"""
import os
import uuid
from typing import Tuple
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

# Configure Cloudinary from environment variables
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)


def upload_audio(local_path: str, user_id: str, job_id: str) -> Tuple[str, str]:
    """
    Upload a WAV file to Cloudinary and return (cloudinary_public_id, public_url).
    
    Args:
        local_path: Path to the local audio file
        user_id: User ID for organizing uploads
        job_id: Job ID for organizing uploads
    
    Returns:
        Tuple of (public_id, secure_url)
    """
    if not all([os.getenv("CLOUDINARY_CLOUD_NAME"), 
                os.getenv("CLOUDINARY_API_KEY"), 
                os.getenv("CLOUDINARY_API_SECRET")]):
        raise ValueError("Cloudinary credentials not configured in environment")
    
    # Create a structured folder path in Cloudinary
    user_part = str(user_id or "unknown").strip()
    job_part = str(job_id or "")
    
    # Generate unique identifier
    unique_id = str(uuid.uuid4())
    
    # Cloudinary folder structure: tts/user_id/job_id/unique_id
    folder = f"tts/{user_part}/{job_part}"
    public_id = f"{folder}/{unique_id}"
    
    try:
        # Upload the file to Cloudinary
        # resource_type="video" is used for audio files in Cloudinary
        result = cloudinary.uploader.upload(
            local_path,
            resource_type="video",  # audio files use "video" resource type
            public_id=public_id,
            format="wav",
            overwrite=False
        )
        
        # Return the public_id and secure URL
        return result["public_id"], result["secure_url"]
        
    except Exception as e:
        print(f"Error uploading to Cloudinary: {e}")
        raise


def upload_file_placeholder(local_path: str, key: str) -> str:
    """
    Placeholder uploader compatible with old S3 interface.
    Uploads to Cloudinary and returns the URL.
    
    Args:
        local_path: Path to the local file
        key: Key/path for the file (used as public_id in Cloudinary)
    
    Returns:
        URL to the uploaded file
    """
    if not all([os.getenv("CLOUDINARY_CLOUD_NAME"), 
                os.getenv("CLOUDINARY_API_KEY"), 
                os.getenv("CLOUDINARY_API_SECRET")]):
        # Fallback to local path if Cloudinary not configured
        return f"file://{os.path.abspath(local_path)}"
    
    try:
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            local_path,
            resource_type="auto",  # auto-detect resource type
            public_id=key.replace("/", "_"),  # Cloudinary uses underscores
            overwrite=False
        )
        
        return result["secure_url"]
        
    except Exception as e:
        print(f"Error uploading to Cloudinary: {e}")
        # Fallback to local path on error
        return f"file://{os.path.abspath(local_path)}"


def generate_presigned_url(cloudinary_public_id: str, expiration: int = 3600) -> str:
    """
    Generate a URL for a Cloudinary resource.
    Note: Cloudinary URLs are public by default, but you can add transformations.
    
    Args:
        cloudinary_public_id: The Cloudinary public ID
        expiration: Not used (Cloudinary URLs don't expire by default)
    
    Returns:
        URL to the Cloudinary resource
    """
    url, _ = cloudinary_url(
        cloudinary_public_id,
        resource_type="video",  # audio files use "video" resource type
        secure=True
    )
    return url


def delete_file(cloudinary_public_id: str) -> bool:
    """
    Delete a file from Cloudinary.
    
    Args:
        cloudinary_public_id: The public ID of the file to delete
    
    Returns:
        True if successful, False otherwise
    """
    try:
        result = cloudinary.uploader.destroy(
            cloudinary_public_id,
            resource_type="video"
        )
        return result.get("result") == "ok"
    except Exception as e:
        print(f"Error deleting from Cloudinary: {e}")
        return False

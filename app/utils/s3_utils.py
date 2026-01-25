
"""
S3 utilities module - now uses Cloudinary instead of S3.
This module is kept for backward compatibility with existing code.
"""
# Import from cloudinary_uploader for backward compatibility
from .cloudinary_uploader import (
    upload_audio,
    generate_presigned_url
)

__all__ = ['upload_audio', 'generate_presigned_url']

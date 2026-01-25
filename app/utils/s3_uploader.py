"""
S3 uploader module - now uses Cloudinary instead of S3.
This module is kept for backward compatibility.
"""
# Import from cloudinary_uploader for backward compatibility
from .cloudinary_uploader import (
    upload_file_placeholder,
    upload_audio,
    generate_presigned_url
)

__all__ = ['upload_file_placeholder', 'upload_audio', 'generate_presigned_url']

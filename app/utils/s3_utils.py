
import os
import uuid
from typing import Tuple
import boto3

def _get_s3_client():
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_REGION")

    # Credentials must be provided via environment in production/dev.
    # Do not attempt to read local files here; rely on env vars.

    session_kwargs = {}
    client_kwargs = {}
    if aws_key and aws_secret:
        session_kwargs["aws_access_key_id"] = aws_key
        session_kwargs["aws_secret_access_key"] = aws_secret
    if region:
        session_kwargs["region_name"] = region
        client_kwargs["region_name"] = region

    session = boto3.session.Session(**session_kwargs)
    return session.client("s3", **client_kwargs)


def upload_audio(local_path: str, user_id: str, job_id: str) -> Tuple[str, str]:
    """Upload a WAV file to S3 and return (s3_key, public_url).

    The S3 key format is: tts/{user_id}/{job_id}/{uuid4()}.wav
    """
    bucket = os.getenv("AWS_S3_BUCKET")
    if not bucket:
        raise ValueError("AWS_S3_BUCKET environment variable is not set")

    s3 = _get_s3_client()

    # sanitize inputs
    user_part = str(user_id or "unknown").strip()
    job_part = str(job_id or "")
    key = f"tts/{user_part}/{job_part}/{uuid.uuid4()}.wav"

    extra_args = {"ContentType": "audio/wav"}
    # Optionally make objects public if explicitly requested
    if os.getenv("AWS_S3_PUBLIC", "").lower() in ("1", "true", "yes"):
        extra_args["ACL"] = "public-read"

    s3.upload_file(local_path, bucket, key, ExtraArgs=extra_args)

    region = os.getenv("AWS_REGION") or getattr(s3, 'meta', None) and getattr(s3.meta, 'region_name', None) or ""
    # Construct a standard S3 URL (may be private if ACL not set)
    if region and region != "us-east-1":
        public_url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
    else:
        public_url = f"https://{bucket}.s3.amazonaws.com/{key}"

    return key, public_url

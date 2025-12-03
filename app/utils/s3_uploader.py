import os

def upload_file_placeholder(local_path: str, key: str) -> str:
    """Placeholder uploader. If S3 env vars are configured, upload; otherwise return a local path.

    Returns a URL or path to the uploaded object.
    """
    s3_endpoint = os.getenv("S3_ENDPOINT", "")
    s3_bucket = os.getenv("S3_BUCKET", "")
    if s3_endpoint and s3_bucket:
        # TODO: implement real upload (boto3 or minio)
        # return presigned URL after upload
        return f"{s3_endpoint}/{s3_bucket}/{key}"
    # fallback to local path
    return f"file://{os.path.abspath(local_path)}"

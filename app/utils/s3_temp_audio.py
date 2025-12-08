import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

# S3 Config
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "")
S3_CLIENT = boto3.client("s3", region_name=AWS_REGION)


def upload_to_s3(audio_bytes: bytes, audio_id: str, date: str) -> tuple[str, str]:
    """
    Upload WAV file to S3 and return signed URL
    
    Args:
        audio_bytes: WAV file bytes
        audio_id: UUID of audio
        date: Date in format YYYY-MM-DD
    
    Returns:
        tuple: (signed_url, s3_key)
    """
    s3_key = f"temp-audio/{date}/{audio_id}.wav"
    
    try:
        S3_CLIENT.put_object(
            Bucket=AWS_S3_BUCKET,
            Key=s3_key,
            Body=audio_bytes,
            ContentType="audio/wav"
        )
        
        # Generate signed URL (24 hour expiry)
        signed_url = S3_CLIENT.generate_presigned_url(
            'get_object',
            Params={'Bucket': AWS_S3_BUCKET, 'Key': s3_key},
            ExpiresIn=86400  # 24 hours
        )
        
        return signed_url, s3_key
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        raise


def save_to_dynamodb(
    dynamodb_table,
    date: str,
    audio_id: str,
    s3_url: str,
    text: str,
    voice_id: str,
    duration: float
) -> None:
    """
    Save audio metadata to DynamoDB
    
    Args:
        dynamodb_table: DynamoDB table resource
        date: Date in format YYYY-MM-DD
        audio_id: UUID of audio
        s3_url: Signed S3 URL
        text: Text that was converted
        voice_id: Voice model used
        duration: Audio duration in seconds
    """
    # TTL = 24 hours from now
    ttl = int((datetime.utcnow() + timedelta(days=1)).timestamp())
    
    try:
        dynamodb_table.put_item(
            Item={
                'date': date,
                'audio_id': audio_id,
                's3_url': s3_url,
                'text': text,
                'voice_id': voice_id,
                'duration': Decimal(str(duration)),  # Convert float to Decimal
                'ttl': ttl
            }
        )
    except Exception as e:
        print(f"Error saving to DynamoDB: {e}")
        raise


def cleanup_yesterday_s3(yesterday_date: str) -> int:
    """
    Delete all audio files from yesterday's S3 folder
    
    Args:
        yesterday_date: Date in format YYYY-MM-DD
    
    Returns:
        int: Number of files deleted
    """
    prefix = f"temp-audio/{yesterday_date}/"
    deleted_count = 0
    
    try:
        # List all files with the prefix
        response = S3_CLIENT.list_objects_v2(
            Bucket=AWS_S3_BUCKET,
            Prefix=prefix
        )
        
        # Delete each file
        if 'Contents' in response:
            for obj in response['Contents']:
                S3_CLIENT.delete_object(
                    Bucket=AWS_S3_BUCKET,
                    Key=obj['Key']
                )
                deleted_count += 1
        
        print(f"Deleted {deleted_count} files from S3 for {yesterday_date}")
        return deleted_count
    except Exception as e:
        print(f"Error cleaning up S3: {e}")
        raise

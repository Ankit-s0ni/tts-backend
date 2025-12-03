import os
from datetime import datetime
import boto3


def _get_dynamodb_table(table_name: str):
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_REGION")

    resource_kwargs = {}
    if aws_key and aws_secret:
        resource_kwargs["aws_access_key_id"] = aws_key
        resource_kwargs["aws_secret_access_key"] = aws_secret
    if region:
        resource_kwargs["region_name"] = region

    dynamodb = boto3.resource("dynamodb", **resource_kwargs)
    return dynamodb.Table(table_name)


def update_job_s3(job_id: str, s3_key: str, s3_url: str):
    """Update the `tts_jobs` DynamoDB table for the given job_id with S3 info.

    Sets `audio_s3_key`, `audio_s3_url`, `status`='completed', and `completed_at` timestamp.
    """
    table_name = os.getenv("DYNAMODB_TABLE_NAME", "tts_jobs")
    table = _get_dynamodb_table(table_name)

    now = datetime.utcnow().isoformat()

    # job_id may be numeric or string in Dynamo; we'll send as string
    key = {"job_id": str(job_id)}

    update_expr = "SET audio_s3_key = :k, audio_s3_url = :u, #s = :st, completed_at = :c"
    expr_attr_vals = {
        ":k": s3_key,
        ":u": s3_url,
        ":st": "completed",
        ":c": now,
    }
    expr_attr_names = {"#s": "status"}

    table.update_item(
        Key=key,
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_attr_vals,
        ExpressionAttributeNames=expr_attr_names,
    )

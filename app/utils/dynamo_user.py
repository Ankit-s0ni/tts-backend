import os
from datetime import datetime
from typing import Optional, Dict
import boto3


def _get_table():
    table_name = os.getenv("DYNAMODB_TABLE_USERS", "users")
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


def get_user(user_id: str) -> Optional[Dict]:
    table = _get_table()
    resp = table.get_item(Key={"user_id": str(user_id)})
    return resp.get("Item")


def create_or_update_user(user_id: str, email: str, data: dict) -> Dict:
    """Create or update a user record in DynamoDB.

    Fields updated: full_name, phone, age, profile_image, updated_at
    Ensures created_at is set on first create.
    Returns the new/updated item.
    """
    table = _get_table()
    now = datetime.utcnow().isoformat()

    # Build update expression dynamically
    update_parts = ["updated_at = :updated_at", "email = :email"]
    expr_vals = {":updated_at": now, ":email": email}

    if data is None:
        data = {}

    if "full_name" in data and data["full_name"] is not None:
        update_parts.append("full_name = :full_name")
        expr_vals[":full_name"] = data["full_name"]
    if "phone" in data and data["phone"] is not None:
        update_parts.append("phone = :phone")
        expr_vals[":phone"] = data["phone"]
    if "age" in data and data["age"] is not None:
        update_parts.append("age = :age")
        expr_vals[":age"] = int(data["age"])
    if "profile_image" in data and data["profile_image"] is not None:
        update_parts.append("profile_image = :profile_image")
        expr_vals[":profile_image"] = data["profile_image"]

    update_expr = "SET " + ", ".join(update_parts) + ", created_at = if_not_exists(created_at, :created_at)"
    expr_vals[":created_at"] = now

    resp = table.update_item(
        Key={"user_id": str(user_id)},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_vals,
        ReturnValues="ALL_NEW",
    )
    return resp.get("Attributes", {})

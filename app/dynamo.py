import os
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from datetime import datetime
from decimal import Decimal

REGION = os.getenv("DYNAMODB_REGION") or os.getenv("AWS_REGION", "ap-south-1")
AUTOCREATE = os.getenv("DYNAMODB_AUTOCREATE", "true").lower() in ("1", "true", "yes")


def _get_resource():
    kwargs = {"region_name": REGION}
    endpoint = os.getenv("DYNAMODB_ENDPOINT_URL")
    if endpoint:
        kwargs["endpoint_url"] = endpoint
        # When talking to a local DynamoDB endpoint, boto3 still attempts
        # to sign requests. Provide dummy credentials if none are set so
        # local testing works without AWS creds.
        kwargs["aws_access_key_id"] = os.getenv("AWS_ACCESS_KEY_ID", "fake")
        kwargs["aws_secret_access_key"] = os.getenv("AWS_SECRET_ACCESS_KEY", "fake")
    return boto3.resource("dynamodb", **kwargs)


def _ensure_tables():
    """Create basic tables if AUTOCREATE is enabled. This is safe to call repeatedly."""
    if not AUTOCREATE:
        return
    dynamo = _get_resource()
    # When using a local DynamoDB endpoint, listing tables can trigger
    # signing behavior that fails if credentials are not present. To
    # keep local dev simple, just attempt to create the tables and
    # ignore already-existing errors. For real AWS environments we
    # still try to be efficient by checking existing table list.
    try:
        if os.getenv("DYNAMODB_ENDPOINT_URL"):
            # don't call dynamo.tables.all() against local endpoint
            # — just attempt creation and ignore ResourceInUseException
            try:
                dynamo.create_table(
                    TableName="counters",
                    KeySchema=[{"AttributeName": "name", "KeyType": "HASH"}],
                    AttributeDefinitions=[{"AttributeName": "name", "AttributeType": "S"}],
                    BillingMode="PAY_PER_REQUEST",
                )
            except ClientError:
                pass
            try:
                dynamo.create_table(
                    TableName="jobs",
                    KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
                    AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "N"}],
                    BillingMode="PAY_PER_REQUEST",
                )
            except ClientError:
                pass
            try:
                dynamo.create_table(
                    TableName="voices",
                    KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
                    AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
                    BillingMode="PAY_PER_REQUEST",
                )
            except ClientError:
                pass
            try:
                dynamo.create_table(
                    TableName="chunks",
                    KeySchema=[
                        {"AttributeName": "job_id", "KeyType": "HASH"},
                        {"AttributeName": "idx", "KeyType": "RANGE"},
                    ],
                    AttributeDefinitions=[
                        {"AttributeName": "job_id", "AttributeType": "N"},
                        {"AttributeName": "idx", "AttributeType": "N"},
                    ],
                    BillingMode="PAY_PER_REQUEST",
                )
            except ClientError:
                pass
            try:
                dynamo.create_table(
                    TableName="tts_temp_audio",
                    KeySchema=[
                        {"AttributeName": "date", "KeyType": "HASH"},
                        {"AttributeName": "audio_id", "KeyType": "RANGE"},
                    ],
                    AttributeDefinitions=[
                        {"AttributeName": "date", "AttributeType": "S"},
                        {"AttributeName": "audio_id", "AttributeType": "S"},
                    ],
                    BillingMode="PAY_PER_REQUEST",
                    TimeToLiveSpecification={
                        "Enabled": True,
                        "AttributeName": "ttl"
                    }
                )
            except ClientError:
                pass
        else:
            try:
                existing = {t.name for t in dynamo.tables.all()}
            except Exception:
                # If listing tables fails (e.g. signing/credential issues),
                # fall back to attempting creation below.
                existing = set()
            if "counters" not in existing:
                dynamo.create_table(
                    TableName="counters",
                    KeySchema=[{"AttributeName": "name", "KeyType": "HASH"}],
                    AttributeDefinitions=[{"AttributeName": "name", "AttributeType": "S"}],
                    BillingMode="PAY_PER_REQUEST",
                )
            if "jobs" not in existing:
                dynamo.create_table(
                    TableName="jobs",
                    KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
                    AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "N"}],
                    BillingMode="PAY_PER_REQUEST",
                )
            if "voices" not in existing:
                dynamo.create_table(
                    TableName="voices",
                    KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
                    AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
                    BillingMode="PAY_PER_REQUEST",
                )
            if "chunks" not in existing:
                dynamo.create_table(
                    TableName="chunks",
                    KeySchema=[
                        {"AttributeName": "job_id", "KeyType": "HASH"},
                        {"AttributeName": "idx", "KeyType": "RANGE"},
                    ],
                    AttributeDefinitions=[
                        {"AttributeName": "job_id", "AttributeType": "N"},
                        {"AttributeName": "idx", "AttributeType": "N"},
                    ],
                    BillingMode="PAY_PER_REQUEST",
                )
            if "tts_temp_audio" not in existing:
                dynamo.create_table(
                    TableName="tts_temp_audio",
                    KeySchema=[
                        {"AttributeName": "date", "KeyType": "HASH"},
                        {"AttributeName": "audio_id", "KeyType": "RANGE"},
                    ],
                    AttributeDefinitions=[
                        {"AttributeName": "date", "AttributeType": "S"},
                        {"AttributeName": "audio_id", "AttributeType": "S"},
                    ],
                    BillingMode="PAY_PER_REQUEST",
                    TimeToLiveSpecification={
                        "Enabled": True,
                        "AttributeName": "ttl"
                    }
                )
    except ClientError:
        # if tables already being created concurrently, ignore
        pass


def _get_table(name: str):
    dynamo = _get_resource()
    table = dynamo.Table(name)
    return table


def _next_id(counter_name: str) -> int:
    """Atomically increments and returns next numeric id for counter_name."""
    _ensure_tables()
    table = _get_table("counters")
    resp = table.update_item(
        Key={"name": counter_name},
        UpdateExpression="ADD #v :inc",
        ExpressionAttributeNames={"#v": "value"},
        ExpressionAttributeValues={":inc": Decimal(1)},
        ReturnValues="UPDATED_NEW",
    )
    return int(resp["Attributes"]["value"]) if "Attributes" in resp else 1


def create_job_item(user_id: int | str | None, job_in: dict) -> dict:
    _ensure_tables()
    table = _get_table("jobs")
    job_id = _next_id("jobs")
    now = datetime.utcnow().isoformat()
    item = {
        "id": job_id,
        "user_id": user_id or None,
        "text": job_in.get("text", ""),
        "voice_id": job_in.get("voice_id") or "en_US-lessac-medium",
        "language": job_in.get("language", "en_US"),
        "include_alignments": bool(job_in.get("include_alignments", False)),
        "status": "queued",
        "created_at": now,
        "updated_at": now,
        "completed_chunks": 0,
        "total_chunks": 0,
    }
    table.put_item(Item=item)
    return item


def get_job_item(job_id: int) -> dict | None:
    _ensure_tables()
    table = _get_table("jobs")
    resp = table.get_item(Key={"id": int(job_id)})
    return resp.get("Item")


def update_job_item(job_id: int, updates: dict) -> dict:
    _ensure_tables()
    table = _get_table("jobs")
    # Build UpdateExpression
    expr_parts = []
    names = {}
    values = {}
    for i, (k, v) in enumerate(updates.items()):
        placeholder_name = f"#k{i}"
        placeholder_val = f":v{i}"
        expr_parts.append(f"{placeholder_name} = {placeholder_val}")
        names[placeholder_name] = k
        # convert bool to native bool, numbers to Decimal
        if isinstance(v, (int, float)):
            values[placeholder_val] = Decimal(str(v))
        else:
            values[placeholder_val] = v

    if not expr_parts:
        return get_job_item(job_id)

    update_expr = "SET " + ", ".join(expr_parts)
    resp = table.update_item(
        Key={"id": int(job_id)},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
        ReturnValues="ALL_NEW",
    )
    return resp.get("Attributes", {})


def get_user_jobs(user_id: str | int, limit: int = 50) -> list:
    """Get all jobs for a specific user, sorted by creation date (newest first)."""
    _ensure_tables()
    table = _get_table("jobs")
    try:
        from boto3.dynamodb.conditions import Attr
        
        # Scan with filter for user_id
        resp = table.scan(
            FilterExpression=Attr("user_id").eq(str(user_id)),
            Limit=limit
        )
        items = resp.get("Items", [])
        
        # Sort by created_at descending (newest first)
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return items
    except Exception as e:
        print(f"Error getting user jobs: {e}")
        return []


def list_voices() -> list:
    _ensure_tables()
    table = _get_table("voices")
    resp = table.scan()
    return resp.get("Items", [])


def list_available_voices() -> list:
    """Return voices where available == True. Falls back to returning all voices
    if filtering is not supported by the environment."""
    _ensure_tables()
    table = _get_table("voices")
    try:
        from boto3.dynamodb.conditions import Attr

        resp = table.scan(FilterExpression=Attr("available").eq(True))
        return resp.get("Items", [])
    except Exception:
        # If scan with filter fails for any reason, return all and let caller filter
        allv = table.scan().get("Items", [])
        return [v for v in allv if v.get("available")]


def get_voice(voice_id: str) -> dict | None:
    _ensure_tables()
    table = _get_table("voices")
    resp = table.get_item(Key={"id": voice_id})
    return resp.get("Item")


def put_voice(voice: dict) -> dict:
    _ensure_tables()
    table = _get_table("voices")
    table.put_item(Item=voice)
    return voice

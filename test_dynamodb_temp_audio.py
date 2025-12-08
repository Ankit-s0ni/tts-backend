import boto3
from datetime import datetime

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("tts_temp_audio")

today = datetime.utcnow().strftime("%Y-%m-%d")

response = table.query(
    KeyConditionExpression="#date = :date",
    ExpressionAttributeNames={"#date": "date"},
    ExpressionAttributeValues={":date": today}
)

items = response.get("Items", [])
print(f"\n✓ Records found for {today}: {len(items)}\n")
for item in items:
    text_preview = item["text"][:40] if len(item["text"]) > 40 else item["text"]
    print(f"Audio ID: {item['audio_id']}")
    print(f"Duration: {item['duration']}s")
    print(f"Voice: {item['voice_id']}")
    print(f"Text: {text_preview}...")
    print(f"S3 Key: temp-audio/{today}/{item['audio_id']}.wav")
    print()

import boto3

s3 = boto3.client('s3', region_name='ap-south-1')
bucket = 'my-tts-bucket-ankit-soni'

response = s3.list_objects_v2(
    Bucket=bucket,
    Prefix='temp-audio/'
)

print(f'\nS3 Files in temp-audio folder:')
if 'Contents' in response:
    for obj in response['Contents']:
        size = obj['Size'] / 1024  # Convert to KB
        print(f'  - {obj["Key"]} ({size:.1f} KB)')
else:
    print('  No files found')

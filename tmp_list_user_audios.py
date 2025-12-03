#!/usr/bin/env python3
"""
List all job items for a given user email and print S3 URLs and local paths.
Usage: python tmp_list_user_audios.py <email>
"""
import os
import sys
import boto3
import json

email = sys.argv[1] if len(sys.argv) > 1 else 'ankitks1515@gmail.com'

DYN_USERS = os.getenv('DYNAMODB_TABLE_USERS', 'users')
DYN_JOBS = os.getenv('DYNAMODB_TABLE_NAME', 'jobs')
REGION = os.getenv('DYNAMODB_REGION') or os.getenv('AWS_REGION')

kwargs = {}
if REGION:
    kwargs['region_name'] = REGION
endpoint = os.getenv('DYNAMODB_ENDPOINT_URL')
if endpoint:
    kwargs['endpoint_url'] = endpoint

# Provide creds if set (container env should have them)
aws_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
if aws_key and aws_secret:
    kwargs['aws_access_key_id'] = aws_key
    kwargs['aws_secret_access_key'] = aws_secret

dynamo = boto3.resource('dynamodb', **kwargs)
users_table = dynamo.Table(DYN_USERS)
jobs_table = dynamo.Table(DYN_JOBS)

print('Scanning users table for email=', email)
# Scan users for item with this email
resp = users_table.scan(FilterExpression="contains(#e, :em)", ExpressionAttributeNames={'#e':'email'}, ExpressionAttributeValues={':em': email})
items = resp.get('Items', [])
# If scan with expression failed due to limited environment, fallback to plain scan
if not items:
    try:
        # full scan and filter in Python
        resp2 = users_table.scan()
        items = [it for it in resp2.get('Items', []) if it.get('email') == email]
    except Exception:
        items = []

if not items:
    print('No user record found for email')
    sys.exit(1)

# If multiple users (unlikely), use all
user_ids = [it.get('user_id') for it in items if it.get('user_id')]
print('Found user_ids:', user_ids)

# Scan jobs table and filter by user_id
print('Scanning jobs table for matching user_id...')
all_jobs = []
try:
    respj = jobs_table.scan()
    all_jobs = respj.get('Items', [])
    # handle pagination
    while 'LastEvaluatedKey' in respj:
        respj = jobs_table.scan(ExclusiveStartKey=respj['LastEvaluatedKey'])
        all_jobs.extend(respj.get('Items', []))
except Exception as e:
    print('Failed to scan jobs table:', e)
    sys.exit(1)

matches = [j for j in all_jobs if str(j.get('user_id')) in user_ids]
print(f'Found {len(matches)} job(s) for user {email}:')
for j in sorted(matches, key=lambda x: int(x.get('id')) if x.get('id') else 0):
    print('\n---')
    print('id:', j.get('id'))
    print('status:', j.get('status'))
    print('local_path (s3_final_url):', j.get('s3_final_url'))
    print('audio_s3_url:', j.get('audio_s3_url'))
    print('audio_s3_key:', j.get('audio_s3_key'))

print('\nDone')

#!/usr/bin/env python3
"""
Scan all DynamoDB tables that look like job tables and list items belonging to a user's email.
Usage: python tmp_find_user_jobs_all_tables.py <email>
"""
import os
import sys
import boto3
import json

email = sys.argv[1] if len(sys.argv) > 1 else 'ankitks1515@gmail.com'
region = os.getenv('DYNAMODB_REGION') or os.getenv('AWS_REGION')
kwargs = {}
if region:
    kwargs['region_name'] = region
endpoint = os.getenv('DYNAMODB_ENDPOINT_URL')
if endpoint:
    kwargs['endpoint_url'] = endpoint
aws_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
if aws_key and aws_secret:
    kwargs['aws_access_key_id'] = aws_key
    kwargs['aws_secret_access_key'] = aws_secret

dynamo = boto3.resource('dynamodb', **kwargs)
client = boto3.client('dynamodb', **kwargs)

users_table_name = os.getenv('DYNAMODB_TABLE_USERS', 'users')
users_table = dynamo.Table(users_table_name)

# find user_id(s)
print('Scanning users table for email=', email)
items = []
try:
    resp = users_table.scan()
    items = [it for it in resp.get('Items', []) if it.get('email') == email]
    while 'LastEvaluatedKey' in resp:
        resp = users_table.scan(ExclusiveStartKey=resp['LastEvaluatedKey'])
        items.extend([it for it in resp.get('Items', []) if it.get('email') == email])
except Exception as e:
    print('Failed scanning users table:', e)
    sys.exit(1)

if not items:
    print('No user found for email', email)
    sys.exit(1)

user_ids = [it.get('user_id') for it in items if it.get('user_id')]
print('Found user_ids:', user_ids)

# list tables and pick candidates
all_tables = client.list_tables().get('TableNames', [])
job_tables = [t for t in all_tables if 'job' in t.lower() or 'jobs' in t.lower() or 'tts' in t.lower()]
print('Candidate job tables:', job_tables)

matches = []
for t in job_tables:
    print('\nScanning table', t)
    try:
        tbl = dynamo.Table(t)
        resp = tbl.scan()
        items = resp.get('Items', [])
        while 'LastEvaluatedKey' in resp:
            resp = tbl.scan(ExclusiveStartKey=resp['LastEvaluatedKey'])
            items.extend(resp.get('Items', []))
        for it in items:
            uid = str(it.get('user_id') or it.get('owner') or it.get('user'))
            if uid in [str(x) for x in user_ids]:
                matches.append((t, it))
    except Exception as e:
        print('  scan failed for', t, e)

print('\nFound', len(matches), 'matching items across tables')
for t, it in matches:
    print('\n---')
    print('table:', t)
    print(json.dumps(it, indent=2, default=str))

print('\nDone')

#!/usr/bin/env python3
"""
Dry-run/apply backfill for jobs with missing user_id in the jobs DynamoDB table.
It attempts to infer user_id from `audio_s3_key` which is expected to be like:
`tts/<user_id>/<job_id>/<uuid>.wav`.

Usage:
  python tmp_backfill_jobs_userid.py [--apply] [--table tts-jobs]

Without `--apply` the script only prints proposed updates.
"""
import os
import sys
import argparse
import boto3
import json

parser = argparse.ArgumentParser()
parser.add_argument('--apply', action='store_true', help='Apply updates')
parser.add_argument('--table', default=os.getenv('DYNAMODB_TABLE_NAME','tts_jobs'))
args = parser.parse_args()

REGION = os.getenv('DYNAMODB_REGION') or os.getenv('AWS_REGION')
kwargs = {}
if REGION:
    kwargs['region_name'] = REGION
endpoint = os.getenv('DYNAMODB_ENDPOINT_URL')
if endpoint:
    kwargs['endpoint_url'] = endpoint
aws_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
if aws_key and aws_secret:
    kwargs['aws_access_key_id'] = aws_key
    kwargs['aws_secret_access_key'] = aws_secret

import app.dynamo as ad

print('Using Dynamo table:', args.table)

dynamo = boto3.resource('dynamodb', **kwargs)
tbl = dynamo.Table(args.table)

# scan all items
print('Scanning table for items with missing or empty user_id...')
resp = tbl.scan()
items = resp.get('Items', [])
while 'LastEvaluatedKey' in resp:
    resp = tbl.scan(ExclusiveStartKey=resp['LastEvaluatedKey'])
    items.extend(resp.get('Items', []))

proposed = []
for it in items:
    job_id = it.get('id')
    user_id = it.get('user_id')
    s3_key = it.get('audio_s3_key') or it.get('audio_s3_key')
    if user_id is None or str(user_id).strip()=='' or str(user_id).lower() in ('none','unknown'):
        # try to infer
        inferred = None
        if s3_key and isinstance(s3_key, str):
            parts = s3_key.split('/')
            # expect ['tts', '<user_id>', '<job_id>', '<file>']
            if len(parts) >= 3:
                # second part likely user id
                candidate = parts[1]
                # basic sanity: contains a '-' or '@' (uuid or email) or length>8
                if candidate and (('-' in candidate) or (len(candidate) > 8)):
                    inferred = candidate
        if inferred:
            proposed.append((job_id, inferred, s3_key))

if not proposed:
    print('No proposed updates found')
    sys.exit(0)

print('Proposed updates:')
for job_id, uid, key in proposed:
    print(f'  job {job_id} -> user_id: {uid}  (s3_key={key})')

if not args.apply:
    print('\nDry-run complete. Rerun with --apply to perform updates.')
    sys.exit(0)

# Apply updates using app.dynamo.update_job_item
print('\nApplying updates...')
for job_id, uid, key in proposed:
    try:
        print('Updating job', job_id, '-> user_id', uid)
        ad.update_job_item(int(job_id), {'user_id': str(uid)})
    except Exception as e:
        print('Failed to update job', job_id, e)

print('Done')

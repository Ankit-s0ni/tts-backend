#!/usr/bin/env python3
"""
Enumerate job IDs and print those owned by a given email.
This uses app.dynamo.get_job_item (Dynamo GetItem) so it avoids table scan permissions.
"""
import sys
from app.dynamo import get_job_item
from app.utils.dynamo_user import _get_table as _get_users_table

email = sys.argv[1] if len(sys.argv) > 1 else 'ankitks1515@gmail.com'

# First, find user_id(s) by scanning users table via update-friendly API
users_table = _get_users_table()
# attempt query via scan
user_ids = []
try:
    resp = users_table.scan()
    items = resp.get('Items', [])
    for it in items:
        if it.get('email') == email:
            user_ids.append(it.get('user_id'))
    # pagination
    while 'LastEvaluatedKey' in resp:
        resp = users_table.scan(ExclusiveStartKey=resp['LastEvaluatedKey'])
        for it in resp.get('Items', []):
            if it.get('email') == email:
                user_ids.append(it.get('user_id'))
except Exception:
    # If scan not permitted, fall back to trying common pattern: maybe email not found
    pass

if not user_ids:
    print('No user_id found via scan for', email)
    # Exit — we could also try to check known user id used earlier
    # But attempt to read possible single user by scanning small range of ids

print('user_ids:', user_ids)

found = []
# enumerate ids - range can be adjusted
for i in range(1, 200):
    job = get_job_item(i)
    if not job:
        continue
    uid = job.get('user_id')
    if uid and str(uid) in [str(x) for x in user_ids]:
        found.append(job)

print(f'Found {len(found)} jobs for {email}:')
for j in found:
    print('id:', j.get('id'), 'status:', j.get('status'), 's3_url:', j.get('audio_s3_url'), 'local:', j.get('s3_final_url'))

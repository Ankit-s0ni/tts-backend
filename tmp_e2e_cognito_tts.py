#!/usr/bin/env python3
"""
End-to-end test using Cognito auth to submit a TTS job and poll for completion.
Usage: run in project `backend` directory: `python tmp_e2e_cognito_tts.py`
"""
import os
import sys
import time
from dotenv import load_dotenv

HERE = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(HERE, '.env'))

USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
CLIENT_ID = os.getenv('COGNITO_APP_CLIENT_ID')
AWS_REGION = os.getenv('AWS_REGION')
BACKEND_URL = os.getenv('BACKEND_URL') or 'http://127.0.0.1:8002'

USERNAME = 'ankitks1515@gmail.com'
PASSWORD = 'Ankit@123'

try:
    from pycognito import Cognito
except Exception as e:
    print('pycognito not available; please pip install pycognito')
    raise

import requests

print('Backend URL:', BACKEND_URL)
print('Authenticating user', USERNAME)

user = Cognito(USER_POOL_ID, CLIENT_ID, username=USERNAME, user_pool_region=AWS_REGION)
try:
    user.authenticate(password=PASSWORD)
except Exception as e:
    print('Authentication failed:', e)
    sys.exit(1)

token = getattr(user, 'id_token', None) or getattr(user, 'access_token', None)
if not token:
    print('No token obtained; aborting')
    sys.exit(1)

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

payload = {'text': 'E2E test: generate a short TTS audio file for Ankit.'}
print('Creating job via /tts/jobs')
try:
    r = requests.post(f'{BACKEND_URL}/tts/jobs', json=payload, headers=headers, timeout=30)
except Exception as e:
    print('Failed to connect to backend:', e)
    sys.exit(1)

print('create job response', r.status_code)
try:
    print(r.json())
except Exception:
    print(r.text)

if r.status_code not in (200,201):
    print('Job creation failed; aborting')
    sys.exit(1)

job = r.json()
job_id = job.get('id') or job.get('job_id')
print('Job ID:', job_id)
if not job_id:
    print('No job id returned; aborting')
    sys.exit(1)

# Poll for status
print('Polling job status...')
final = None
for i in range(300):
    try:
        rr = requests.get(f'{BACKEND_URL}/tts/jobs/{job_id}', headers=headers, timeout=15)
    except Exception as e:
        print('Status request failed:', e)
        time.sleep(1)
        continue
    if rr.status_code!=200:
        print('status fetch', rr.status_code, rr.text)
    else:
        data = rr.json()
        st = data.get('status')
        print(i, 'status', st)
        if st in ('completed','failed','error'):
            final = data
            break
    time.sleep(1)

print('Final job record:')
print(final)

# List output files
out_dir = os.path.join(HERE, 'output')
print('\nListing output dir:', out_dir)
if os.path.exists(out_dir):
    for root,dirs,files in os.walk(out_dir):
        for f in files:
            fp = os.path.join(root,f)
            try:
                print(fp, os.path.getsize(fp))
            except Exception:
                print(fp)
else:
    print('No output directory found')

print('\nDone')

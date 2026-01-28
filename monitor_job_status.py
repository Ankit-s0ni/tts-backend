#!/usr/bin/env python3
"""
Monitor TTS Job Status Transitions
Continuously poll a job to see if it moves from queued → processing → completed
"""

import requests
import json
import time

BASE_URL = 'http://127.0.0.1:8002'

# Register and login
test_email = f'test_monitor_{int(time.time())}@example.com'
test_password = 'TestPass123!@'

print('Registering user...')
requests.post(f'{BASE_URL}/auth/register',
    json={'email': test_email, 'password': test_password})

print('Logging in...')
login = requests.post(f'{BASE_URL}/auth/login',
    json={'email': test_email, 'password': test_password})

token = login.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

# Create a TTS job
print('\nCreating TTS job...')
job_resp = requests.post(f'{BASE_URL}/tts/jobs',
    json={
        'text': 'This is a test message to check job processing status',
        'voice_id': 'en_US-lessac-high'
    },
    headers=headers
)

job_id = job_resp.json()['id']
print(f'Job created: {job_id}')

# Monitor job status
print('\nMonitoring job status (updating every 1 second for 60 seconds)...')
print('='*70)

max_checks = 60
for check_num in range(1, max_checks + 1):
    job = requests.get(f'{BASE_URL}/tts/jobs/{job_id}', headers=headers).json()
    
    status = job.get('status')
    audio_url = job.get('audio_url')
    created_at = job.get('created_at')
    
    elapsed = check_num
    print(f'[{elapsed:2d}s] Status: {status:12s} | Audio URL: {("YES" if audio_url else "NO"):3s}')
    
    if status == 'completed':
        print(f'\nJob completed successfully!')
        print(f'Audio URL: {audio_url}')
        break
    
    if status == 'failed':
        print(f'\nJob failed!')
        break
    
    time.sleep(1)

print('='*70)
print(f'\nFinal job status: {job.get("status")}')
print(f'Full job data: {json.dumps(job, indent=2)}')

# Check worker status via Flower API
print('\n\nChecking worker status via Flower API...')
try:
    flower_stats = requests.get('http://127.0.0.1:5556/api/workers', timeout=5)
    if flower_stats.status_code == 200:
        workers = flower_stats.json()
        print(f'Active workers: {json.dumps(workers, indent=2)}')
    else:
        print(f'Flower API returned {flower_stats.status_code}')
except Exception as e:
    print(f'Could not connect to Flower: {e}')

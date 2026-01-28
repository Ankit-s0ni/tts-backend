#!/usr/bin/env python3
"""
Debug: Compare Voice API response vs Flutter app calls
Check if voice_id parameter names match
"""

import requests
import json

BASE_URL = 'http://127.0.0.1:8002'

# Get available voices
print('='*70)
print('STEP 1: Get available voices from API')
print('='*70)
voices_resp = requests.get(f'{BASE_URL}/voices/')
voices = voices_resp.json()

print(f'Total voices available: {len(voices)}')
print(f'\nFirst 3 voices structure:')
for voice in voices[:3]:
    print(json.dumps(voice, indent=2))

# Check voice ID format
print(f'\n\nVoice ID examples:')
for voice in voices[:5]:
    print(f'  - {voice.get("id")} ({voice.get("display_name")})')

# Get a valid voice ID
valid_voice_id = voices[0]['id'] if voices else None
print(f'\nSelected voice ID for testing: {valid_voice_id}')

# Register and login
print('\n' + '='*70)
print('STEP 2: Register and Login')
print('='*70)

import time
test_email = f'test_debug_{int(time.time())}@example.com'
test_password = 'TestPass123!@'

reg_resp = requests.post(
    f'{BASE_URL}/auth/register',
    json={'email': test_email, 'password': test_password}
)
print(f'Register: {reg_resp.status_code}')

login_resp = requests.post(
    f'{BASE_URL}/auth/login',
    json={'email': test_email, 'password': test_password}
)
print(f'Login: {login_resp.status_code}')

token = login_resp.json().get('access_token')
headers = {'Authorization': f'Bearer {token}'}

# Test sync TTS with voice_id (what Flutter does)
print('\n' + '='*70)
print('STEP 3: Test /tts/sync with voice_id parameter')
print('='*70)

payload = {
    'text': 'Hello, this is a test message',
    'voice': valid_voice_id
}
print(f'Payload: {json.dumps(payload, indent=2)}')

sync_resp = requests.post(
    f'{BASE_URL}/tts/sync',
    json=payload,
    headers=headers
)

print(f'Status: {sync_resp.status_code}')
print(f'Response: {json.dumps(sync_resp.json(), indent=2)}')

# Test createJob with voice_id (what Flutter does)
print('\n' + '='*70)
print('STEP 4: Test /tts/jobs POST with voice_id parameter')
print('='*70)

job_payload = {
    'text': 'This is a longer test message for job synthesis',
    'voice_id': valid_voice_id,
    'language': 'en_US'
}
print(f'Payload: {json.dumps(job_payload, indent=2)}')

job_resp = requests.post(
    f'{BASE_URL}/tts/jobs',
    json=job_payload,
    headers=headers
)

print(f'Status: {job_resp.status_code}')
print(f'Response: {json.dumps(job_resp.json(), indent=2)}')

# Check if audio_url is present
if job_resp.status_code == 200:
    job_data = job_resp.json()
    print(f'\nJob created: {job_data.get("id")}')
    print(f'Status: {job_data.get("status")}')
    print(f'Audio URL: {job_data.get("audio_url")}')

print('\n' + '='*70)
print('ANALYSIS')
print('='*70)
print(f'1. Voice API returns voice.id field: {voices[0].get("id")}')
print(f'2. Flutter sends voice_id parameter to /tts/sync: {job_payload.get("voice_id")}')
print(f'3. Flutter sends voice_id parameter to /tts/jobs: {job_payload.get("voice_id")}')
print(f'\nIf sync/jobs failed, check if the API expects "voice" or "voice_id" param')

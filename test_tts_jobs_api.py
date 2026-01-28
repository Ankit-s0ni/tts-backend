#!/usr/bin/env python3
"""
Test TTS Jobs API Endpoints
Tests POST /tts/jobs, GET /tts/jobs, GET /tts/jobs/{job_id}
"""

import requests
import json
import sys
import time

BASE_URL = 'http://127.0.0.1:8002'
TIMEOUT = 20

def test_endpoint(method, path, data=None, name=None, headers=None):
    """Test an API endpoint and print results."""
    url = f'{BASE_URL}{path}'
    label = name or f'{method} {path}'
    
    print(f'\n{"="*70}')
    print(f'TEST: {label}')
    print(f'URL:  {url}')
    if headers:
        print(f'HEADERS: {headers}')
    if data:
        print(f'DATA: {json.dumps(data, indent=2)}')
    print('='*70)
    
    try:
        if method == 'GET':
            response = requests.get(url, timeout=TIMEOUT, headers=headers)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=TIMEOUT, headers=headers)
        else:
            print(f'ERROR: Unknown method {method}')
            return None
        
        print(f'STATUS: {response.status_code}')
        
        # Try to parse JSON
        try:
            resp_json = response.json()
            print(f'RESPONSE:\n{json.dumps(resp_json, indent=2)}')
            return resp_json
        except:
            # Not JSON, just print raw
            print(f'RESPONSE (raw):\n{response.text[:500]}')
            return None
        
    except requests.ConnectionError as e:
        print(f'ERROR: Connection failed - {e}')
        return None
    except requests.Timeout:
        print(f'ERROR: Request timeout after {TIMEOUT}s')
        return None
    except Exception as e:
        print(f'ERROR: {type(e).__name__}: {e}')
        return None

def main():
    print('\n' + '='*70)
    print('TTS JOBS API TEST SUITE')
    print('='*70)
    print(f'Base URL: {BASE_URL}')
    print(f'Timeout:  {TIMEOUT}s')
    
    results = {}
    
    # Phase 0: Try to get a valid token by registering/logging in
    print(f'\n\nPHASE 0: AUTHENTICATION')
    token = None
    
    # Try registration
    test_email = f'test_user_{int(time.time())}@example.com'
    test_password = 'TestPass123!@'
    
    print(f'\nAttempting to register: {test_email}')
    reg_response = test_endpoint(
        'POST',
        '/auth/register',
        data={'email': test_email, 'password': test_password},
        name='Register User'
    )
    
    if reg_response and 'user_id' in reg_response:
        print(f'Registration successful')
    else:
        print(f'Registration failed or user already exists')
    
    # Try login
    print(f'\nAttempting to login: {test_email}')
    login_response = test_endpoint(
        'POST',
        '/auth/login',
        data={'email': test_email, 'password': test_password},
        name='Login User'
    )
    
    if login_response and 'access_token' in login_response:
        token = login_response.get('access_token')
        print(f'Login successful - got token')
    else:
        print(f'Login failed')
    
    if not token:
        print('\nERROR: Could not obtain authentication token')
        print('TTS Jobs endpoints require authentication.')
        return 1
    
    headers = {'Authorization': f'Bearer {token}'}
    print(f'\nUsing token for subsequent requests')
    
    # Test 1: Create a TTS job
    print(f'\n\nPHASE 1: CREATE TTS JOB')
    job_data = {
        'text': 'This is a test message to synthesize. The quick brown fox jumps over the lazy dog.',
        'voice_id': 'en_US-lessac-high',
        'language': 'en_US'
    }
    job_response = test_endpoint(
        'POST',
        '/tts/jobs',
        data=job_data,
        headers=headers,
        name='Create TTS Job'
    )
    
    if job_response and isinstance(job_response, dict):
        results['create_job'] = True
        job_id = job_response.get('id')
        print(f'\nJob created successfully with ID: {job_id}')
    else:
        results['create_job'] = False
        job_id = None
        print('\nFailed to create job')
    
    # Test 2: List all jobs
    print(f'\n\nPHASE 2: LIST ALL JOBS')
    jobs_list = test_endpoint(
        'GET',
        '/tts/jobs?limit=10',
        headers=headers,
        name='List TTS Jobs'
    )
    
    if jobs_list and isinstance(jobs_list, list):
        results['list_jobs'] = True
        print(f'\nRetrieved {len(jobs_list)} job(s)')
    else:
        results['list_jobs'] = False
        print('\nFailed to list jobs')
    
    # Test 3: Get specific job details (if we have a job_id)
    if job_id:
        print(f'\n\nPHASE 3: GET JOB DETAILS')
        time.sleep(2)  # Wait a bit for job processing to start
        
        job_details = test_endpoint(
            'GET',
            f'/tts/jobs/{job_id}',
            headers=headers,
            name=f'Get Job Details ({job_id})'
        )
        
        if job_details and isinstance(job_details, dict):
            results['get_job'] = True
            status = job_details.get('status')
            print(f'\nJob status: {status}')
            if job_details.get('audio_url'):
                print(f'Audio URL available: {job_details.get("audio_url")}')
            else:
                print(f'(Audio not yet ready - job may still be processing)')
        else:
            results['get_job'] = False
            print('\nFailed to get job details')
    else:
        results['get_job'] = False
        print('\n\nPHASE 3: SKIPPED (no job ID from creation)')
    
    # Test 4: Try with invalid job ID
    print(f'\n\nPHASE 4: ERROR HANDLING - Invalid Job ID')
    invalid_response = test_endpoint(
        'GET',
        '/tts/jobs/invalid-job-id-12345',
        headers=headers,
        name='Get Non-existent Job (should return 404)'
    )
    
    # Summary
    print(f'\n{"="*70}')
    print('SUMMARY')
    print('='*70)
    for test_name, passed in results.items():
        status = 'PASS' if passed else 'FAIL'
        print(f'{test_name:20s} {status}')
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f'\nTotal: {passed}/{total} critical tests passed')
    
    return 0 if passed >= 3 else 1

if __name__ == '__main__':
    sys.exit(main())

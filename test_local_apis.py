#!/usr/bin/env python3
"""
Local API Test Script
Tests all endpoints on http://127.0.0.1:8002
"""

import requests
import json
import sys

BASE_URL = 'http://127.0.0.1:8002'
TIMEOUT = 10

def test_endpoint(method, path, data=None, name=None):
    """Test an API endpoint and print results."""
    url = f'{BASE_URL}{path}'
    label = name or f'{method} {path}'
    
    print(f'\n{"="*60}')
    print(f'TEST: {label}')
    print(f'URL:  {url}')
    print('='*60)
    
    try:
        if method == 'GET':
            response = requests.get(url, timeout=TIMEOUT)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=TIMEOUT)
        else:
            print(f'ERROR: Unknown method {method}')
            return False
        
        print(f'STATUS: {response.status_code}')
        
        # Try to parse JSON
        try:
            resp_json = response.json()
            print(f'RESPONSE:\n{json.dumps(resp_json, indent=2)}')
        except:
            # Not JSON, just print raw
            print(f'RESPONSE (raw):\n{response.text}')
        
        return response.status_code < 400
        
    except requests.ConnectionError as e:
        print(f'ERROR: Connection failed')
        print(f'Details: {e}')
        return False
    except requests.Timeout:
        print(f'ERROR: Request timeout after {TIMEOUT}s')
        return False
    except Exception as e:
        print(f'ERROR: {type(e).__name__}: {e}')
        return False

def main():
    print('\n' + '='*60)
    print('LOCAL API TEST SUITE')
    print('='*60)
    print(f'Base URL: {BASE_URL}')
    print(f'Timeout:  {TIMEOUT}s')
    
    results = {}
    
    # Test 1: Health check
    results['health'] = test_endpoint('GET', '/health', name='Health Check')
    
    # Test 2: Config
    results['config'] = test_endpoint('GET', '/config', name='API Config')
    
    # Test 3: Voices list
    results['voices'] = test_endpoint('GET', '/voices/', name='List Voices')
    
    # Test 4: Sync TTS (short text)
    results['tts_sync'] = test_endpoint(
        'POST',
        '/tts/sync',
        data={
            'text': 'Hello from local test',
            'voice': 'en_US-lessac-high'
        },
        name='TTS Sync (short text)'
    )
    
    # Summary
    print(f'\n{"="*60}')
    print('SUMMARY')
    print('='*60)
    for test_name, passed in results.items():
        status = 'PASS' if passed else 'FAIL'
        print(f'{test_name:20s} {status}')
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f'\nTotal: {passed}/{total} tests passed')
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())

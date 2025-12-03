"""Authenticate with Cognito and test /auth/link-profile and /users/me/profile endpoints.

Usage: python scripts/test_profile_endpoints.py <email> <password>
"""
import os
import sys
from dotenv import load_dotenv
import requests

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(HERE, '.env'))

USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
CLIENT_ID = os.getenv('COGNITO_APP_CLIENT_ID')
AWS_REGION = os.getenv('AWS_REGION')
BACKEND_URL = os.getenv('BACKEND_URL') or 'http://127.0.0.1:8002'

if len(sys.argv) < 3:
    print('Usage: python scripts/test_profile_endpoints.py <email> <password>')
    sys.exit(2)

username = sys.argv[1]
password = sys.argv[2]

try:
    from pycognito import Cognito
except Exception:
    print('pycognito not installed; run pip install pycognito')
    raise

user = Cognito(USER_POOL_ID, CLIENT_ID, username=username, user_pool_region=AWS_REGION)
user.authenticate(password=password)
token = getattr(user, 'id_token', None) or getattr(user, 'access_token', None)
if not token:
    print('No token obtained')
    sys.exit(1)

headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

payload = {
    'full_name': 'Ankit S',
    'phone': '9999999999',
    'age': 30,
    'profile_image': 'https://example.com/avatar.png'
}

print('Calling POST /auth/link-profile')
r = requests.post(f'{BACKEND_URL}/auth/link-profile', json=payload, headers=headers, timeout=15)
print(r.status_code)
try:
    print(r.json())
except Exception:
    print(r.text)

print('\nCalling GET /users/me/profile')
r2 = requests.get(f'{BACKEND_URL}/users/me/profile', headers=headers, timeout=15)
print(r2.status_code)
try:
    print(r2.json())
except Exception:
    print(r2.text)

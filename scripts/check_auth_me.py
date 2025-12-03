"""Simple script to authenticate with Cognito and call backend /auth/me.

Usage:
  python check_auth_me.py <username> <password>

It loads `backend/.env` for Cognito config and calls the running backend at http://127.0.0.1:8002/auth/me
"""
from dotenv import load_dotenv
import os, sys, traceback
import httpx

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(HERE, '.env'))

COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
CLIENT_ID = os.getenv('COGNITO_APP_CLIENT_ID')
AWS_REGION = os.getenv('AWS_REGION')
BACKEND_URL = os.getenv('BACKEND_URL') or 'http://127.0.0.1:8002'

if not (COGNITO_USER_POOL_ID and CLIENT_ID and AWS_REGION):
    print('Missing Cognito configuration in .env (COGNITO_USER_POOL_ID, COGNITO_APP_CLIENT_ID, AWS_REGION)')
    sys.exit(2)

if len(sys.argv) >= 3:
    username = sys.argv[1]
    password = sys.argv[2]
else:
    print('Usage: python check_auth_me.py <username> <password>')
    sys.exit(2)

try:
    from pycognito import Cognito
except Exception:
    print('pycognito not installed. Run: pip install pycognito')
    raise

try:
    user = Cognito(COGNITO_USER_POOL_ID, CLIENT_ID, username=username, user_pool_region=AWS_REGION)
    user.authenticate(password=password)
    token = getattr(user, 'id_token', None) or getattr(user, 'access_token', None)
    if not token:
        print('No token obtained from Cognito')
        sys.exit(1)
    print('Obtained token (len):', len(token))
except Exception:
    print('Cognito authentication failed:')
    traceback.print_exc()
    sys.exit(1)

headers = {'Authorization': f'Bearer {token}'}
try:
    r = httpx.get(f'{BACKEND_URL}/auth/me', headers=headers, timeout=10.0)
    print('/auth/me', r.status_code)
    try:
        print(r.json())
    except Exception:
        print(r.text)
except Exception:
    print('Request to backend failed:')
    traceback.print_exc()
    sys.exit(1)

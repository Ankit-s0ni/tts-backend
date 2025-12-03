from pycognito import Cognito
from dotenv import load_dotenv
import os
import sys

# Load .env from backend dir
here = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(here, '.env'))

USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
CLIENT_ID = os.getenv('COGNITO_APP_CLIENT_ID')
AWS_REGION = os.getenv('AWS_REGION')

if not (USER_POOL_ID and CLIENT_ID and AWS_REGION):
    print('Missing Cognito config. Please set COGNITO_USER_POOL_ID, COGNITO_APP_CLIENT_ID and AWS_REGION in backend/.env')
    sys.exit(2)

if len(sys.argv) < 3:
    print('Usage: python auth_with_cognito.py <email> <password>')
    sys.exit(2)

username = sys.argv[1]
password = sys.argv[2]

try:
    user = Cognito(USER_POOL_ID, CLIENT_ID, username=username, user_pool_region=AWS_REGION)
    user.authenticate(password=password)
    print('Authentication succeeded')
    print('ID token:', getattr(user, 'id_token', None))
    print('Access token:', getattr(user, 'access_token', None))
    print('Refresh token:', getattr(user, 'refresh_token', None))
    try:
        claims = user.id_token_jwt_claims
    except Exception:
        claims = {}
    print('Claims (id token):', claims)
except Exception as e:
    print('Authentication failed:', e)
    raise

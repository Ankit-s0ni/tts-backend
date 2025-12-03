from dotenv import load_dotenv
import os, traceback
base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(base, '.env'))
from pycognito import Cognito
from dotenv import load_dotenv

COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
CLIENT_ID = os.getenv('COGNITO_APP_CLIENT_ID')
AWS_REGION = os.getenv('AWS_REGION')

user = Cognito(COGNITO_USER_POOL_ID, CLIENT_ID, username=os.getenv('COGNITO_TEST_USER') or (os.sys.argv[1] if len(os.sys.argv)>1 else None), user_pool_region=AWS_REGION)
password = os.getenv('COGNITO_TEST_PASS') or (os.sys.argv[2] if len(os.sys.argv)>2 else None)
user.authenticate(password=password)
token = getattr(user, 'access_token', None) or getattr(user, 'id_token', None)
print('Token length', len(token))

# Import app.auth and call get_current_user
import app.auth as auth
try:
    u = auth.get_current_user(token=token)
    print('Verified user:', u)
except Exception as e:
    print('get_current_user raised:')
    traceback.print_exc()

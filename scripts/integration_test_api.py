from dotenv import load_dotenv
import os, sys, traceback

# Load env
base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(base, '.env'))

COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
CLIENT_ID = os.getenv('COGNITO_APP_CLIENT_ID')
AWS_REGION = os.getenv('AWS_REGION')

if not (COGNITO_USER_POOL_ID and CLIENT_ID and AWS_REGION):
    print('Missing Cognito config in .env')
    sys.exit(2)

# Credentials provided on command line or via env
if len(sys.argv) >= 3:
    username = sys.argv[1]
    password = sys.argv[2]
else:
    username = os.getenv('COGNITO_TEST_USER')
    password = os.getenv('COGNITO_TEST_PASS')

if not (username and password):
    print('Provide username and password as args or set COGNITO_TEST_USER/COGNITO_TEST_PASS in .env')
    sys.exit(2)

# Authenticate to Cognito to obtain an access token
try:
    from pycognito import Cognito
except Exception as e:
    print('pycognito not installed; run `pip install pycognito`')
    raise

try:
    user = Cognito(COGNITO_USER_POOL_ID, CLIENT_ID, username=username, user_pool_region=AWS_REGION)
    user.authenticate(password=password)
    token = getattr(user, 'access_token', None) or getattr(user, 'id_token', None)
    if not token:
        print('No token returned')
        sys.exit(1)
    print('Obtained token, length', len(token))
except Exception:
    print('Authentication failed:')
    traceback.print_exc()
    sys.exit(1)

# Now call the FastAPI app using TestClient
try:
    from fastapi.testclient import TestClient
    from app.main import app
except Exception:
    print('Failed to import FastAPI app:')
    traceback.print_exc()
    sys.exit(1)

client = TestClient(app)
headers = {'Authorization': f'Bearer {token}'}

# Create a job
print('Creating job...')
resp = client.post('/tts/jobs', json={'text': 'Integration test: hello'}, headers=headers)
print('POST /tts/jobs', resp.status_code, resp.text)
if resp.status_code not in (200, 201):
    sys.exit(1)

job = resp.json()
job_id = job.get('id')
print('Created job id', job_id)

# Fetch job
print('Fetching job...')
r = client.get(f'/tts/jobs/{job_id}', headers=headers)
print(f'GET /tts/jobs/{job_id}', r.status_code, r.text)

print('Integration test finished')

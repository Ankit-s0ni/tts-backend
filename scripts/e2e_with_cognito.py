from dotenv import load_dotenv
import os, sys, time, traceback
import httpx

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(base_dir, '.env'))

BASE = os.getenv('BACKEND_URL') or os.getenv('BACKEND_BASE') or 'http://127.0.0.1:8001'
INPUT_PATH = os.path.join(base_dir, 'input', 'large_test.txt')

COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
CLIENT_ID = os.getenv('COGNITO_APP_CLIENT_ID')
AWS_REGION = os.getenv('AWS_REGION')

if not (COGNITO_USER_POOL_ID and CLIENT_ID and AWS_REGION):
    print('Missing Cognito config in .env')
    sys.exit(2)

# Credentials from args or .env
if len(sys.argv) >= 3:
    username = sys.argv[1]
    password = sys.argv[2]
else:
    username = os.getenv('COGNITO_TEST_USER')
    password = os.getenv('COGNITO_TEST_PASS')

if not (username and password):
    print('Provide username and password as args or set COGNITO_TEST_USER/COGNITO_TEST_PASS in .env')
    sys.exit(2)

# Authenticate
try:
    from pycognito import Cognito
except Exception as e:
    print('pycognito not installed; run `pip install pycognito`')
    raise

try:
    user = Cognito(COGNITO_USER_POOL_ID, CLIENT_ID, username=username, user_pool_region=AWS_REGION)
    user.authenticate(password=password)
    # Prefer the ID token for backend auth; fall back to access token.
    token = getattr(user, 'id_token', None) or getattr(user, 'access_token', None)
    if not token:
        print('No token returned')
        sys.exit(1)
    print('Obtained token, length', len(token))
except Exception:
    print('Authentication failed:')
    traceback.print_exc()
    sys.exit(1)

# Read input
if not os.path.exists(INPUT_PATH):
    print('Input file not found at', INPUT_PATH)
    sys.exit(1)
with open(INPUT_PATH, 'r', encoding='utf8') as fh:
    text = fh.read()
print('Read input length', len(text))

headers = {'Authorization': f'Bearer {token}'}

# Create job
print('Creating job via /tts/jobs')
try:
    resp = httpx.post(f'{BASE}/tts/jobs', json={'text': text}, headers=headers, timeout=30.0)
except Exception as e:
    print('Request failed:', e)
    sys.exit(1)
print('create job response', resp.status_code, resp.text)
if resp.status_code not in (200,201):
    print('Job creation failed')
    sys.exit(1)
job = resp.json()
job_id = job.get('id')
print('Job ID:', job_id)

# Poll job status
for i in range(300):
    try:
        r = httpx.get(f"{BASE}/tts/jobs/{job_id}", headers=headers, timeout=20.0)
    except Exception as e:
        print('poll request failed', e)
        time.sleep(1)
        continue
    if r.status_code!=200:
        print('poll status', r.status_code, r.text)
    else:
        st = r.json().get('status')
        print(i, 'status', st)
        if st in ('completed','failed','error'):
            break
    time.sleep(1)

print('Final GET')
r = httpx.get(f"{BASE}/tts/jobs/{job_id}", headers=headers, timeout=10.0)
print('final job GET', r.status_code, r.text)
print('\nDone')

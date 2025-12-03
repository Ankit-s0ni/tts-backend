import httpx, time, os, sys
from app.db import SessionLocal, engine, Base
from app.models import User
from app import auth

# create user directly in SQLite DB
email = 'e2e-api@example.com'
password = 'StrongPassw0rd!'
print('Ensuring user exists in local SQLite DB:', email)
Base.metadata.create_all(bind=engine)
session = SessionLocal()
try:
    u = session.query(User).filter(User.email==email).first()
    if u:
        print('User already exists with id', u.id)
    else:
        # This project now uses Cognito for authentication. Store a lightweight
        # local profile entry (without passwords) if you want a mapping.
        nu = User(email=email, cognito_sub=None)
        session.add(nu)
        session.commit()
        print('Created user id', nu.id)
finally:
    session.close()

# Generate a signed access token directly (skip login) and use it for API calls
base='http://127.0.0.1:8001'
print('Using token from TEST_COGNITO_TOKEN environment variable')
token = os.getenv('TEST_COGNITO_TOKEN')
if not token:
    print('No TEST_COGNITO_TOKEN provided; cannot run e2e script against Cognito-backed API')
    sys.exit(1)
headers = {'Authorization': f'Bearer {token}'}

# Read long input
input_path = './input/large_test.txt'
with open(input_path,'r',encoding='utf8') as fh:
    text = fh.read()
print('Input read, length', len(text))

# Create job via API
print('Creating job via /tts/jobs')
resp = httpx.post(base+'/tts/jobs', json={'text': text}, headers=headers, timeout=30.0)
print('create job response', resp.status_code)
if resp.status_code not in (200,201):
    print('response text', resp.text)
    sys.exit(1)
job = resp.json()
job_id = job.get('id')
print('Job ID:', job_id)

# Poll job status
for i in range(600):
    r = httpx.get(f"{base}/tts/jobs/{job_id}", headers=headers, timeout=20.0)
    if r.status_code!=200:
        print('poll status', r.status_code, r.text)
    else:
        st = r.json().get('status')
        print(i, 'status', st)
        if st in ('completed','failed','error'):
            break
    time.sleep(1)

# final job GET
r = httpx.get(f"{base}/tts/jobs/{job_id}", headers=headers, timeout=20.0)
print('final job GET', r.status_code, r.text)

# List output files
out_dir='./output'
print('Listing ./output:')
for root,dirs,files in os.walk(out_dir):
    for f in files:
        fp=os.path.join(root,f)
        print(fp, os.path.getsize(fp))

print('\nDone')

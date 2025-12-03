import httpx, time, os, sys
base='http://127.0.0.1:8001'
input_path='./input/large_test.txt'
with open(input_path,'r',encoding='utf8') as fh:
    text = fh.read()

print('Read input length', len(text), 'chars')

# Register user (try register, fallback to login)
email='test@test.com'
password='Test1234'
print('Attempting to register user', email)
try:
    r = httpx.post(base+'/auth/register', json={'email':email,'password':password}, timeout=20.0)
    print('register status', r.status_code, r.text)
    if r.status_code==200:
        token = r.json().get('access_token')
    else:
        # try login
        r2 = httpx.post(base+'/auth/login', json={'email':email,'password':password}, timeout=20.0)
        print('login status', r2.status_code, r2.text)
        token = r2.json().get('access_token')
except Exception as e:
    print('auth request failed', e)
    sys.exit(1)

if not token:
    print('Failed to obtain token; aborting')
    sys.exit(1)

headers={'Authorization':f'Bearer {token}'}

# Create job via API
print('Creating job via /tts/jobs (this will enqueue via Celery)')
resp = httpx.post(base+'/tts/jobs', json={'text': text}, headers=headers, timeout=20.0)
print('create job response', resp.status_code, resp.text)
if resp.status_code!=200 and resp.status_code!=201:
    print('Job creation failed')
    sys.exit(1)
job = resp.json()
job_id = job.get('id')
print('Job ID:', job_id)

# Poll job status until completed
for i in range(600):
    r = httpx.get(f"{base}/tts/jobs/{job_id}", headers=headers, timeout=20.0)
    if r.status_code!=200:
        print('poll status', r.status_code, r.text)
    else:
        st = r.json().get('status')
        print(i, 'status', st)
        if st=='completed' or st=='failed' or st=='error':
            break
    time.sleep(1)

# Dump final job record directly from Dynamo via API: get endpoint returns minimal fields
r = httpx.get(f"{base}/tts/jobs/{job_id}", headers=headers, timeout=10.0)
print('final job GET', r.status_code, r.text)

# List output files and stats
out_dir='./output'
print('Listing ./output:')
for root,dirs,files in os.walk(out_dir):
    for f in files:
        fp=os.path.join(root,f)
        print(fp, os.path.getsize(fp))

print('\nDone')

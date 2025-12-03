import httpx, time, os
base='http://127.0.0.1:8000'
print('registering user')
try:
    r = httpx.post(base+'/auth/register', json={'email':'test@example.com','password':'testpass'}, timeout=10.0)
    print('register status', r.status_code, r.text)
    token = r.json().get('access_token')
except Exception as e:
    print('register failed or already registered:', e)
    r = httpx.post(base+'/auth/login', json={'email':'test@example.com','password':'testpass'}, timeout=10.0)
    print('login status', r.status_code, r.text)
    token = r.json().get('access_token')

headers = {'Authorization': f'Bearer {token}'}
print('\ncreating job')
resp = httpx.post(base+'/tts/jobs', json={'text':'This is a Celery job test. Please synth.'}, headers=headers, timeout=10.0)
print('create job status', resp.status_code, resp.text)
job = resp.json()
job_id = job.get('id')
print('job id', job_id)

# poll job status
for i in range(60):
    r = httpx.get(f"{base}/tts/jobs/{job_id}", headers=headers, timeout=10.0)
    print(i, 'status', r.status_code, r.text)
    if r.status_code==200 and 'completed' in r.text:
        break
    time.sleep(1)

# list output files
print('\nOutput dir:')
for root,dirs,files in os.walk('/app/output'):
    for f in files:
        print(os.path.join(root,f), os.path.getsize(os.path.join(root,f)))

print('\nDone')

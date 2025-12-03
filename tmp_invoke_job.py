import time
from app.dynamo import create_job_item, get_job_item
import celery_worker

# create a job directly in DynamoDB (no HTTP auth required for test)
job = create_job_item(None, {'text':'End-to-end worker test. This should synth via Piper using default model.'})
job_id = int(job['id'])
print('created job id', job_id)
# Run the worker code synchronously in this process (simulate worker run)
print('running process_job synchronously in this container')
res = celery_worker.process_job(job_id)
print('process_job returned:', res)

# poll for status
for i in range(60):
    j = get_job_item(job_id)
    print(i, 'job status', j.get('status'))
    if j.get('status') in ('completed','failed','error'):
        break
    time.sleep(1)
print('final job record:', get_job_item(job_id))
# show output files
import os
print('\nOutput files:')
out_dir = os.path.join(os.getcwd(), 'output')
if os.path.exists(out_dir):
    for f in os.listdir(out_dir):
        print(f, os.path.getsize(os.path.join(out_dir, f)))
else:
    print('no output dir', out_dir)

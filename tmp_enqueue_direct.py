from app.dynamo import create_job_item, get_job_item
import time
import celery_worker

job = create_job_item(None, {'text':'Quick direct enqueue test. This uses Celery delay to enqueue a job for the worker to process.'})
job_id = int(job['id'])
print('Created job id', job_id)
try:
    res = celery_worker.process_job.delay(job_id)
    print('Enqueued task id', res.id)
except Exception as e:
    print('Failed to enqueue via Celery.delay', e)
    raise

# poll job status
for i in range(60):
    j = get_job_item(job_id)
    print(i, 'job status', j.get('status'))
    if j.get('status') in ('completed','failed','error'):
        break
    time.sleep(1)
print('final job record:', get_job_item(job_id))

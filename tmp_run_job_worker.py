from app.dynamo import get_job_item
import celery_worker

JOB_ID = 1
print('running process_job synchronously for', JOB_ID)
res = celery_worker.process_job(JOB_ID)
print('process_job returned:', res)
print('final job record:', get_job_item(JOB_ID))

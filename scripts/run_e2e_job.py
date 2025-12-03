"""Create a job in DynamoDB and run the worker synchronously for end-to-end test.

Usage: run from `backend` folder: `python scripts/run_e2e_job.py`
"""
import os
import sys
import traceback
from dotenv import load_dotenv

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(HERE, '.env'))

def main():
    try:
        from app.dynamo import create_job_item
        from celery_worker import process_job

        user_id = os.getenv('TEST_USER_ID') or 'e2e-user'
        job_in = {'text': 'Hello world from end-to-end test.', 'voice_id': 'en_US-lessac-medium'}

        item = create_job_item(user_id, job_in)
        job_id = int(item.get('id'))
        print('Created job id:', job_id)

        print('Running worker.process_job synchronously...')
        # Call the Celery task's run method to execute the implementation inline
        result = process_job.run(job_id)
        print('Worker result:', result)

    except Exception:
        traceback.print_exc()
        sys.exit(2)


if __name__ == '__main__':
    main()

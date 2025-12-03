import sqlite3
from celery import Celery

DB='dev.db'
JOB_ID=2

conn=sqlite3.connect(DB)
c=conn.cursor()
print('PRAGMA table_info(jobs):')
for row in c.execute('PRAGMA table_info("jobs")'):
    print(row)

r=list(c.execute('SELECT id, text, status, s3_final_url FROM jobs WHERE id=?', (JOB_ID,)))
print('job row:', r)

if r and (r[0][1] is None or r[0][1]==''):
    print('job text is empty, updating with test text')
    c.execute('UPDATE jobs SET text=? WHERE id=?', ('Hello from reprocessed job', JOB_ID))
    conn.commit()
else:
    print('job text present or job not found')

conn.close()

# enqueue the task
app = Celery('tmp', broker='redis://127.0.0.1:6379/0')
res = app.send_task('backend.process_job', args=(JOB_ID,))
print('sent', res.id)

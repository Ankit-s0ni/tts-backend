import sqlite3
from celery import Celery

DB='dev.db'
conn=sqlite3.connect(DB)
c=conn.cursor()
# insert a test job
c.execute("INSERT INTO jobs (user_id, language, voice_id, text, include_alignments, status, created_at, updated_at) VALUES (?,?,?,?,?,?,datetime('now'),datetime('now'))", (None,'en','default','Assistant test job',False,'queued'))
job_id = c.lastrowid
conn.commit()
conn.close()
print('inserted job', job_id)
app=Celery('tmp', broker='redis://127.0.0.1:6379/0')
res=app.send_task('backend.process_job', args=(job_id,))
print('sent task id', res.id)

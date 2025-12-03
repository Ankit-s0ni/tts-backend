import sqlite3
from celery import Celery
DB='dev.db'
JOB_ID=2
conn=sqlite3.connect(DB)
c=conn.cursor()
c.execute('UPDATE jobs SET status=?, completed_chunks=?, s3_final_url=? WHERE id=?', ('queued',0,None,JOB_ID))
conn.commit()
conn.close()
app=Celery('tmp', broker='redis://127.0.0.1:6379/0')
res=app.send_task('backend.process_job', args=(JOB_ID,))
print('sent', res.id)

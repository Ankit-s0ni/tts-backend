import time
import os
import sqlite3
from celery import Celery

DB='dev.db'
JOB_ID=2
LOG_PATH=os.path.join('logs', f'worker_job_{JOB_ID}.log')
OUT_DIR='output'

app=Celery('tmp', broker='redis://127.0.0.1:6379/0')
res=app.send_task('backend.process_job', args=(JOB_ID,))
print('sent', res.id)

start=time.time()

def get_job():
    conn=sqlite3.connect(DB)
    c=conn.cursor()
    r=list(c.execute('SELECT id, text, status, s3_final_url, completed_chunks FROM jobs WHERE id=?', (JOB_ID,)))
    conn.close()
    return r[0] if r else None

while True:
    job=get_job()
    now=time.time()
    print('time', int(now-start), 's - job:', job)
    if os.path.exists(LOG_PATH):
        print('\n--- worker log tail ---')
        with open(LOG_PATH,'r',encoding='utf8') as f:
            data=f.read()
        print(data[-4000:])
    if os.path.isdir(OUT_DIR):
        print('output files:', os.listdir(OUT_DIR))
    if job and job[2] in ('completed','failed'):
        print('final status:', job[2])
        break
    if now-start > 120:
        print('timeout after 120s')
        break
    time.sleep(2)

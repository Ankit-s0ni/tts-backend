import sqlite3, time, os
from celery import Celery

DB='dev.db'
JOB_TEXT='Quick test job from script'

# insert test job
conn=sqlite3.connect(DB)
c=conn.cursor()
c.execute("INSERT INTO jobs (user_id, language, voice_id, text, include_alignments, status, created_at, updated_at) VALUES (?,?,?,?,?,?,datetime('now'),datetime('now'))", (None,'en','default',JOB_TEXT,False,'queued'))
job_id=c.lastrowid
conn.commit()
conn.close()
print('Inserted job', job_id)

# enqueue
app=Celery('tmp', broker='redis://127.0.0.1:6379/0')
res=app.send_task('backend.process_job', args=(job_id,))
print('Sent task id', res.id)

out_dir='output'
log_path=os.path.join('logs', f'worker_job_{job_id}.log')
start=time.time()
while True:
    conn=sqlite3.connect(DB)
    c=conn.cursor()
    r=list(c.execute('SELECT id, status, s3_final_url, completed_chunks FROM jobs WHERE id=?', (job_id,)))
    conn.close()
    print('status poll:', r)
    if os.path.exists(log_path):
        print('--- worker log tail ---')
        with open(log_path,'r',encoding='utf8') as f:
            print(f.read()[-4000:])
    if os.path.isdir(out_dir):
        files=os.listdir(out_dir)
        print('output files:', files)
    if r and r[0][1] in ('completed','failed'):
        print('final:', r)
        break
    if time.time()-start>120:
        print('timeout')
        break
    time.sleep(2)

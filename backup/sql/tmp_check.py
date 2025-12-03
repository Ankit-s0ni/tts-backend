import sqlite3, time, os
DB='dev.db'
JOB_ID=2

def print_job():
    conn=sqlite3.connect(DB)
    c=conn.cursor()
    r=list(c.execute('SELECT id, text, status, s3_final_url, completed_chunks FROM jobs WHERE id=?', (JOB_ID,)))
    print('job row:', r)
    conn.close()

for i in range(12):
    print('\n--- poll', i, '---')
    print_job()
    outdir='output'
    if os.path.exists(outdir):
        print('output files:', os.listdir(outdir))
    else:
        print('no output dir yet')
    logpath=os.path.join('logs', f'worker_job_{JOB_ID}.log')
    if os.path.exists(logpath):
        print('--- worker log tail ---')
        with open(logpath,'r',encoding='utf8') as f:
            data=f.read()
        print(data[-4000:])
    time.sleep(2)

import sqlite3, os, sys, textwrap
DB='dev.db'
JOB_ID=2
print('== Job row ==')
conn=sqlite3.connect(DB)
c=conn.cursor()
r=list(c.execute('SELECT id, text, status, s3_final_url, completed_chunks FROM jobs WHERE id=?', (JOB_ID,)))
print(r)
conn.close()
print('\n== Worker log tail ==')
logpath=os.path.join('logs', f'worker_job_{JOB_ID}.log')
if os.path.exists(logpath):
    with open(logpath,'r',encoding='utf8') as f:
        data=f.read()
    print(data[-4000:])
else:
    print('(no log file)')

print('\n== Output files ==')
out_dir='output'
if os.path.isdir(out_dir):
    for p in os.listdir(out_dir):
        try:
            print(p, os.path.getsize(os.path.join(out_dir,p)))
        except Exception:
            print(p)
else:
    print('(no output dir)')

print('\n== Celery processes ==')
try:
    import subprocess
    ps = subprocess.run(['powershell','-NoProfile','-Command', "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match 'celery') } | Select-Object ProcessId, CommandLine | Format-List"], capture_output=True, text=True)
    print(ps.stdout)
except Exception as e:
    print('failed to list processes:', e)

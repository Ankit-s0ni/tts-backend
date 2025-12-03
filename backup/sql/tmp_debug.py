import sqlite3, os
from app.utils.chunker import chunk_text
from app.config import settings
import httpx

DB='dev.db'
JOB_ID=2
conn=sqlite3.connect(DB)
c=conn.cursor()
r = list(c.execute('SELECT id, text FROM jobs WHERE id=?', (JOB_ID,)))
print('db row:', r)
if not r:
    raise SystemExit('job not found')
text = r[0][1] or ''
chunks = chunk_text(text, max_chars=500)
print('chunks:', len(chunks))
for i,ch in enumerate(chunks):
    print('chunk', i, repr(ch)[:80])

piper_url = str(settings.PIPER_URL).rstrip('/') or 'http://127.0.0.1:5000'
print('using Piper URL:', piper_url)
client = httpx.Client(timeout=30.0)
for i,ch in enumerate(chunks):
    resp = client.post(piper_url, json={'text': ch})
    print('chunk', i, 'status', resp.status_code, 'len', len(resp.content))
    if resp.status_code==200:
        tmpdir=os.path.join('tmp_debug_chunks')
        os.makedirs(tmpdir, exist_ok=True)
        p=os.path.join(tmpdir, f'chunk_{i}.wav')
        with open(p,'wb') as f:
            f.write(resp.content)
        print('wrote', p)

print('done')
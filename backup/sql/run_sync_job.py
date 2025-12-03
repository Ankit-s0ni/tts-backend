import os
import sqlite3
from celery_worker import process_job

BASE = os.path.dirname(__file__)
DB = os.path.join(BASE, 'dev.db')
TEXT_PATH = os.path.abspath(os.path.join(BASE, '..', 'two_page.txt'))

if not os.path.exists(TEXT_PATH):
    print('two_page.txt not found at', TEXT_PATH)
    raise SystemExit(1)

text = open(TEXT_PATH, 'r', encoding='utf8').read()

conn = sqlite3.connect(DB)
cur = conn.cursor()
# create jobs table if missing (very defensive)
cur.execute("""
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    language TEXT,
    voice_id TEXT,
    text TEXT,
    include_alignments INTEGER DEFAULT 0,
    original_filename TEXT,
    total_chunks INTEGER DEFAULT 0,
    completed_chunks INTEGER DEFAULT 0,
    status TEXT DEFAULT 'queued',
    s3_final_url TEXT,
    alignments_s3_url TEXT,
    created_at TEXT,
    updated_at TEXT
)
""")
conn.commit()

cur.execute("INSERT INTO jobs (user_id, language, voice_id, text, include_alignments, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))",
            (1, 'en_US', 'en_US-lessac-medium', text, 0, 'queued'))
job_id = cur.lastrowid
conn.commit()
conn.close()

print('Created job', job_id, ' — running process_job synchronously...')
res = process_job(job_id)
print('process_job result:', res)
if res.get('output'):
    print('Output file:', res.get('output'))

import sqlite3
conn=sqlite3.connect('backend/dev.db')
cur=conn.cursor()
print('JOBS:')
for r in cur.execute('select id,user_id,status,created_at,s3_final_url from jobs'):
    print(r)
conn.close()

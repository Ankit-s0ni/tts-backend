import sqlite3, os
db='backend/dev.db'
if os.path.exists(db):
    conn=sqlite3.connect(db)
    cur=conn.cursor()
    print('USERS:')
    for r in cur.execute('select id,email,created_at from users'):
        print(r)
    print('\nJOBS:')
    for r in cur.execute('select id,user_id,status,created_at from jobs'):
        print(r)
    conn.close()
else:
    print('DB not found', db)

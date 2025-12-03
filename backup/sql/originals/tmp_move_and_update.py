import os, sqlite3, shutil

# Paths
cwd = os.getcwd()
# source path observed earlier
src = os.path.join(cwd, 'backend', 'output', 'job_2.wav')
dst_dir = os.path.join(cwd, 'output')
dst = os.path.join(dst_dir, 'job_2.wav')
DB='dev.db'

print('cwd:', cwd)
print('src:', src)
print('dst:', dst)

if not os.path.exists(src):
    print('Source file does not exist:', src)
else:
    os.makedirs(dst_dir, exist_ok=True)
    shutil.move(src, dst)
    print('Moved file to', dst)

# Update DB s3_final_url for job 2
conn=sqlite3.connect(DB)
c=conn.cursor()
newpath = os.path.abspath(dst)
c.execute('UPDATE jobs SET s3_final_url=?, updated_at=datetime("now") WHERE id=?', (newpath, 2))
conn.commit()
print('Updated DB for job 2 with', newpath)
# show row
r=list(c.execute('SELECT id, status, s3_final_url FROM jobs WHERE id=2'))
print(r)
conn.close()

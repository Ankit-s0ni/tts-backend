import pymongo

client = pymongo.MongoClient("mongodb+srv://voicetexta:voicetexta@cluster0.dvq4rui.mongodb.net/?appName=Cluster0")
db = client["tts_production"]

# Check the latest job
job = db.jobs.find_one(sort=[("created_at", -1)])
print(f"Latest job user_id: {job.get('user_id')}")
print(f"Job ID: {job.get('job_id')}")
print(f"Job created_at: {job.get('created_at')}")

# Check all unique user_ids
user_ids = db.jobs.distinct("user_id")
print(f"\nUnique user_ids in database: {user_ids}")
print(f"Total jobs: {db.jobs.count_documents({})}")

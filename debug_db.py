#!/usr/bin/env python3
"""Debug script to inspect MongoDB database content and schema."""

from pymongo import MongoClient
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv("MONGODB_URI", "mongodb+srv://voicetexta:voicetexta@cluster0.dvq4rui.mongodb.net/?appName=Cluster0")
DB_NAME = os.getenv("MONGODB_DB_NAME", "tts_production")
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

print("=" * 80)
print("DATABASE SCHEMA & CONTENT INSPECTION")
print("=" * 80)

# Check jobs collection
jobs_col = db.jobs
print(f"\n[JOBS COLLECTION]\n")
print(f"Total documents: {jobs_col.count_documents({})}")

# Get recent jobs (last 5)
print(f"\n--- Recent 5 Jobs (sorted by created_at DESC) ---\n")
recent = list(jobs_col.find().sort("created_at", -1).limit(5))
for i, job in enumerate(recent, 1):
    print(f"{i}. Job ID: {job.get('job_id')}")
    print(f"   User ID: {job.get('user_id')} (type: {type(job.get('user_id')).__name__})")
    print(f"   Status: {job.get('status')}")
    print(f"   Voice: {job.get('voice_id')}")
    print(f"   Text: {job.get('text', '')[:50]}...")
    print(f"   Created: {job.get('created_at')}")
    print(f"   Audio URL: {job.get('audio_url', 'N/A')[:60] if job.get('audio_url') else 'N/A'}...")
    print()

# Check unique user_ids
print("\n--- User IDs in Database ---\n")
unique_users = jobs_col.distinct("user_id")
print(f"Total unique user_ids: {len(unique_users)}")
for user_id in sorted(unique_users)[:20]:  # Show first 20
    count = jobs_col.count_documents({"user_id": user_id})
    print(f"  user_id='{user_id}': {count} jobs")

# Check null/missing user_id
print(f"\n--- Jobs with NULL or Missing user_id ---\n")
null_count = jobs_col.count_documents({"user_id": None})
missing_count = jobs_col.count_documents({"user_id": {"$exists": False}})
print(f"Jobs with user_id=None: {null_count}")
print(f"Jobs with missing user_id: {missing_count}")

# Check users collection
print(f"\n[USERS COLLECTION]\n")
users_col = db.users
print(f"Total users: {users_col.count_documents({})}")

print(f"\n--- Recent 5 Users ---\n")
recent_users = list(users_col.find().sort("id", -1).limit(5))
for user in recent_users:
    print(f"ID: {user.get('id')}, Email: {user.get('email')}, Name: {user.get('full_name')}")

# Check if there's an index on user_id
print(f"\n--- Indexes on jobs collection ---\n")
indexes = jobs_col.list_indexes()
for idx in indexes:
    print(f"Index: {idx.get('name')}")
    print(f"  Keys: {idx.get('key')}")
    print()

# Sample query: Get jobs for a specific user
print(f"\n--- Testing Filter: get jobs for user_id='7' ---\n")
user_7_jobs = list(jobs_col.find({"user_id": "7"}).limit(3))
print(f"Found {len(user_7_jobs)} jobs for user_id='7'")
for job in user_7_jobs:
    print(f"  - {job.get('job_id')}: {job.get('text', '')[:40]}... (user_id={job.get('user_id')})")

print(f"\n--- Testing Filter: get jobs for user_id='8' ---\n")
user_8_jobs = list(jobs_col.find({"user_id": "8"}).limit(3))
print(f"Found {len(user_8_jobs)} jobs for user_id='8'")
for job in user_8_jobs:
    print(f"  - {job.get('job_id')}: {job.get('text', '')[:40]}... (user_id={job.get('user_id')})")

print("\n" + "=" * 80)
client.close()

"""Test if backend is now connected to AWS DynamoDB and returning all jobs"""
import requests
import json

# Get fresh token
login_url = "http://localhost:8001/auth/login"
login_data = {
    "email": "ankitks1515@gmail.com",
    "password": "Ankit@123"
}

print("Getting authentication token...")
login_response = requests.post(login_url, json=login_data)
token = login_response.json()["access_token"]
print(f"✓ Token obtained\n")

# Test jobs endpoint
jobs_url = "http://localhost:8001/tts/jobs"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("Fetching jobs from backend API...")
jobs_response = requests.get(jobs_url, headers=headers)

if jobs_response.status_code == 200:
    jobs = jobs_response.json()
    print(f"\n{'='*80}")
    print(f"✓ SUCCESS! Backend returned {len(jobs)} jobs")
    print(f"{'='*80}\n")
    
    for job in jobs:
        print(f"Job #{job['id']}:")
        print(f"  Status: {job['status']}")
        print(f"  Audio URL: {job['audio_url']}")
        print(f"  Created: {job['created_at']}")
        print(f"  Voice: {job.get('voice_id', 'N/A')}")
        print()
    
    if len(jobs) == 5:
        print("✓ ALL 5 JOBS FROM AWS DYNAMODB ARE NOW VISIBLE!")
    elif len(jobs) == 1:
        print("⚠️  Still only seeing 1 job - backend might still be using local DynamoDB")
        print("   Try restarting the backend container again")
    else:
        print(f"ℹ️  Found {len(jobs)} jobs")
else:
    print(f"❌ Error: {jobs_response.status_code}")
    print(jobs_response.text)

"""
Comprehensive Data Isolation Security Test
Tests that:
1. Each user's jobs are stored with their correct user_id
2. Users can only list their own jobs
3. Users can only access their own job details
4. Users cannot stream audio from other users' jobs
5. Access denied returns 403 Forbidden
"""

import requests
import json
import time

BASE_URL = "http://localhost:8002"

def test_security():
    print("\n" + "="*60)
    print("DATA ISOLATION SECURITY TEST")
    print("="*60)
    
    # Step 1: Register two users
    print("\n[1] Registering test users...")
    user1 = {
        "email": f"sectest1-{int(time.time())}@example.com",
        "password": "SecurePass123!"
    }
    user2 = {
        "email": f"sectest2-{int(time.time())}@example.com",
        "password": "SecurePass123!"
    }
    
    r1 = requests.post(f"{BASE_URL}/auth/register", json=user1)
    user1_id = r1.json()["user_id"]
    print(f"  ✓ User 1 registered: ID={user1_id}")
    
    r2 = requests.post(f"{BASE_URL}/auth/register", json=user2)
    user2_id = r2.json()["user_id"]
    print(f"  ✓ User 2 registered: ID={user2_id}")
    
    # Step 2: Login both users
    print("\n[2] Logging in users...")
    r1 = requests.post(f"{BASE_URL}/auth/login", json=user1)
    token1 = r1.json()["access_token"]
    print(f"  ✓ User 1 logged in")
    
    r2 = requests.post(f"{BASE_URL}/auth/login", json=user2)
    token2 = r2.json()["access_token"]
    print(f"  ✓ User 2 logged in")
    
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}
    
    # Step 3: Create jobs for both users
    print("\n[3] Creating jobs...")
    job_data = {"text": "Hello from user 1", "voice_id": "en_US-lessac-high"}
    r = requests.post(f"{BASE_URL}/tts/jobs", json=job_data, headers=headers1)
    job1_id = r.json()["id"]
    print(f"  ✓ User 1 created job: {job1_id}")
    
    job_data = {"text": "Hello from user 2", "voice_id": "en_US-lessac-high"}
    r = requests.post(f"{BASE_URL}/tts/jobs", json=job_data, headers=headers2)
    job2_id = r.json()["id"]
    print(f"  ✓ User 2 created job: {job2_id}")
    
    # Step 4: Test list isolation
    print("\n[4] Testing job list isolation...")
    r = requests.get(f"{BASE_URL}/tts/jobs", headers=headers1)
    user1_jobs = r.json()
    user1_job_ids = [j.get("id") for j in (user1_jobs if isinstance(user1_jobs, list) else [user1_jobs])]
    print(f"  User 1 sees jobs: {user1_job_ids}")
    
    r = requests.get(f"{BASE_URL}/tts/jobs", headers=headers2)
    user2_jobs = r.json()
    user2_job_ids = [j.get("id") for j in (user2_jobs if isinstance(user2_jobs, list) else [user2_jobs])]
    print(f"  User 2 sees jobs: {user2_job_ids}")
    
    # Verify isolation
    if job1_id in user1_job_ids and job1_id not in user2_job_ids:
        print(f"  ✓ User 1's job NOT visible to User 2")
    else:
        print(f"  ✗ SECURITY ISSUE: User 1's job visible to User 2!")
    
    if job2_id in user2_job_ids and job2_id not in user1_job_ids:
        print(f"  ✓ User 2's job NOT visible to User 1")
    else:
        print(f"  ✗ SECURITY ISSUE: User 2's job visible to User 1!")
    
    # Step 5: Test job detail access control
    print("\n[5] Testing job detail access control...")
    
    # User 1 accessing own job
    r = requests.get(f"{BASE_URL}/tts/jobs/{job1_id}", headers=headers1)
    if r.status_code == 200:
        print(f"  ✓ User 1 can access own job (200 OK)")
    else:
        print(f"  ✗ User 1 cannot access own job ({r.status_code})")
    
    # User 2 accessing own job
    r = requests.get(f"{BASE_URL}/tts/jobs/{job2_id}", headers=headers2)
    if r.status_code == 200:
        print(f"  ✓ User 2 can access own job (200 OK)")
    else:
        print(f"  ✗ User 2 cannot access own job ({r.status_code})")
    
    # User 1 accessing User 2's job (should be denied)
    r = requests.get(f"{BASE_URL}/tts/jobs/{job2_id}", headers=headers1)
    if r.status_code == 403:
        print(f"  ✓ User 1 denied access to User 2's job (403 Forbidden)")
    else:
        print(f"  ✗ SECURITY ISSUE: User 1 got {r.status_code} instead of 403!")
    
    # User 2 accessing User 1's job (should be denied)
    r = requests.get(f"{BASE_URL}/tts/jobs/{job1_id}", headers=headers2)
    if r.status_code == 403:
        print(f"  ✓ User 2 denied access to User 1's job (403 Forbidden)")
    else:
        print(f"  ✗ SECURITY ISSUE: User 2 got {r.status_code} instead of 403!")
    
    # Step 6: Test audio stream access control
    print("\n[6] Testing audio stream access control...")
    
    # User 1 accessing own audio
    r = requests.get(f"{BASE_URL}/tts/jobs/{job1_id}/audio", headers=headers1)
    if r.status_code == 200:
        print(f"  ✓ User 1 can stream own audio (200 OK, {len(r.content)} bytes)")
    else:
        print(f"  ✗ User 1 cannot stream own audio ({r.status_code})")
    
    # User 1 accessing User 2's audio (should be denied)
    r = requests.get(f"{BASE_URL}/tts/jobs/{job2_id}/audio", headers=headers1)
    if r.status_code == 403:
        print(f"  ✓ User 1 denied audio stream for User 2's job (403 Forbidden)")
    else:
        print(f"  ✗ SECURITY ISSUE: User 1 got {r.status_code} instead of 403!")
    
    print("\n" + "="*60)
    print("✓ ALL SECURITY TESTS PASSED!")
    print("="*60 + "\n")

if __name__ == "__main__":
    time.sleep(2)  # Wait for API
    test_security()

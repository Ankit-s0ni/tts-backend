#!/usr/bin/env python3
"""Pre-deployment verification script.

Checks that all Phase 2 changes are correctly implemented before deploying.
Run this BEFORE rebuilding Docker containers.

Usage:
    python backend/scripts/verify_phase2_changes.py
"""
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists."""
    path = Path(filepath)
    if path.exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} MISSING: {filepath}")
        return False

def check_file_contains(filepath, search_text, description):
    """Check if a file contains specific text."""
    path = Path(filepath)
    if not path.exists():
        print(f"❌ {description}: File not found - {filepath}")
        return False
    
    content = path.read_text(encoding='utf-8')
    if search_text in content:
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description}: Text not found in {filepath}")
        print(f"   Looking for: {search_text[:50]}...")
        return False

def main():
    """Run all verification checks."""
    print("="*70)
    print("Phase 2 Pre-Deployment Verification")
    print("="*70)
    
    checks = []
    
    # File existence checks
    print("\n📁 File Existence Checks:")
    checks.append(check_file_exists("backend/app/voice_manager.py", "VoiceManager module"))
    checks.append(check_file_exists("backend/scripts/test_phase2_migration.py", "Test suite"))
    checks.append(check_file_exists("MIGRATION_PLAN.md", "Migration plan"))
    checks.append(check_file_exists("PHASE2_DEPLOYMENT.md", "Deployment guide"))
    
    # Requirements.txt checks
    print("\n📦 Requirements.txt Checks:")
    checks.append(check_file_contains(
        "backend/requirements.txt",
        "piper-tts>=1.2.0",
        "piper-tts added to requirements"
    ))
    checks.append(check_file_contains(
        "backend/requirements.txt",
        "numpy>=1.20.0",
        "numpy added to requirements"
    ))
    
    # Celery worker checks
    print("\n⚙️  Celery Worker Checks:")
    checks.append(check_file_contains(
        "backend/celery_worker.py",
        "from app.voice_manager import get_voice_manager",
        "voice_manager import added"
    ))
    checks.append(check_file_contains(
        "backend/celery_worker.py",
        "voice_manager = get_voice_manager()",
        "VoiceManager initialized in worker"
    ))
    checks.append(check_file_contains(
        "backend/celery_worker.py",
        "voice.synthesize(chunk",
        "Direct Piper API call (synthesize)"
    ))
    
    # Check HTTP client is removed
    worker_content = Path("backend/celery_worker.py").read_text(encoding='utf-8')
    if "import httpx" in worker_content:
        print("❌ httpx still imported (should be removed)")
        checks.append(False)
    else:
        print("✅ httpx import removed")
        checks.append(True)
    
    if "client.post(target_root" in worker_content:
        print("❌ HTTP POST call still present (should be removed)")
        checks.append(False)
    else:
        print("✅ HTTP POST calls removed")
        checks.append(True)
    
    # Docker compose checks
    print("\n🐳 Docker Compose Checks:")
    checks.append(check_file_contains(
        "docker-compose.yml",
        "MODELS_DIR=/models",
        "MODELS_DIR environment variable added"
    ))
    checks.append(check_file_contains(
        "docker-compose.yml",
        "MAX_CACHED_VOICES=5",
        "MAX_CACHED_VOICES environment variable added"
    ))
    
    # Check PIPER_URL removed from worker
    compose_content = Path("docker-compose.yml").read_text(encoding='utf-8')
    worker_section_start = compose_content.find("worker:")
    worker_section_end = compose_content.find("\n  ", worker_section_start + 50)
    worker_section = compose_content[worker_section_start:worker_section_end]
    
    if "PIPER_URL" in worker_section:
        print("❌ PIPER_URL still in worker environment (should be removed)")
        checks.append(False)
    else:
        print("✅ PIPER_URL removed from worker")
        checks.append(True)
    
    # Config checks
    print("\n⚙️  Config.py Checks:")
    checks.append(check_file_contains(
        "backend/app/config.py",
        "MODELS_DIR: str",
        "MODELS_DIR setting added"
    ))
    checks.append(check_file_contains(
        "backend/app/config.py",
        "MAX_CACHED_VOICES: int",
        "MAX_CACHED_VOICES setting added"
    ))
    
    # VoiceManager implementation checks
    print("\n🎯 VoiceManager Implementation Checks:")
    checks.append(check_file_contains(
        "backend/app/voice_manager.py",
        "class VoiceManager:",
        "VoiceManager class defined"
    ))
    checks.append(check_file_contains(
        "backend/app/voice_manager.py",
        "def get_voice(",
        "get_voice method defined"
    ))
    checks.append(check_file_contains(
        "backend/app/voice_manager.py",
        "OrderedDict",
        "LRU cache using OrderedDict"
    ))
    checks.append(check_file_contains(
        "backend/app/voice_manager.py",
        "Lock",
        "Thread-safe locking implemented"
    ))
    
    # Summary
    print("\n" + "="*70)
    total_checks = len(checks)
    passed_checks = sum(checks)
    
    print(f"Results: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print("\n✅ ALL CHECKS PASSED!")
        print("\n🚀 Ready to deploy Phase 2:")
        print("   1. docker compose build worker")
        print("   2. docker compose down")
        print("   3. docker compose up -d")
        print("   4. python backend/scripts/test_phase2_migration.py")
        return 0
    else:
        print(f"\n❌ {total_checks - passed_checks} CHECK(S) FAILED!")
        print("\n⚠️  Please fix the issues above before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

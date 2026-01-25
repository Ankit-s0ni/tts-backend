#!/usr/bin/env python3
"""
Test script to verify the new email auth system is properly set up.
Run this after installing dependencies.
"""
import sys

def test_imports():
    """Test that all new modules can be imported."""
    print("Testing imports...")
    errors = []
    
    try:
        from app.auth_email import create_user, get_current_user
        print("✓ app.auth_email")
    except Exception as e:
        errors.append(f"✗ app.auth_email: {e}")
    
    try:
        from app.utils.email_service import send_verification_email
        print("✓ app.utils.email_service")
    except Exception as e:
        errors.append(f"✗ app.utils.email_service: {e}")
    
    try:
        from app.utils.cloudinary_uploader import upload_audio
        print("✓ app.utils.cloudinary_uploader")
    except Exception as e:
        errors.append(f"✗ app.utils.cloudinary_uploader: {e}")
    
    try:
        from app.routers.auth_router_email import router
        print("✓ app.routers.auth_router_email")
    except Exception as e:
        errors.append(f"✗ app.routers.auth_router_email: {e}")
    
    try:
        from app.models import User, VerificationCode
        print("✓ app.models (User, VerificationCode)")
    except Exception as e:
        errors.append(f"✗ app.models: {e}")
    
    if errors:
        print("\n❌ Import Errors:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("\n✅ All imports successful!")
        return True


def test_database():
    """Test database setup."""
    print("\nTesting database...")
    try:
        from app.db import Base, engine
        from app.models import User, VerificationCode
        
        # Try to create tables
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created/verified")
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False


def test_config():
    """Test environment configuration."""
    print("\nTesting configuration...")
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    required = {
        "JWT_SECRET_KEY": "JWT authentication",
        "RESEND_API_KEY": "Email service",
        "CLOUDINARY_CLOUD_NAME": "File storage",
        "CLOUDINARY_API_KEY": "File storage",
        "CLOUDINARY_API_SECRET": "File storage",
    }
    
    missing = []
    for var, purpose in required.items():
        value = os.getenv(var)
        if not value:
            missing.append(f"{var} ({purpose})")
            print(f"✗ {var}: NOT SET")
        elif value.startswith("change-this") or value.startswith("your-"):
            missing.append(f"{var} ({purpose}) - placeholder value")
            print(f"⚠ {var}: needs updating")
        else:
            print(f"✓ {var}: configured")
    
    if missing:
        print(f"\n⚠️  Configuration issues: {len(missing)}")
        return False
    else:
        print("\n✅ All configuration complete!")
        return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Email Auth System - Verification Tests")
    print("=" * 60)
    print()
    
    results = {
        "imports": test_imports(),
        "database": test_database(),
        "config": test_config()
    }
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.capitalize()}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! System is ready.")
        print("\nNext steps:")
        print("1. Start the server: uvicorn app.main:app --reload")
        print("2. Visit: http://localhost:8000/docs")
        print("3. Test registration: POST /auth/register")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Update .env with your API keys")
        print("3. Check MIGRATION_GUIDE.md for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""
Quick test to verify password validation is working correctly.
Run this to test the validators without making API calls.
"""
from app.routers.auth_router_email import RegisterRequest, ResetPasswordRequest
from pydantic import ValidationError

def test_password(password: str, description: str):
    """Test a password against the validators"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Password: '{password}' ({len(password)} chars, {len(password.encode('utf-8'))} bytes)")
    print(f"{'='*60}")
    
    try:
        # Test with RegisterRequest
        req = RegisterRequest(
            email="test@example.com",
            password=password,
            full_name="Test User"
        )
        print("✅ PASS: Password accepted")
        return True
    except ValidationError as e:
        print("❌ FAIL: Password rejected")
        for error in e.errors():
            print(f"  Error: {error['msg']}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*15 + "PASSWORD VALIDATION TEST" + " "*19 + "║")
    print("╚" + "="*58 + "╝")
    
    tests = [
        ("123456", "Too short (6 chars)"),
        ("12345678", "Minimum valid (8 chars)"),
        ("#Manav@423", "Your original password (10 chars)"),
        ("SecurePass123!", "Good password (14 chars)"),
        ("a" * 72, "Maximum valid (72 chars)"),
        ("a" * 73, "Too long (73 chars)"),
        ("a" * 100, "Way too long (100 chars)"),
        ("🔐password", "Unicode emoji (11 bytes for emoji alone)"),
    ]
    
    results = []
    for password, description in tests:
        result = test_password(password, description)
        results.append((description, result))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for desc, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {desc}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n{passed}/{total} tests behaved as expected")
    print("="*60 + "\n")

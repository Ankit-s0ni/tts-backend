"""
Comprehensive test of the email authentication flow.
Tests: registration, verification, login, password reset
"""
import requests
import time
from typing import Dict, Any

# API Configuration
BASE_URL = "https://api.voicetexta.com"
# BASE_URL = "http://localhost:8000"  # Uncomment for local testing

# Test user data
TEST_EMAIL = f"test_{int(time.time())}@example.com"
TEST_PASSWORD = "#Manav@423"
TEST_NAME = "Test User"


def print_section(title: str):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(success: bool, message: str, data: Any = None):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if data:
        print(f"  Data: {data}")


def test_registration() -> Dict[str, Any]:
    """Test user registration"""
    print_section("1. USER REGISTRATION")
    
    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": TEST_NAME
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        
        if response.status_code == 201:
            data = response.json()
            print_result(True, "Registration successful", data)
            return {"success": True, "data": data}
        else:
            print_result(False, f"Registration failed: {response.status_code}", response.json())
            return {"success": False, "error": response.json()}
    except Exception as e:
        print_result(False, f"Registration exception: {str(e)}")
        return {"success": False, "error": str(e)}


def test_login_without_verification() -> Dict[str, Any]:
    """Test login before email verification"""
    print_section("2. LOGIN WITHOUT VERIFICATION")
    
    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Login successful (user can login without verification)", data)
            return {"success": True, "data": data, "token": data.get("access_token")}
        else:
            print_result(False, f"Login blocked: {response.status_code}", response.json())
            return {"success": False, "error": response.json()}
    except Exception as e:
        print_result(False, f"Login exception: {str(e)}")
        return {"success": False, "error": str(e)}


def test_email_verification(code: str) -> Dict[str, Any]:
    """Test email verification"""
    print_section("3. EMAIL VERIFICATION")
    
    payload = {
        "email": TEST_EMAIL,
        "code": code
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/verify-email", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Email verification successful", data)
            return {"success": True, "data": data, "token": data.get("access_token")}
        else:
            print_result(False, f"Verification failed: {response.status_code}", response.json())
            return {"success": False, "error": response.json()}
    except Exception as e:
        print_result(False, f"Verification exception: {str(e)}")
        return {"success": False, "error": str(e)}


def test_get_profile(token: str) -> Dict[str, Any]:
    """Test getting user profile"""
    print_section("4. GET USER PROFILE")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Profile retrieved", data)
            return {"success": True, "data": data}
        else:
            print_result(False, f"Profile retrieval failed: {response.status_code}", response.json())
            return {"success": False, "error": response.json()}
    except Exception as e:
        print_result(False, f"Profile exception: {str(e)}")
        return {"success": False, "error": str(e)}


def test_login_after_verification() -> Dict[str, Any]:
    """Test login after email verification"""
    print_section("5. LOGIN AFTER VERIFICATION")
    
    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Login successful", data)
            return {"success": True, "data": data, "token": data.get("access_token")}
        else:
            print_result(False, f"Login failed: {response.status_code}", response.json())
            return {"success": False, "error": response.json()}
    except Exception as e:
        print_result(False, f"Login exception: {str(e)}")
        return {"success": False, "error": str(e)}


def test_password_reset_request() -> Dict[str, Any]:
    """Test password reset request"""
    print_section("6. PASSWORD RESET REQUEST")
    
    payload = {"email": TEST_EMAIL}
    
    try:
        response = requests.post(f"{BASE_URL}/auth/forgot-password", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Password reset requested", data)
            return {"success": True, "data": data}
        else:
            print_result(False, f"Reset request failed: {response.status_code}", response.json())
            return {"success": False, "error": response.json()}
    except Exception as e:
        print_result(False, f"Reset request exception: {str(e)}")
        return {"success": False, "error": str(e)}


def test_password_reset(code: str, new_password: str) -> Dict[str, Any]:
    """Test password reset with code"""
    print_section("7. PASSWORD RESET")
    
    payload = {
        "email": TEST_EMAIL,
        "code": code,
        "new_password": new_password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/reset-password", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Password reset successful", data)
            return {"success": True, "data": data}
        else:
            print_result(False, f"Password reset failed: {response.status_code}", response.json())
            return {"success": False, "error": response.json()}
    except Exception as e:
        print_result(False, f"Password reset exception: {str(e)}")
        return {"success": False, "error": str(e)}


def test_login_with_new_password(new_password: str) -> Dict[str, Any]:
    """Test login with new password"""
    print_section("8. LOGIN WITH NEW PASSWORD")
    
    payload = {
        "email": TEST_EMAIL,
        "password": new_password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print_result(True, "Login with new password successful", data)
            return {"success": True, "data": data}
        else:
            print_result(False, f"Login failed: {response.status_code}", response.json())
            return {"success": False, "error": response.json()}
    except Exception as e:
        print_result(False, f"Login exception: {str(e)}")
        return {"success": False, "error": str(e)}


def test_password_length_validation():
    """Test password length validation (72 byte limit)"""
    print_section("9. PASSWORD LENGTH VALIDATION")
    
    # Create a password longer than 72 bytes
    long_password = "a" * 73
    
    payload = {
        "email": f"longpass_{int(time.time())}@example.com",
        "password": long_password,
        "full_name": "Long Password Test"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        
        if response.status_code == 400:
            data = response.json()
            if "too long" in data.get("detail", "").lower():
                print_result(True, "Password length validation working", data)
                return {"success": True}
            else:
                print_result(False, "Wrong error message", data)
                return {"success": False}
        else:
            print_result(False, f"Should have rejected long password: {response.status_code}", response.json())
            return {"success": False}
    except Exception as e:
        print_result(False, f"Test exception: {str(e)}")
        return {"success": False}


def run_full_test():
    """Run complete authentication flow test"""
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "AUTHENTICATION FLOW TEST" + " " * 29 + "║")
    print("╚" + "=" * 68 + "╝")
    print(f"\nTesting with email: {TEST_EMAIL}")
    print(f"Testing with password: {TEST_PASSWORD}")
    
    results = []
    
    # 1. Test registration
    reg_result = test_registration()
    results.append(("Registration", reg_result["success"]))
    
    if not reg_result["success"]:
        print("\n❌ Registration failed. Cannot continue tests.")
        return
    
    # 2. Test login without verification
    login_no_verify = test_login_without_verification()
    results.append(("Login without verification", login_no_verify["success"]))
    
    # Manual verification code entry
    print_section("VERIFICATION CODE REQUIRED")
    print("⚠️  Please check your email and enter the verification code.")
    print(f"   Email: {TEST_EMAIL}")
    verification_code = input("   Enter verification code: ").strip()
    
    if not verification_code:
        print("\n❌ No verification code provided. Skipping remaining tests.")
        return
    
    # 3. Test email verification
    verify_result = test_email_verification(verification_code)
    results.append(("Email verification", verify_result["success"]))
    
    if verify_result["success"]:
        token = verify_result.get("token")
        
        # 4. Test get profile
        profile_result = test_get_profile(token)
        results.append(("Get profile", profile_result["success"]))
        
        # 5. Test login after verification
        login_after = test_login_after_verification()
        results.append(("Login after verification", login_after["success"]))
    
    # 6. Test password reset request
    reset_req = test_password_reset_request()
    results.append(("Password reset request", reset_req["success"]))
    
    if reset_req["success"]:
        print_section("PASSWORD RESET CODE REQUIRED")
        print("⚠️  Please check your email and enter the password reset code.")
        reset_code = input("   Enter reset code: ").strip()
        
        if reset_code:
            new_password = "#NewPassword@789"
            
            # 7. Test password reset
            reset_result = test_password_reset(reset_code, new_password)
            results.append(("Password reset", reset_result["success"]))
            
            if reset_result["success"]:
                # 8. Test login with new password
                new_login = test_login_with_new_password(new_password)
                results.append(("Login with new password", new_login["success"]))
    
    # 9. Test password length validation
    length_result = test_password_length_validation()
    results.append(("Password length validation", length_result["success"]))
    
    # Summary
    print_section("TEST SUMMARY")
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'=' * 70}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    run_full_test()

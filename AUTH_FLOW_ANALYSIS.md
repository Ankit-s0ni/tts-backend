# Authentication Flow Analysis

## Overview
Complete analysis of the email-based authentication system.

## Components

### 1. **Database Models** (`app/models.py`)
- ✅ **User Model**: Properly defined with all required fields
  - `id`: Primary key
  - `email`: Unique, indexed
  - `hashed_password`: Bcrypt hashed
  - `full_name`: Optional
  - `is_active`: Default True
  - `is_verified`: Default False
  - `created_at`, `updated_at`: Timestamps

- ✅ **VerificationCode Model**: Properly defined
  - `email`: Indexed for fast lookup
  - `code`: 6-digit verification code
  - `code_type`: "email_verification" or "password_reset"
  - `is_used`: Prevents code reuse
  - `expires_at`: 15-minute expiration
  - `created_at`: Timestamp

### 2. **Core Authentication** (`app/auth_email.py`)

#### Password Hashing
- ✅ Uses bcrypt via passlib
- ✅ Auto-truncation enabled (`bcrypt__truncate_error=False`)
- ⚠️ **Issue**: 72-byte limit error still occurs

#### JWT Configuration
- ✅ Secret key from environment (`JWT_SECRET_KEY`)
- ✅ 7-day token expiration
- ✅ HS256 algorithm

#### Key Functions
1. ✅ `verify_password()`: Validates password against hash
2. ✅ `get_password_hash()`: Hashes passwords
3. ✅ `create_access_token()`: Generates JWT tokens
4. ✅ `generate_verification_code()`: Creates 6-digit codes
5. ✅ `create_verification_code()`: Stores codes in DB with expiration
6. ✅ `verify_code()`: Validates and marks codes as used
7. ✅ `authenticate_user()`: Email/password authentication
8. ✅ `get_current_user()`: Extracts user from JWT token
9. ✅ `get_current_verified_user()`: Ensures email is verified
10. ✅ `create_user()`: Creates new users

### 3. **API Endpoints** (`app/routers/auth_router_email.py`)

#### Registration Flow
**POST /auth/register**
```
1. Validate password length (72 bytes)
2. Create user in database
3. Generate verification code
4. Send verification email
5. Return success message
```
- ✅ Email uniqueness check
- ✅ Password validation
- ✅ Error handling
- ⚠️ **Potential Issue**: Password validation method might not be called properly

#### Email Verification Flow
**POST /auth/verify-email**
```
1. Verify code validity
2. Check code expiration
3. Mark user as verified
4. Send welcome email
5. Return access token
```
- ✅ Code validation
- ✅ Expiration check
- ✅ User status update
- ✅ Token generation

**POST /auth/resend-verification-code**
```
1. Check if user exists
2. Invalidate old codes
3. Generate new code
4. Send email
```
- ✅ Prevents enumeration (same response for existing/non-existing emails)
- ✅ Code invalidation

#### Login Flow
**POST /auth/login**
```
1. Authenticate user (email + password)
2. Check if user is active
3. Generate access token
4. Return token
```
- ✅ Password verification
- ✅ Active user check
- ⚠️ **Note**: Users can login before email verification
  - This is intentional but should be documented

#### Password Reset Flow
**POST /auth/forgot-password**
```
1. Find user by email
2. Generate reset code
3. Send reset email
4. Return generic message
```
- ✅ Prevents email enumeration
- ✅ Code generation

**POST /auth/reset-password**
```
1. Validate password length
2. Verify reset code
3. Update user password
4. Return success
```
- ✅ Code validation
- ✅ Password hashing
- ✅ Password length validation

#### User Profile
**GET /auth/me**
```
Requires: Valid JWT token
Returns: User profile data
```
- ✅ Token validation
- ✅ User data serialization

**GET /users/me/profile**
```
Requires: Valid JWT token + verified email
Returns: User profile data
```
- ✅ Verification check
- ✅ Token validation

### 4. **Email Service** (`app/utils/email_service.py`)

#### Configuration
- ✅ Uses Resend API
- ✅ API key from environment (`RESEND_API_KEY`)
- ✅ Professional HTML email templates

#### Email Types
1. ✅ **Verification Email**: 6-digit code, 15-min expiry
2. ✅ **Password Reset Email**: 6-digit code, 15-min expiry
3. ✅ **Welcome Email**: Sent after verification

#### Error Handling
- ✅ Graceful failure (logs but doesn't block)
- ✅ Returns boolean success status

## Issues Found

### 🔴 Critical Issues

#### 1. Password Validation Not Properly Executed
**Location**: `auth_router_email.py` - `register()` and `reset_password()`

**Problem**: The `validate_password_length()` method is defined but might not raise exceptions properly.

**Current Code**:
```python
class RegisterRequest(BaseModel):
    def validate_password_length(self):
        if len(self.password.encode('utf-8')) > 72:
            raise ValueError("Password is too long. Maximum length is 72 bytes.")
        return self.password
```

**Issue**: This is a custom method, not a Pydantic validator. It needs to be called, but might not work as expected.

**Solution**: Use Pydantic's `@field_validator` decorator instead:
```python
from pydantic import field_validator

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    
    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password is too long. Maximum length is 72 bytes.')
        return v
```

### 🟡 Medium Issues

#### 2. bcrypt Configuration Might Not Work
**Location**: `auth_email.py`

**Current**:
```python
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=False
)
```

**Issue**: The parameter name might be incorrect for the version of passlib being used.

**Better Approach**: Pre-validate passwords before hashing

#### 3. Login Without Email Verification
**Location**: `auth_router_email.py` - `login()`

**Current Behavior**: Users can login without verifying their email.

**Recommendation**: Document this behavior or add verification requirement:
```python
if not user.is_verified:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Please verify your email before logging in"
    )
```

### 🟢 Minor Issues

#### 4. No Password Strength Requirements
**Location**: Registration endpoint

**Current**: Only length check
**Recommendation**: Add strength requirements:
- Minimum 8 characters
- At least one uppercase
- At least one lowercase
- At least one number
- At least one special character

#### 5. No Rate Limiting
**Location**: All endpoints

**Risk**: Brute force attacks, code guessing
**Recommendation**: Add rate limiting for:
- Login attempts
- Verification code requests
- Password reset requests

#### 6. No Account Lockout
**Location**: Login endpoint

**Risk**: Unlimited login attempts
**Recommendation**: Lock account after N failed attempts

## Security Recommendations

### High Priority
1. ✅ Use environment variables for secrets (already done)
2. ⚠️ Implement rate limiting
3. ⚠️ Add account lockout mechanism
4. ⚠️ Require email verification before login

### Medium Priority
1. ⚠️ Add password strength requirements
2. ⚠️ Implement IP-based rate limiting
3. ⚠️ Add 2FA support
4. ✅ Use HTTPS only (already configured)

### Low Priority
1. Add remember-me functionality
2. Add device tracking
3. Add login notifications
4. Add session management

## Testing Checklist

- [ ] Register new user
- [ ] Receive verification email
- [ ] Verify email with correct code
- [ ] Verify email with incorrect code
- [ ] Verify email with expired code
- [ ] Login with correct credentials
- [ ] Login with incorrect password
- [ ] Login with non-existent email
- [ ] Request password reset
- [ ] Reset password with correct code
- [ ] Reset password with incorrect code
- [ ] Reset password with expired code
- [ ] Login with new password
- [ ] Access protected endpoints with token
- [ ] Access protected endpoints without token
- [ ] Test password length validation (>72 bytes)
- [ ] Resend verification code
- [ ] Multiple registration attempts with same email

## Environment Variables Required

```bash
# Database
DATABASE_URL=sqlite:///./test.db  # or PostgreSQL URL

# JWT
JWT_SECRET_KEY=your-secret-key-here  # MUST be changed in production

# Email
RESEND_API_KEY=re_xxxxxxxxxxxx

# AWS (for S3/DynamoDB)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=
AWS_S3_BUCKET=

# Piper
PIPER_URL=http://piper:5000
```

## API Documentation

### Base URL
- Production: `https://api.voicetexta.com`
- Local: `http://localhost:8000`

### Endpoints

#### 1. Register
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}

Response 201:
{
  "message": "Registration successful. Please check your email for verification code.",
  "email": "user@example.com",
  "user_id": 1
}
```

#### 2. Verify Email
```http
POST /auth/verify-email
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456"
}

Response 200:
{
  "message": "Email verified successfully",
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

#### 3. Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}

Response 200:
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

#### 4. Get Profile
```http
GET /auth/me
Authorization: Bearer eyJ...

Response 200:
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_verified": true,
  "is_active": true
}
```

#### 5. Forgot Password
```http
POST /auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}

Response 200:
{
  "message": "If an account exists for user@example.com, a password reset code has been sent."
}
```

#### 6. Reset Password
```http
POST /auth/reset-password
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456",
  "new_password": "NewSecurePass123!"
}

Response 200:
{
  "message": "Password reset successfully"
}
```

## Next Steps

1. **Fix password validation** (use Pydantic validators)
2. **Test the complete flow** (use `test_auth_flow.py`)
3. **Add rate limiting** (consider `slowapi` or `fastapi-limiter`)
4. **Decide on verification requirement** (login before/after verification)
5. **Add password strength validation**
6. **Implement account lockout**
7. **Add comprehensive logging**
8. **Set up monitoring and alerts**

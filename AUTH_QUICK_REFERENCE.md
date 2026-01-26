# Authentication Flow - Quick Reference

## 🔧 Fixes Applied

### 1. Password Validation (FIXED ✅)
- **Issue**: Password longer than 72 bytes caused cryptic bcrypt error
- **Fix**: Added Pydantic field validators to both `RegisterRequest` and `ResetPasswordRequest`
- **Validation Rules**:
  - Minimum: 8 characters
  - Maximum: 72 bytes (bcrypt limit)
  - Automatic validation before processing

### 2. Bcrypt Configuration (IMPROVED ✅)
- **Added**: `bcrypt__truncate_error=False` to handle edge cases
- **Location**: `app/auth_email.py`

## 📋 Complete Auth Flow

### Registration & Verification
```
1. POST /auth/register
   ├─> Validates password (8-72 bytes)
   ├─> Creates user (is_verified=False)
   ├─> Generates 6-digit code (15-min expiry)
   └─> Sends verification email

2. POST /auth/verify-email
   ├─> Validates code
   ├─> Sets is_verified=True
   ├─> Sends welcome email
   └─> Returns access token

3. POST /auth/login
   ├─> Validates email + password
   ├─> Checks is_active status
   └─> Returns access token (works even if not verified)
```

### Password Reset
```
1. POST /auth/forgot-password
   ├─> Finds user by email
   ├─> Generates 6-digit reset code
   └─> Sends reset email

2. POST /auth/reset-password
   ├─> Validates password (8-72 bytes)
   ├─> Verifies reset code
   ├─> Updates hashed_password
   └─> Returns success

3. POST /auth/login
   └─> Login with new password
```

### Profile Access
```
GET /auth/me
├─> Requires: Valid JWT token
└─> Returns: User profile (any user)

GET /users/me/profile  
├─> Requires: Valid JWT token + verified email
└─> Returns: User profile (verified users only)
```

## 🧪 Testing

### Quick Test (Manual)
```bash
# 1. Register
curl -X POST https://api.voicetexta.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "full_name": "Test User"
  }'

# 2. Check email for code

# 3. Verify
curl -X POST https://api.voicetexta.com/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "code": "123456"
  }'

# 4. Save the access_token from response

# 5. Get profile
curl -X GET https://api.voicetexta.com/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Automated Test
```bash
cd /Users/manavgenius/Desktop/ISL/voicetexta-tts/tts-backend
python test_auth_flow.py
```

## ⚠️ Known Behavior

### Users CAN Login Before Email Verification
- **Current**: Login works even if `is_verified=False`
- **Protected**: Only `/users/me/profile` requires verification
- **Consideration**: If you want to block unverified logins, add this to `login()`:
  ```python
  if not user.is_verified:
      raise HTTPException(403, "Please verify your email")
  ```

### Password Requirements
- ✅ Minimum 8 characters
- ✅ Maximum 72 bytes (bcrypt limit)
- ❌ No complexity requirements (add if needed)

## 🔐 Security Notes

### Implemented
- ✅ Bcrypt password hashing
- ✅ JWT tokens (7-day expiry)
- ✅ Email verification codes (15-min expiry)
- ✅ Code reuse prevention
- ✅ Email enumeration protection (password reset)
- ✅ HTTPS enforced
- ✅ Environment-based secrets

### Missing (To Implement)
- ⚠️ Rate limiting (brute force protection)
- ⚠️ Account lockout (failed login attempts)
- ⚠️ Password complexity requirements
- ⚠️ 2FA support
- ⚠️ Session management
- ⚠️ Device tracking
- ⚠️ IP-based restrictions

## 📊 Database Schema

### users
```sql
- id: INTEGER PRIMARY KEY
- email: STRING UNIQUE
- hashed_password: STRING
- full_name: STRING (nullable)
- is_active: BOOLEAN (default: true)
- is_verified: BOOLEAN (default: false)
- created_at: DATETIME
- updated_at: DATETIME
```

### verification_codes
```sql
- id: INTEGER PRIMARY KEY
- email: STRING (indexed)
- code: STRING (6 digits)
- code_type: STRING ("email_verification" or "password_reset")
- is_used: BOOLEAN (default: false)
- expires_at: DATETIME
- created_at: DATETIME
```

## 🔑 Environment Variables

```bash
# Required
JWT_SECRET_KEY=your-super-secret-key-min-32-chars
RESEND_API_KEY=re_xxxxxxxxxxxx
DATABASE_URL=sqlite:///./test.db  # or postgresql://...

# Optional (for TTS features)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
AWS_S3_BUCKET=voicetexta-audio
PIPER_URL=http://piper:5000
```

## 📝 Error Messages

### Registration
- `"Email already registered"` - Email exists in database
- `"Password is too long (X bytes). Maximum length is 72 bytes."` - Password > 72 bytes
- `"Password must be at least 8 characters long."` - Password < 8 chars
- `"Failed to send verification email"` - Email service error

### Login
- `"Invalid email or password"` - Wrong credentials
- `"Account is inactive"` - User is_active=False

### Verification
- `"Invalid or expired verification code"` - Code wrong/expired/used
- `"User not found"` - Email doesn't exist
- `"Email already verified"` - Trying to resend code for verified user

### Password Reset
- `"Invalid or expired reset code"` - Reset code wrong/expired/used

## 🎯 Common Issues & Solutions

### Issue: "password cannot be longer than 72 bytes"
**Cause**: Password exceeds bcrypt's 72-byte limit  
**Solution**: ✅ Fixed with Pydantic validators  
**User Action**: Use shorter password (usually 72 chars is enough)

### Issue: Can't receive verification emails
**Check**:
1. `RESEND_API_KEY` is set correctly
2. Email domain `voicetexta.com` is verified in Resend
3. Check spam folder
4. Check Resend dashboard for delivery status

### Issue: JWT token expired
**Cause**: Token older than 7 days  
**Solution**: Login again to get new token

### Issue: Can't login after registration
**Check**:
1. Correct password being used
2. User is_active=True
3. No typos in email
4. Password meets requirements (8-72 bytes)

## 🚀 Deployment Checklist

- [ ] Set strong `JWT_SECRET_KEY` (min 32 characters)
- [ ] Configure `RESEND_API_KEY`
- [ ] Set up PostgreSQL (production)
- [ ] Enable HTTPS only
- [ ] Set up rate limiting
- [ ] Configure CORS properly
- [ ] Set up monitoring/logging
- [ ] Back up database regularly
- [ ] Test all endpoints
- [ ] Document API for frontend team

## 📞 Support

For issues or questions:
1. Check [AUTH_FLOW_ANALYSIS.md](AUTH_FLOW_ANALYSIS.md) for detailed analysis
2. Run `python test_auth_flow.py` to verify flow
3. Check backend logs for errors
4. Verify environment variables are set

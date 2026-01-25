# Migration Guide: From AWS to Resend + Cloudinary

This guide explains the migration from AWS services (Cognito, S3) to Resend (email) and Cloudinary (file storage).

## What Changed

### Authentication: Cognito → Email/Password + Resend

**Before (Cognito):**
- AWS Cognito handled user registration, login, and email verification
- Required AWS credentials and User Pool configuration

**After (Email + Resend):**
- Custom email/password authentication with JWT tokens
- Email verification codes sent via Resend API
- Users stored in local database (SQLite/PostgreSQL)

### File Storage: S3 → Cloudinary

**Before (S3):**
- Audio files uploaded to AWS S3
- Required S3 bucket and AWS credentials

**After (Cloudinary):**
- Audio files uploaded to Cloudinary
- Uses Cloudinary's video resource type for audio files
- No AWS credentials needed

## New Environment Variables

Update your `.env` file:

```env
# JWT Authentication
JWT_SECRET_KEY=your-secure-random-secret-key

# Resend Email Service
RESEND_API_KEY=re_your_resend_api_key

# Cloudinary File Storage
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

## New Files Created

1. **app/auth_email.py** - Email-based authentication system
2. **app/routers/auth_router_email.py** - New auth endpoints
3. **app/utils/email_service.py** - Resend email integration
4. **app/utils/cloudinary_uploader.py** - Cloudinary file uploads
5. **app/models.py** - Updated with VerificationCode model

## Database Migration

Run database migration to create new tables:

```bash
# Create a new migration
alembic revision --autogenerate -m "Add email auth tables"

# Apply the migration
alembic upgrade head
```

Or manually create tables:
- `users` table: now includes `hashed_password`, `full_name`, `is_verified`
- `verification_codes` table: new table for email verification codes

## API Changes

### Registration Flow

**Before:**
```
POST /auth/register → returns user
POST /auth/confirm-signup → verifies email
```

**After:**
```
POST /auth/register → sends verification email
POST /auth/verify-email → verifies with code, returns token
```

### Login

**Before:**
```
POST /auth/login → returns Cognito tokens
```

**After:**
```
POST /auth/login → returns JWT access_token
```

### Password Reset

**New endpoints:**
```
POST /auth/forgot-password → sends reset code
POST /auth/reset-password → resets password with code
```

## Code Updates Needed

### 1. Import the new auth router in main.py

```python
# Replace or add alongside old auth router
from app.routers.auth_router_email import router as auth_router_email

app.include_router(auth_router_email)
```

### 2. Update protected endpoints to use new auth

```python
# Old
from app.auth import get_current_user

# New
from app.auth_email import get_current_verified_user

@router.get("/protected")
def protected_route(user = Depends(get_current_verified_user)):
    # user.id is now a string (user ID from database)
    # user.email is the email
    pass
```

### 3. File uploads now use Cloudinary

No code changes needed - the imports remain the same:

```python
from app.utils.s3_uploader import upload_audio
from app.utils.s3_utils import upload_audio

# Both now use Cloudinary under the hood
```

## Testing the Migration

### 1. Install new dependencies

```bash
pip install -r requirements.txt
```

### 2. Test registration

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"securepass123","full_name":"Test User"}'
```

### 3. Check email for verification code

Check the email inbox for a 6-digit code.

### 4. Verify email

```bash
curl -X POST http://localhost:8000/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","code":"123456"}'
```

### 5. Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"securepass123"}'
```

### 6. Test authenticated endpoint

```bash
TOKEN="your_token_here"
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

## Backward Compatibility

The old AWS files are preserved for reference:
- `app/auth.py` (old Cognito auth)
- `app/routers/auth_router.py` (old Cognito endpoints)

You can run both auth systems in parallel during migration if needed.

## Rollback Plan

If you need to rollback:
1. Keep AWS credentials in `.env`
2. Revert to old auth router in `main.py`
3. Keep both sets of files until fully migrated

## Production Checklist

- [ ] Generate strong JWT_SECRET_KEY (use `openssl rand -hex 32`)
- [ ] Configure Resend domain and verify sender email
- [ ] Set up Cloudinary transformations if needed
- [ ] Test email delivery in production
- [ ] Update frontend to use new auth endpoints
- [ ] Migrate existing users (if any)
- [ ] Update API documentation
- [ ] Monitor error logs during migration

## Support

- Resend Docs: https://resend.com/docs
- Cloudinary Docs: https://cloudinary.com/documentation
- FastAPI JWT: https://fastapi.tiangolo.com/tutorial/security/

## Notes

- Email verification codes expire in 15 minutes
- JWT tokens expire in 7 days
- Cloudinary URLs don't expire (public by default)
- Password reset codes are single-use

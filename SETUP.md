# 🚀 Setup Instructions - Email Auth & Cloudinary

## Quick Start (3 Steps)

### 1️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `resend` - Email service
- `cloudinary` - File storage
- All existing dependencies

### 2️⃣ Configure Environment Variables

Edit the `.env` file and ensure these are set:

```env
# Generate a secure secret key
JWT_SECRET_KEY=your-secure-random-secret-here

# Get from https://resend.com/api-keys
RESEND_API_KEY=re_your_api_key_here

# Get from https://cloudinary.com/console
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

**Generate JWT Secret:**
```bash
openssl rand -hex 32
```

### 3️⃣ Setup Database

```bash
python3 -c "from app.db import Base, engine; Base.metadata.create_all(bind=engine)"
```

Or use the automated setup script:
```bash
./setup_email_auth.sh
```

## ✅ Verify Setup

Run the verification test:

```bash
python3 test_email_auth_setup.py
```

Expected output:
```
Testing imports...
✓ app.auth_email
✓ app.utils.email_service
✓ app.utils.cloudinary_uploader
✓ app.routers.auth_router_email
✓ app.models (User, VerificationCode)

✅ All imports successful!

Testing database...
✓ Database tables created/verified

Testing configuration...
✓ JWT_SECRET_KEY: configured
✓ RESEND_API_KEY: configured
✓ CLOUDINARY_CLOUD_NAME: configured
✓ CLOUDINARY_API_KEY: configured
✓ CLOUDINARY_API_SECRET: configured

✅ All configuration complete!

🎉 All tests passed! System is ready.
```

## 🏃 Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

Visit:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 📚 Test the API

### Using Swagger UI (Browser)

1. Go to http://localhost:8000/docs
2. Try the `/auth/register` endpoint
3. Check your email for verification code
4. Use `/auth/verify-email` with the code
5. Copy the `access_token` from response
6. Click "Authorize" button and paste token
7. Try protected endpoints like `/auth/me`

### Using cURL (Terminal)

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "SecurePass123",
    "full_name": "Your Name"
  }'

# Check your email for 6-digit code, then verify
curl -X POST http://localhost:8000/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "code": "123456"
  }'

# Save the access_token from response, then login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "SecurePass123"
  }'

# Use token to access protected endpoints
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🔧 Troubleshooting

### ❌ ModuleNotFoundError: No module named 'resend'

```bash
pip install -r requirements.txt
```

### ❌ Database table not found

```bash
python3 -c "from app.db import Base, engine; Base.metadata.create_all(bind=engine)"
```

### ❌ Emails not sending

1. Check `RESEND_API_KEY` is correct
2. Verify sender domain in Resend dashboard
3. Check application logs for error messages

### ❌ File upload fails

1. Verify all 3 Cloudinary env vars are set
2. Check Cloudinary dashboard quota
3. Test with a small file first

### ❌ JWT token errors

1. Ensure `JWT_SECRET_KEY` is set in .env
2. Make sure token hasn't expired (7 days)
3. Check Authorization header: `Bearer {token}`

## 📁 Project Structure

```
tts-backend/
├── app/
│   ├── auth_email.py              # ⭐ NEW: Email auth system
│   ├── routers/
│   │   └── auth_router_email.py   # ⭐ NEW: Auth endpoints
│   ├── utils/
│   │   ├── email_service.py       # ⭐ NEW: Resend integration
│   │   ├── cloudinary_uploader.py # ⭐ NEW: Cloudinary uploads
│   │   ├── s3_uploader.py         # UPDATED: Now uses Cloudinary
│   │   └── s3_utils.py            # UPDATED: Now uses Cloudinary
│   ├── models.py                  # UPDATED: New tables
│   └── main.py                    # UPDATED: New router
├── .env                           # UPDATED: New config
├── requirements.txt               # UPDATED: New packages
├── setup_email_auth.sh            # ⭐ NEW: Setup script
├── test_email_auth_setup.py       # ⭐ NEW: Test script
├── MIGRATION_GUIDE.md             # ⭐ NEW: Migration docs
├── EMAIL_AUTH_GUIDE.md            # ⭐ NEW: Quick reference
└── MIGRATION_COMPLETE.md          # ⭐ NEW: Summary
```

## 📖 Documentation

- **SETUP.md** (this file) - Setup instructions
- **EMAIL_AUTH_GUIDE.md** - API reference & examples
- **MIGRATION_GUIDE.md** - Detailed migration guide
- **MIGRATION_COMPLETE.md** - Complete summary

## 🎯 What's Working

✅ Email/password registration  
✅ Email verification with codes  
✅ JWT token authentication  
✅ Password reset flow  
✅ Cloudinary file uploads  
✅ Resend email service  
✅ Protected routes  
✅ User management  

## 🚫 What's Removed

❌ AWS Cognito dependency  
❌ AWS S3 dependency  
❌ AWS credentials needed  
❌ pycognito package  

## ⚡ Next Steps

1. ✅ Install dependencies
2. ✅ Configure .env
3. ✅ Setup database
4. ✅ Test with verification script
5. ✅ Start server
6. ✅ Test registration flow
7. 📱 Update frontend to use new endpoints
8. 🚀 Deploy to production

## 💡 Tips

- Use `.env.example` as template (create one if needed)
- Keep JWT_SECRET_KEY secure and never commit it
- Test email delivery with your domain
- Monitor Cloudinary usage/quota
- Check logs for debugging: `uvicorn app.main:app --reload --log-level debug`

## 🆘 Need Help?

1. Check documentation files in project root
2. Review error messages in terminal
3. Test with verification script
4. Check API docs at /docs endpoint

---

**Ready to go!** 🎉

Start the server and test your first registration!

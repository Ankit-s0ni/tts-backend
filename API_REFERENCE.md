# TTS App - Complete API Reference

## Base URL
```
Local: http://localhost:8001
Production: https://api.voicetexta.com
```

---

## 🏥 Health & Status

### GET /health
Check API health and deployment status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-27T11:08:21.783677",
  "version": "2.0",
  "services": {
    "api": "running",
    "piper_tts": "available|unavailable",
    "cloudinary": "configured|not_configured",
    "file_storage": "ready|not_ready"
  },
  "features": {
    "tts_sync": true,
    "tts_async": true,
    "voice_list": true,
    "auth_email": true,
    "cloudinary_upload": true,
    "audio_serving": true
  },
  "recent_changes": {}
}
```

---

## 🎙️ TTS Endpoints

### GET /voices
List all available TTS voices (45+ voices including Indian languages).

**Response:**
```json
[
  {
    "id": "en_US-lessac-high",
    "engine": "piper",
    "language": "en_US",
    "display_name": "Lessac (High Quality)"
  },
  ...
]
```

### POST /tts/sync
Generate speech synchronously and return audio URL.

**Request:**
```json
{
  "text": "Hello world",
  "voice": "en_US-lessac-high"
}
```

**Response:**
```json
{
  "duration": 2.74,
  "text": "Hello world",
  "voice_id": "en_US-lessac-high",
  "engine": "piper",
  "sample_rate": 22050,
  "status": "success",
  "audio_url": "https://res.cloudinary.com/dnxatxoij/video/upload/v1769506607/tts/en_US-lessac-high/xxx.wav"
}
```

### GET /tts/audio/{filename}
Download audio file by filename.

**Example:**
```
GET /tts/audio/tts_abc123_20260127_123456.wav
```

**Response:** WAV audio file (audio/wav)

---

## 🔐 Authentication Endpoints

### GET /auth/info
Get authentication system information.

**Response:**
```json
{
  "auth": "email",
  "note": "Registration and login use email/password with verification codes"
}
```

### POST /auth/register
Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe"
}
```

**Response:** (201 Created)
```json
{
  "message": "Registration successful. Please check your email for verification code.",
  "email": "user@example.com",
  "user_id": 1
}
```

### POST /auth/verify-email
Verify email with 6-digit code.

**Request:**
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response:** (200 OK)
```json
{
  "message": "Email verified successfully",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### POST /auth/resend-verification-code
Resend verification code to email.

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:** (200 OK)
```json
{
  "message": "Verification code sent to user@example.com"
}
```

### POST /auth/login
Login with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response:** (200 OK)
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### POST /auth/forgot-password
Request password reset code.

**Request:**
```json
{
  "email": "user@example.com"
}
```

**Response:** (200 OK)
```json
{
  "message": "If an account exists for user@example.com, a password reset code has been sent."
}
```

### POST /auth/reset-password
Reset password with reset code.

**Request:**
```json
{
  "email": "user@example.com",
  "code": "123456",
  "new_password": "NewSecurePass123"
}
```

**Response:** (200 OK)
```json
{
  "message": "Password reset successfully"
}
```

---

## 👤 User Profile Endpoints

### GET /auth/me
Get current user information (requires authentication).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** (200 OK)
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_verified": true,
  "is_active": true
}
```

### PUT /auth/me
Update current user profile (requires authentication).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "full_name": "John Doe Updated"
}
```

**Response:** (200 OK)
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe Updated",
  "is_verified": true,
  "is_active": true
}
```

### POST /auth/link-profile
Update user profile (backward compatible endpoint).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request:**
```json
{
  "full_name": "John Doe",
  "phone": "+1234567890",
  "age": 25,
  "profile_image": "https://example.com/avatar.png"
}
```

**Response:** (200 OK)
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_verified": true,
  "is_active": true
}
```

### GET /users/me/profile
Get user profile (requires verified email).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** (200 OK)
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_verified": true,
  "is_active": true
}
```

---

## 📊 Complete Endpoint Summary

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | ❌ | Health check |
| GET | `/voices` | ❌ | List all voices |
| POST | `/tts/sync` | ❌ | Generate speech |
| GET | `/tts/audio/{filename}` | ❌ | Download audio |
| GET | `/auth/info` | ❌ | Auth system info |
| POST | `/auth/register` | ❌ | Register user |
| POST | `/auth/verify-email` | ❌ | Verify email |
| POST | `/auth/resend-verification-code` | ❌ | Resend code |
| POST | `/auth/login` | ❌ | Login |
| POST | `/auth/forgot-password` | ❌ | Request reset |
| POST | `/auth/reset-password` | ❌ | Reset password |
| GET | `/auth/me` | ✅ | Get user info |
| PUT | `/auth/me` | ✅ | Update profile |
| POST | `/auth/link-profile` | ✅ | Update profile (alt) |
| GET | `/users/me/profile` | ✅ | Get verified profile |

---

## 🔑 Authentication

### Token Format
All authenticated requests use Bearer token:
```
Authorization: Bearer {access_token}
```

### Token Expiry
- Access tokens expire in **7 days**
- Re-login to get a new token

### Error Responses
```json
{
  "detail": "Error message here"
}
```

**Common Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad request
- `401` - Unauthorized (missing/invalid token)
- `404` - Not found
- `500` - Server error

---

## 📱 Flutter Integration Example

### Registration
```dart
final response = await Dio().post(
  'https://api.voicetexta.com/auth/register',
  data: {
    'email': 'user@example.com',
    'password': 'SecurePass123',
    'full_name': 'John Doe'
  }
);
```

### Email Verification
```dart
final response = await Dio().post(
  'https://api.voicetexta.com/auth/verify-email',
  data: {
    'email': 'user@example.com',
    'code': '123456'
  }
);
final token = response.data['access_token'];
```

### Update Profile
```dart
final response = await Dio().post(
  'https://api.voicetexta.com/auth/link-profile',
  data: {
    'full_name': 'John Doe Updated'
  },
  options: Options(
    headers: {'Authorization': 'Bearer $token'}
  )
);
```

### Generate Speech
```dart
final response = await Dio().post(
  'https://api.voicetexta.com/tts/sync',
  data: {
    'text': 'Hello world',
    'voice': 'en_US-lessac-high'
  }
);
final audioUrl = response.data['audio_url'];
```

---

## 🚀 Recent Updates (v2.0)

✅ **Cloudinary Integration** - Audio files uploaded to CDN  
✅ **Email Authentication** - Verification codes via email  
✅ **Profile Updates** - `/auth/link-profile` endpoint  
✅ **Health Check** - `/health` endpoint for monitoring  
✅ **Optional Age** - Age field not required in registration  
✅ **45+ Voices** - Including Malayalam, Telugu, Hindi  
✅ **Audio Serving** - Download audio files directly  

---

## 📞 Support

For issues or questions:
1. Check `/health` endpoint first
2. Review error message in response
3. Ensure correct Content-Type: `application/json`
4. Verify token format if using authenticated endpoints

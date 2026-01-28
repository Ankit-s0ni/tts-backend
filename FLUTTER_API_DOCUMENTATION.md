# TTS API Documentation - Flutter Implementation Guide

**Version:** 2.0  
**Last Updated:** January 29, 2026  
**Base URL:** `https://your-domain.com` (or `http://localhost:8002` for development)

---

## Table of Contents

1. [Authentication](#authentication)
2. [Error Handling](#error-handling)
3. [API Endpoints](#api-endpoints)
4. [Flutter Implementation Examples](#flutter-implementation-examples)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Authentication

### Overview
This API uses **JWT (JSON Web Token)** based authentication via email and password. Users must register, verify their email, and then authenticate to receive tokens for subsequent requests.

### Authentication Flow
```
1. User registers with email & password
2. Verification code sent to email
3. User verifies email with code
4. User logs in with email & password
5. Server returns access token (expires in 7 days)
6. All subsequent requests include Authorization header
```

### JWT Token Structure
- **Type:** Bearer Token
- **Expiration:** 7 days from login
- **Location:** HTTP Authorization Header
- **Format:** `Authorization: Bearer {token}`

### Token Claims
```json
{
  "sub": "user_id",           // Subject: numeric user ID as string
  "exp": 1770236294,          // Expiration timestamp
  "iat": 1769631494,          // Issued at timestamp
  "email": "user@example.com" // User email (optional)
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | User doesn't have permission (e.g., accessing other user's job) |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error in request body |
| 500 | Internal Server Error | Server error |

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Example Error Response
```json
{
  "detail": "Access denied"
}
```

### Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid credentials" | Wrong email/password | Verify email and password |
| "Email not verified" | Email verification pending | Check email for verification code |
| "Access denied" | Accessing another user's job | Ensure you own the resource |
| "Job not found" | Job ID doesn't exist | Verify job ID is correct |
| "Token expired" | JWT token expired | Re-login to get new token |

---

## API Endpoints

### 1. Health & Configuration

#### GET /health
Check if API is running.

**Request:**
```http
GET /health HTTP/1.1
Host: your-domain.com
```

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

**Flutter Example:**
```dart
Future<bool> checkApiHealth() async {
  try {
    final response = await http.get(
      Uri.parse('https://your-domain.com/health'),
      headers: {'Content-Type': 'application/json'},
    ).timeout(Duration(seconds: 5));
    
    return response.statusCode == 200;
  } catch (e) {
    print('Health check failed: $e');
    return false;
  }
}
```

---

#### GET /config
Get API configuration and supported voices.

**Request:**
```http
GET /config HTTP/1.1
Host: your-domain.com
```

**Response (200 OK):**
```json
{
  "api_version": "2.0",
  "environment": "production",
  "max_text_length": 5000,
  "supported_voices": ["en_US-lessac-high", "hi_IN-pratham-medium"]
}
```

---

### 2. Authentication Endpoints

#### POST /auth/register
Register a new user account.

**Request:**
```http
POST /auth/register HTTP/1.1
Host: your-domain.com
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Registration successful. Please check your email for verification code.",
  "email": "user@example.com",
  "user_id": 1
}
```

**Validation Rules:**
- Email: Valid email format required
- Password: Minimum 8 characters, must contain uppercase, lowercase, number, and special character

**Flutter Example:**
```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class AuthService {
  final String baseUrl = 'https://your-domain.com';
  
  Future<Map<String, dynamic>> register(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/register'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'password': password,
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['detail'] ?? 'Registration failed');
      }
    } catch (e) {
      throw Exception('Registration error: $e');
    }
  }
}
```

---

#### POST /auth/verify-email
Verify email with verification code sent to user.

**Request:**
```http
POST /auth/verify-email HTTP/1.1
Host: your-domain.com
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response (200 OK):**
```json
{
  "message": "Email verified successfully"
}
```

**Flutter Example:**
```dart
Future<void> verifyEmail(String email, String code) async {
  final response = await http.post(
    Uri.parse('$baseUrl/auth/verify-email'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'email': email,
      'code': code,
    }),
  );
  
  if (response.statusCode != 200) {
    final error = jsonDecode(response.body);
    throw Exception(error['detail'] ?? 'Verification failed');
  }
}
```

---

#### POST /auth/resend-code
Resend verification code if user didn't receive it.

**Request:**
```http
POST /auth/resend-code HTTP/1.1
Host: your-domain.com
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Verification code sent to email"
}
```

---

#### POST /auth/login
Authenticate user and receive JWT token.

**Request:**
```http
POST /auth/login HTTP/1.1
Host: your-domain.com
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzcwMjM2Mjk0fQ.34NghYX0pax93Ey6kH7SXTMI4bQH2plI6jfoqNatRcI",
  "token_type": "bearer",
  "user_id": 1,
  "email": "user@example.com"
}
```

**Flutter Example:**
```dart
Future<String> login(String email, String password) async {
  final response = await http.post(
    Uri.parse('$baseUrl/auth/login'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'email': email,
      'password': password,
    }),
  );
  
  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    String token = data['access_token'];
    
    // Save token securely (using flutter_secure_storage)
    await storage.write(key: 'auth_token', value: token);
    
    return token;
  } else {
    final error = jsonDecode(response.body);
    throw Exception(error['detail'] ?? 'Login failed');
  }
}
```

---

#### GET /auth/me
Get current authenticated user information.

**Request:**
```http
GET /auth/me HTTP/1.1
Host: your-domain.com
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": true
}
```

**Flutter Example:**
```dart
Future<Map<String, dynamic>> getCurrentUser(String token) async {
  final response = await http.get(
    Uri.parse('$baseUrl/auth/me'),
    headers: {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    },
  );
  
  if (response.statusCode == 200) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Failed to fetch user');
  }
}
```

---

#### PUT /auth/me
Update current user's profile information.

**Request:**
```http
PUT /auth/me HTTP/1.1
Host: your-domain.com
Authorization: Bearer {token}
Content-Type: application/json

{
  "full_name": "John Updated"
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Updated",
  "is_active": true,
  "is_verified": true
}
```

---

#### POST /auth/forgot-pwd
Request password reset by sending reset link to email.

**Request:**
```http
POST /auth/forgot-pwd HTTP/1.1
Host: your-domain.com
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Password reset email sent"
}
```

---

#### POST /auth/reset-pwd
Reset password using reset token from email.

**Request:**
```http
POST /auth/reset-pwd HTTP/1.1
Host: your-domain.com
Content-Type: application/json

{
  "email": "user@example.com",
  "reset_token": "token_from_email",
  "new_password": "NewSecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password reset successful"
}
```

---

#### POST /auth/link-profile
Link additional authentication methods to user account.

**Request:**
```http
POST /auth/link-profile HTTP/1.1
Host: your-domain.com
Authorization: Bearer {token}
Content-Type: application/json

{
  "auth_type": "google",
  "auth_id": "google_user_id"
}
```

**Response (200 OK):**
```json
{
  "message": "Profile linked successfully"
}
```

---

### 3. Voice Catalog Endpoints

#### GET /voices
Get list of all available voices for TTS.

**Request:**
```http
GET /voices HTTP/1.1
Host: your-domain.com
```

**Response (200 OK):**
```json
[
  {
    "voice_id": "en_US-lessac-high",
    "name": "Lessac (High)",
    "language": "en_US",
    "gender": "male",
    "engine": "piper",
    "description": "High quality male voice"
  },
  {
    "voice_id": "hi_IN-pratham-medium",
    "name": "Pratham",
    "language": "hi_IN",
    "gender": "male",
    "engine": "piper",
    "description": "Hindi male voice"
  }
]
```

**Flutter Example:**
```dart
class Voice {
  final String voiceId;
  final String name;
  final String language;
  final String gender;
  final String engine;
  
  Voice({
    required this.voiceId,
    required this.name,
    required this.language,
    required this.gender,
    required this.engine,
  });
  
  factory Voice.fromJson(Map<String, dynamic> json) {
    return Voice(
      voiceId: json['voice_id'],
      name: json['name'],
      language: json['language'],
      gender: json['gender'],
      engine: json['engine'],
    );
  }
}

Future<List<Voice>> getVoices() async {
  final response = await http.get(
    Uri.parse('$baseUrl/voices'),
    headers: {'Content-Type': 'application/json'},
  );
  
  if (response.statusCode == 200) {
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((json) => Voice.fromJson(json)).toList();
  } else {
    throw Exception('Failed to load voices');
  }
}
```

---

### 4. Text-to-Speech Endpoints

#### POST /tts/sync
Synchronous TTS endpoint - converts text to speech and returns audio URL immediately.

**Request:**
```http
POST /tts/sync HTTP/1.1
Host: your-domain.com
Content-Type: application/json

{
  "text": "Hello, how are you today?",
  "voice": "en_US-lessac-high"
}
```

**Response (200 OK):**
```json
{
  "audio_url": "/tts/audio/generated_audio_1234.wav",
  "duration": 2.5,
  "filename": "generated_audio_1234.wav",
  "engine": "piper"
}
```

**Constraints:**
- Max text length: 500 characters for sync endpoint
- Response time: 2-5 seconds depending on text length

**Flutter Example:**
```dart
class TTSResponse {
  final String audioUrl;
  final double duration;
  final String filename;
  
  TTSResponse({
    required this.audioUrl,
    required this.duration,
    required this.filename,
  });
  
  factory TTSResponse.fromJson(Map<String, dynamic> json) {
    return TTSResponse(
      audioUrl: json['audio_url'],
      duration: json['duration'].toDouble(),
      filename: json['filename'],
    );
  }
}

Future<TTSResponse> synthesizeSyncTTS(String text, String voiceId) async {
  final token = await storage.read(key: 'auth_token');
  
  final response = await http.post(
    Uri.parse('$baseUrl/tts/sync'),
    headers: {
      'Content-Type': 'application/json',
    },
    body: jsonEncode({
      'text': text,
      'voice': voiceId,
    }),
  );
  
  if (response.statusCode == 200) {
    return TTSResponse.fromJson(jsonDecode(response.body));
  } else {
    final error = jsonDecode(response.body);
    throw Exception(error['detail'] ?? 'TTS synthesis failed');
  }
}
```

---

#### POST /tts/jobs
Create asynchronous TTS job (for long text).

**Request:**
```http
POST /tts/jobs HTTP/1.1
Host: your-domain.com
Authorization: Bearer {token}
Content-Type: application/json

{
  "text": "This is a very long text that will be processed asynchronously. It can contain multiple paragraphs and sentences.",
  "voice_id": "en_US-lessac-high"
}
```

**Response (200 OK):**
```json
{
  "id": "a982745f-bb67-4655-9480-7f045d675f9c",
  "status": "queued",
  "created_at": "2026-01-28T20:18:19.693876",
  "audio_url": null
}
```

**Status Values:**
- `queued` - Job waiting to be processed
- `processing` - Job is being synthesized
- `completed` - Audio ready, `audio_url` populated
- `failed` - Error during synthesis

**Constraints:**
- Max text length: 5000 characters
- Processing time: 10 seconds to 2 minutes
- Job stored for 7 days after creation

**Flutter Example:**
```dart
class TTSJob {
  final String id;
  final String status;
  final DateTime createdAt;
  final String? audioUrl;
  final String? text;
  final String? voiceId;
  
  TTSJob({
    required this.id,
    required this.status,
    required this.createdAt,
    this.audioUrl,
    this.text,
    this.voiceId,
  });
  
  factory TTSJob.fromJson(Map<String, dynamic> json) {
    return TTSJob(
      id: json['id'],
      status: json['status'],
      createdAt: DateTime.parse(json['created_at']),
      audioUrl: json['audio_url'],
      text: json['text'],
      voiceId: json['voice_id'],
    );
  }
  
  bool get isCompleted => status == 'completed';
  bool get isProcessing => status == 'processing' || status == 'queued';
  bool get isFailed => status == 'failed';
}

Future<TTSJob> createTTSJob(String text, String voiceId) async {
  final token = await storage.read(key: 'auth_token');
  
  final response = await http.post(
    Uri.parse('$baseUrl/tts/jobs'),
    headers: {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    },
    body: jsonEncode({
      'text': text,
      'voice_id': voiceId,
    }),
  );
  
  if (response.statusCode == 200) {
    return TTSJob.fromJson(jsonDecode(response.body));
  } else {
    final error = jsonDecode(response.body);
    throw Exception(error['detail'] ?? 'Failed to create TTS job');
  }
}
```

---

#### GET /tts/jobs
List all TTS jobs for current user.

**Request:**
```http
GET /tts/jobs?limit=50 HTTP/1.1
Host: your-domain.com
Authorization: Bearer {token}
```

**Query Parameters:**
- `limit` (optional, default: 50): Maximum number of jobs to return (1-500)

**Response (200 OK):**
```json
[
  {
    "id": "a982745f-bb67-4655-9480-7f045d675f9c",
    "status": "completed",
    "created_at": "2026-01-28T20:18:19.693876",
    "audio_url": "https://res.cloudinary.com/dnxatxoij/video/upload/v1769631505/tts/en_US-lessac-high/7e1a1a01d043.wav",
    "text": "Hello world",
    "voice_id": "en_US-lessac-high"
  }
]
```

**Security:**
- User can only see their own jobs
- Other users' jobs are not visible
- Returns 403 Forbidden if accessing another user's data

**Flutter Example:**
```dart
Future<List<TTSJob>> getUserJobs({int limit = 50}) async {
  final token = await storage.read(key: 'auth_token');
  
  final response = await http.get(
    Uri.parse('$baseUrl/tts/jobs?limit=$limit'),
    headers: {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    },
  );
  
  if (response.statusCode == 200) {
    final List<dynamic> data = jsonDecode(response.body);
    return data.map((json) => TTSJob.fromJson(json)).toList();
  } else {
    throw Exception('Failed to fetch jobs');
  }
}

// Usage with polling
Future<void> pollJobStatus(String jobId) async {
  const maxAttempts = 60;
  const pollInterval = Duration(seconds: 1);
  
  for (int i = 0; i < maxAttempts; i++) {
    final job = await getTTSJob(jobId);
    
    if (job.isCompleted) {
      print('Job completed! Audio URL: ${job.audioUrl}');
      break;
    }
    
    if (job.isFailed) {
      throw Exception('Job failed');
    }
    
    print('Job status: ${job.status}');
    await Future.delayed(pollInterval);
  }
}
```

---

#### GET /tts/jobs/{job_id}
Get details of a specific TTS job.

**Request:**
```http
GET /tts/jobs/a982745f-bb67-4655-9480-7f045d675f9c HTTP/1.1
Host: your-domain.com
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "id": "a982745f-bb67-4655-9480-7f045d675f9c",
  "status": "completed",
  "created_at": "2026-01-28T20:18:19.693876",
  "audio_url": "https://res.cloudinary.com/dnxatxoij/video/upload/v1769631505/tts/en_US-lessac-high/7e1a1a01d043.wav",
  "text": "Hello world",
  "voice_id": "en_US-lessac-high"
}
```

**Security:**
- User can only access their own jobs
- Returns 403 Forbidden if accessing another user's job
- Returns 404 Not Found if job doesn't exist

**Flutter Example:**
```dart
Future<TTSJob> getTTSJob(String jobId) async {
  final token = await storage.read(key: 'auth_token');
  
  final response = await http.get(
    Uri.parse('$baseUrl/tts/jobs/$jobId'),
    headers: {
      'Authorization': 'Bearer $token',
      'Content-Type': 'application/json',
    },
  );
  
  if (response.statusCode == 200) {
    return TTSJob.fromJson(jsonDecode(response.body));
  } else if (response.statusCode == 403) {
    throw Exception('Access denied - this is not your job');
  } else if (response.statusCode == 404) {
    throw Exception('Job not found');
  } else {
    throw Exception('Failed to fetch job');
  }
}
```

---

#### GET /tts/jobs/{job_id}/audio
Stream or download audio from a completed TTS job.

**Request:**
```http
GET /tts/jobs/a982745f-bb67-4655-9480-7f045d675f9c/audio HTTP/1.1
Host: your-domain.com
Authorization: Bearer {token}
```

**Response (200 OK):**
- Content-Type: `audio/wav`
- Binary audio data (WAV format, 22050 Hz)

**Security:**
- User can only access audio from their own jobs
- Returns 403 Forbidden if accessing another user's audio
- Returns 404 Not Found if job doesn't exist or isn't completed

**Flutter Example (Playing Audio):**
```dart
import 'package:audioplayers/audioplayers.dart';

Future<void> playTTSAudio(String jobId) async {
  final token = await storage.read(key: 'auth_token');
  
  try {
    final audioPlayer = AudioPlayer();
    
    // Method 1: Stream directly from URL (if audio_url is available)
    final job = await getTTSJob(jobId);
    if (job.audioUrl != null) {
      await audioPlayer.play(UrlSource(job.audioUrl!));
      return;
    }
    
    // Method 2: Download and play
    final response = await http.get(
      Uri.parse('$baseUrl/tts/jobs/$jobId/audio'),
      headers: {
        'Authorization': 'Bearer $token',
      },
    );
    
    if (response.statusCode == 200) {
      // Save to temporary file
      final tempDir = await getTemporaryDirectory();
      final audioFile = File('${tempDir.path}/tts_audio_$jobId.wav');
      await audioFile.writeAsBytes(response.bodyBytes);
      
      // Play audio
      await audioPlayer.play(DeviceFileSource(audioFile.path));
    } else if (response.statusCode == 403) {
      throw Exception('Access denied');
    } else {
      throw Exception('Failed to download audio');
    }
  } catch (e) {
    print('Error playing audio: $e');
    rethrow;
  }
}
```

---

#### GET /tts/audio/{filename}
Direct access to generated audio file (if URL provided in response).

**Request:**
```http
GET /tts/audio/generated_audio_1234.wav HTTP/1.1
Host: your-domain.com
```

**Response (200 OK):**
- Binary WAV audio file
- Can be played directly or downloaded

---

## Flutter Implementation Examples

### Complete TTS Service Class

```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class TTSService {
  final String baseUrl = 'https://your-domain.com';
  final _storage = const FlutterSecureStorage();
  
  // ===== AUTHENTICATION =====
  
  /// Register new user
  Future<int> register(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
      }),
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body)['user_id'];
    } else {
      throw Exception(_getErrorMessage(response));
    }
  }
  
  /// Verify email with code
  Future<void> verifyEmail(String email, String code) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/verify-email'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'code': code}),
    );
    
    if (response.statusCode != 200) {
      throw Exception(_getErrorMessage(response));
    }
  }
  
  /// Login and save token
  Future<String> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    
    if (response.statusCode == 200) {
      final token = jsonDecode(response.body)['access_token'];
      await _storage.write(key: 'auth_token', value: token);
      return token;
    } else {
      throw Exception(_getErrorMessage(response));
    }
  }
  
  /// Get current token
  Future<String?> getToken() => _storage.read(key: 'auth_token');
  
  /// Logout
  Future<void> logout() => _storage.delete(key: 'auth_token');
  
  // ===== VOICES =====
  
  /// Get all available voices
  Future<List<Map<String, dynamic>>> getVoices() async {
    final response = await http.get(
      Uri.parse('$baseUrl/voices'),
      headers: {'Content-Type': 'application/json'},
    );
    
    if (response.statusCode == 200) {
      return List<Map<String, dynamic>>.from(jsonDecode(response.body));
    } else {
      throw Exception('Failed to load voices');
    }
  }
  
  // ===== TTS SYNTHESIS =====
  
  /// Synchronous TTS (fast, for short text)
  Future<Map<String, dynamic>> synthesizeSync(String text, String voiceId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/tts/sync'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'text': text, 'voice': voiceId}),
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception(_getErrorMessage(response));
    }
  }
  
  /// Create async TTS job
  Future<String> createJob(String text, String voiceId) async {
    final token = await getToken();
    if (token == null) throw Exception('Not authenticated');
    
    final response = await http.post(
      Uri.parse('$baseUrl/tts/jobs'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({'text': text, 'voice_id': voiceId}),
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body)['id'];
    } else {
      throw Exception(_getErrorMessage(response));
    }
  }
  
  /// Get job details
  Future<Map<String, dynamic>> getJob(String jobId) async {
    final token = await getToken();
    if (token == null) throw Exception('Not authenticated');
    
    final response = await http.get(
      Uri.parse('$baseUrl/tts/jobs/$jobId'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else if (response.statusCode == 403) {
      throw Exception('Access denied');
    } else {
      throw Exception('Job not found');
    }
  }
  
  /// List user's jobs
  Future<List<Map<String, dynamic>>> listJobs({int limit = 50}) async {
    final token = await getToken();
    if (token == null) throw Exception('Not authenticated');
    
    final response = await http.get(
      Uri.parse('$baseUrl/tts/jobs?limit=$limit'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
    );
    
    if (response.statusCode == 200) {
      return List<Map<String, dynamic>>.from(jsonDecode(response.body));
    } else {
      throw Exception('Failed to load jobs');
    }
  }
  
  /// Poll until job is completed
  Future<String?> waitForJobCompletion(String jobId, {Duration timeout = const Duration(minutes: 5)}) async {
    final startTime = DateTime.now();
    const pollInterval = Duration(seconds: 2);
    
    while (DateTime.now().difference(startTime) < timeout) {
      final job = await getJob(jobId);
      
      if (job['status'] == 'completed') {
        return job['audio_url'];
      }
      
      if (job['status'] == 'failed') {
        throw Exception('TTS job failed');
      }
      
      await Future.delayed(pollInterval);
    }
    
    throw Exception('Job timeout');
  }
  
  // ===== UTILITY =====
  
  String _getErrorMessage(http.Response response) {
    try {
      return jsonDecode(response.body)['detail'] ?? 'Unknown error';
    } catch (_) {
      return 'Error: ${response.statusCode}';
    }
  }
}
```

---

### Example UI Integration

```dart
import 'package:flutter/material.dart';

class TTSScreen extends StatefulWidget {
  @override
  _TTSScreenState createState() => _TTSScreenState();
}

class _TTSScreenState extends State<TTSScreen> {
  final _ttsService = TTSService();
  final _textController = TextEditingController();
  String? _selectedVoice;
  List<Map<String, dynamic>> _voices = [];
  bool _isLoading = false;
  String? _jobId;
  String? _audioUrl;
  
  @override
  void initState() {
    super.initState();
    _loadVoices();
  }
  
  void _loadVoices() async {
    try {
      final voices = await _ttsService.getVoices();
      setState(() => _voices = voices);
      if (voices.isNotEmpty) {
        _selectedVoice = voices.first['voice_id'];
      }
    } catch (e) {
      _showError('Failed to load voices: $e');
    }
  }
  
  void _synthesize() async {
    if (_textController.text.isEmpty || _selectedVoice == null) {
      _showError('Please enter text and select a voice');
      return;
    }
    
    setState(() => _isLoading = true);
    
    try {
      // Check text length
      if (_textController.text.length <= 500) {
        // Use sync endpoint for short text
        final result = await _ttsService.synthesizeSync(
          _textController.text,
          _selectedVoice!,
        );
        setState(() {
          _audioUrl = result['audio_url'];
        });
      } else {
        // Use async endpoint for long text
        final jobId = await _ttsService.createJob(
          _textController.text,
          _selectedVoice!,
        );
        setState(() => _jobId = jobId);
        
        // Wait for completion
        _showInfo('Processing... (this may take a minute)');
        final audioUrl = await _ttsService.waitForJobCompletion(jobId);
        setState(() => _audioUrl = audioUrl);
      }
      
      _showInfo('Audio ready!');
    } catch (e) {
      _showError('Synthesis failed: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }
  
  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }
  
  void _showInfo(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Text to Speech')),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Voice selector
            DropdownButton<String>(
              isExpanded: true,
              value: _selectedVoice,
              items: _voices
                  .map((v) => DropdownMenuItem(
                        value: v['voice_id'],
                        child: Text('${v['name']} (${v['language']})'),
                      ))
                  .toList(),
              onChanged: (v) => setState(() => _selectedVoice = v),
            ),
            SizedBox(height: 16),
            
            // Text input
            TextField(
              controller: _textController,
              maxLines: 5,
              decoration: InputDecoration(
                hintText: 'Enter text to synthesize...',
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 16),
            
            // Synthesis button
            ElevatedButton(
              onPressed: _isLoading ? null : _synthesize,
              child: _isLoading
                  ? CircularProgressIndicator()
                  : Text('Synthesize'),
            ),
          ],
        ),
      ),
    );
  }
  
  @override
  void dispose() {
    _textController.dispose();
    super.dispose();
  }
}
```

---

## Best Practices

### 1. Authentication & Token Management

```dart
// ✅ DO: Securely store tokens
await secureStorage.write(key: 'auth_token', value: token);
final token = await secureStorage.read(key: 'auth_token');

// ❌ DON'T: Store tokens in SharedPreferences (unencrypted)
prefs.setString('auth_token', token);

// ✅ DO: Refresh token on app startup
void initState() {
  super.initState();
  _checkAuthStatus();
}

Future<void> _checkAuthStatus() async {
  final token = await secureStorage.read(key: 'auth_token');
  if (token != null) {
    // Token exists, check if valid
  } else {
    // Redirect to login
  }
}
```

### 2. Error Handling

```dart
// ✅ DO: Specific error handling
try {
  await createTTSJob(text, voiceId);
} on FormatException {
  showError('Invalid response format');
} on SocketException {
  showError('Network error. Check connection.');
} on TimeoutException {
  showError('Request timeout');
} catch (e) {
  showError('Unknown error: $e');
}

// ❌ DON'T: Generic error handling
try {
  // ...
} catch (e) {
  showError('Error');
}
```

### 3. Network Requests

```dart
// ✅ DO: Add timeouts
final response = await http.get(
  Uri.parse(url),
  headers: headers,
).timeout(
  Duration(seconds: 30),
  onTimeout: () => throw TimeoutException('Request timeout'),
);

// ✅ DO: Check status codes
if (response.statusCode == 200) {
  // Success
} else if (response.statusCode == 401) {
  // Unauthorized - refresh token or logout
} else if (response.statusCode == 403) {
  // Forbidden - access denied
} else {
  // Other error
}

// ❌ DON'T: Assume 2xx status without checking
final data = jsonDecode(response.body);
```

### 4. Async Job Polling

```dart
// ✅ DO: Implement intelligent polling
Future<String?> waitForCompletion(String jobId) async {
  int attemptCount = 0;
  const maxAttempts = 120; // 2 minutes with 1 sec interval
  const interval = Duration(seconds: 1);
  
  while (attemptCount < maxAttempts) {
    try {
      final job = await getJob(jobId);
      
      if (job['status'] == 'completed') {
        return job['audio_url'];
      }
      
      if (job['status'] == 'failed') {
        throw Exception('Synthesis failed');
      }
      
      attemptCount++;
      await Future.delayed(interval);
    } catch (e) {
      print('Poll error: $e');
      await Future.delayed(interval);
    }
  }
  
  throw Exception('Job timeout');
}

// ❌ DON'T: Poll too frequently
// This wastes bandwidth and server resources
while (true) {
  final job = await getJob(jobId);
  // No delay - bad!
}
```

### 5. Text Validation

```dart
// ✅ DO: Validate before sending
bool validateText(String text) {
  if (text.isEmpty) return false;
  if (text.length > 5000) return false; // Max 5000 chars
  return true;
}

String sanitizeText(String text) {
  return text
      .trim() // Remove whitespace
      .replaceAll(RegExp(r'\s+'), ' ') // Normalize spaces
      .trim();
}

// ❌ DON'T: Send unvalidated text
await createJob(userInput, voiceId);
```

### 6. Caching

```dart
// ✅ DO: Cache voices list
class VoiceProvider {
  List<Voice>? _cachedVoices;
  
  Future<List<Voice>> getVoices() async {
    if (_cachedVoices != null) {
      return _cachedVoices!;
    }
    
    _cachedVoices = await _ttsService.getVoices();
    return _cachedVoices!;
  }
  
  void clearCache() => _cachedVoices = null;
}
```

---

## Troubleshooting

### Common Issues

#### 1. "Invalid credentials" on Login
**Problem:** Email or password is incorrect
```dart
// Debug: Check email format
if (!email.contains('@')) {
  showError('Invalid email format');
  return;
}

// Solution: Case-sensitive email
final normalizedEmail = email.toLowerCase();
```

#### 2. "Email not verified"
**Problem:** User hasn't verified email yet
```dart
// Solution: Show verification screen
Navigator.push(context, MaterialPageRoute(
  builder: (_) => VerifyEmailScreen(email: email),
));
```

#### 3. "Token expired"
**Problem:** JWT token expired (7 days)
```dart
// Solution: Automatically handle expiration
if (response.statusCode == 401) {
  // Clear token and redirect to login
  await secureStorage.delete(key: 'auth_token');
  Navigator.of(context).pushReplacementNamed('/login');
}
```

#### 4. "Access denied" on Job Access
**Problem:** Accessing another user's job
```dart
// Cause: user_id mismatch
// Solution: Never access jobs other than current user's
// Jobs are automatically filtered in list endpoint
// Direct access returns 403 Forbidden
```

#### 5. Network Timeout
**Problem:** Request takes too long or server not responding
```dart
// Solution: Check connectivity first
import 'package:connectivity_plus/connectivity_plus.dart';

Future<bool> hasConnection() async {
  final result = await Connectivity().checkConnectivity();
  return result != ConnectivityResult.none;
}

// Then add timeout to requests
.timeout(Duration(seconds: 30))
```

#### 6. CORS Issues (if testing from web)
**Problem:** Cross-origin requests blocked
```
Access-Control-Allow-Origin header missing
```
**Solution:** Server must enable CORS (contact backend team)
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
```

---

## API Rate Limits

Currently no strict rate limits, but recommended practices:

- **TTS Synthesis:** Max 100 requests per hour
- **Job List:** Max 10 requests per minute
- **Voice List:** Cache result, request max once per session
- **Polling:** Max 2-second interval (don't poll faster)

---

## Support & Contact

For API issues or questions:
- Email: support@ttsapp.com
- Documentation: https://your-domain.com/docs
- GitHub Issues: https://github.com/your-org/tts-app

---

**Last Updated:** January 29, 2026  
**API Version:** 2.0  
**Status:** Production Ready ✓

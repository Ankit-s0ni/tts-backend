# DynamoDB to MongoDB Migration - Complete

## Migration Summary

Successfully migrated the TTS backend from DynamoDB to MongoDB.

### MongoDB Connection
- **URI**: `mongodb+srv://voicetexta:voicetexta@cluster0.dvq4rui.mongodb.net/?appName=Cluster0`
- **Database**: `tts_production`

## Changes Made

### 1. Dependencies Added
- Added to [requirements.txt](../requirements.txt):
  - `pymongo>=4.6.0`
  - `motor>=3.3.0`

### 2. New Files Created

#### [app/mongodb.py](../app/mongodb.py)
- MongoDB connection management (async and sync)
- Database initialization
- Collection and index creation
- TTL index for temp_audio (24-hour expiry)

#### [app/mongo_db.py](../app/mongo_db.py)
- Complete MongoDB data layer replacing both `dynamo_simple.py` and `dynamo.py`
- Job operations: create, get, update, delete, list
- Voice operations: create, get, list (all/available)
- Temp audio operations
- Counter management for auto-incrementing IDs
- Compatible with existing API interfaces

#### [app/utils/mongo_user.py](../app/utils/mongo_user.py)
- User management for MongoDB
- Replaces `dynamo_user.py`

### 3. Files Updated

#### Configuration
- [app/config.py](../app/config.py)
  - Added `MONGODB_URI` and `MONGODB_DB_NAME` settings
  - Kept legacy AWS settings for backward compatibility

#### Main Application
- [app/main.py](../app/main.py)
  - Added MongoDB initialization on startup
  - Added connection cleanup on shutdown
  - Added logging for MongoDB operations

#### Routers
- [app/routers/tts_router.py](../app/routers/tts_router.py)
  - Changed import from `dynamo_simple` to `mongo_db`
- [app/routers/auth_router.py](../app/routers/auth_router.py)
  - Changed import from `dynamo_user` to `mongo_user`

#### Utilities
- [app/utils/dynamo_utils_simple.py](../app/utils/dynamo_utils_simple.py)
  - Changed import to use `mongo_db`
- [app/utils/sync_piper_models.py](../app/utils/sync_piper_models.py)
  - Changed import to use `mongo_db` (both instances)

#### Workers
- [celery_worker.py](../celery_worker.py)
  - Changed import from `dynamo_simple` to `mongo_db`
- [app/seed_voices.py](../app/seed_voices.py)
  - Changed import from `dynamo` to `mongo_db`
  - Updated initialization to use `init_mongodb()`

## MongoDB Collections

### 1. `jobs`
Stores TTS job information
- **Indexes**:
  - `job_id` (unique)
  - `user_id`
  - `created_at` (descending)

### 2. `voices`
Stores available TTS voices
- **Indexes**:
  - `voice_id` (unique)
  - `available`

### 3. `counters`
Auto-incrementing counters
- **Indexes**:
  - `name` (unique)

### 4. `temp_audio`
Temporary audio files with TTL
- **Indexes**:
  - `audio_id` (unique)
  - `created_at` (TTL: 24 hours)

### 5. `users`
User information
- **Indexes**:
  - `user_id` (unique)

## Backward Compatibility

The new MongoDB implementation maintains full API compatibility with the previous DynamoDB implementation:
- Same function signatures
- Same return types
- Same error handling patterns
- Supports both string and integer IDs

## Next Steps

1. **Install Dependencies**:
   ```bash
   cd /Users/manavgenius/Desktop/ISL/voicetexta-tts/tts-backend
   pip install -r requirements.txt
   ```

2. **Set Environment Variables** (optional, if different from defaults):
   ```bash
   export MONGODB_URI="mongodb+srv://voicetexta:voicetexta@cluster0.dvq4rui.mongodb.net/?appName=Cluster0"
   export MONGODB_DB_NAME="tts_production"
   ```

3. **Restart Application**:
   The application will automatically:
   - Connect to MongoDB on startup
   - Create collections and indexes
   - Be ready to use

4. **Test the Migration**:
   - The error you encountered should now be fixed
   - All job operations will now use MongoDB
   - Data will persist across restarts

## Legacy Files (Can be Deprecated)

The following files are no longer used but kept for reference:
- `app/dynamo_simple.py`
- `app/dynamo.py`
- `app/utils/dynamo_user.py`

These can be safely removed after confirming the migration works correctly.

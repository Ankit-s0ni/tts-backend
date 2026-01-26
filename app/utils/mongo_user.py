"""MongoDB user utilities - replaces dynamo_user.py"""
from datetime import datetime
from typing import Optional, Dict
from ..mongodb import get_sync_database


def _get_collection():
    """Get users collection from MongoDB."""
    db = get_sync_database()
    return db.users


def get_user(user_id: str) -> Optional[Dict]:
    """Get user by ID.
    
    Args:
        user_id: User ID
    
    Returns:
        User document or None
    """
    collection = _get_collection()
    user = collection.find_one({"user_id": str(user_id)})
    
    if user and "_id" in user:
        user["_id"] = str(user["_id"])
    
    return user


def create_or_update_user(user_id: str, email: str, data: dict = None) -> Dict:
    """Create or update a user record in MongoDB.

    Fields updated: full_name, phone, age, profile_image, updated_at
    Ensures created_at is set on first create.
    Returns the new/updated item.
    
    Args:
        user_id: User ID
        email: User email
        data: Additional user data
    
    Returns:
        User document
    """
    collection = _get_collection()
    now = datetime.utcnow().isoformat()
    
    if data is None:
        data = {}
    
    # Build update document
    update_doc = {
        "email": email,
        "updated_at": now
    }
    
    # Add optional fields if present
    for field in ["full_name", "phone", "age", "profile_image"]:
        if field in data and data[field] is not None:
            update_doc[field] = data[field]
    
    # Upsert user with created_at only on insert
    user = collection.find_one_and_update(
        {"user_id": str(user_id)},
        {
            "$set": update_doc,
            "$setOnInsert": {"created_at": now}
        },
        upsert=True,
        return_document=True
    )
    
    if user and "_id" in user:
        user["_id"] = str(user["_id"])
    
    return user


def list_users(limit: int = 100) -> list:
    """List all users.
    
    Args:
        limit: Maximum number of users to return
    
    Returns:
        List of user documents
    """
    collection = _get_collection()
    users = list(collection.find().limit(limit))
    
    for user in users:
        if "_id" in user:
            user["_id"] = str(user["_id"])
    
    return users


def delete_user(user_id: str) -> bool:
    """Delete a user.
    
    Args:
        user_id: User ID
    
    Returns:
        True if deleted, False otherwise
    """
    collection = _get_collection()
    result = collection.delete_one({"user_id": str(user_id)})
    return result.deleted_count > 0

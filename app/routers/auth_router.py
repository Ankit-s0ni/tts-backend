from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
from ..auth import get_current_user
from .. import schemas
from ..utils.dynamo_user import get_user, create_or_update_user
router = APIRouter(prefix="/auth", tags=["auth"])
# Public router for top-level endpoints (not under /auth prefix)
public_router = APIRouter()


@router.get("/info")
def info():
    """Informational endpoint: this application uses AWS Cognito for auth."""
    return {"auth": "cognito", "note": "Registration and login are handled by Cognito; do not call /auth/register or /auth/login"}


@router.post("/register")
def register_disabled():
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="Registration is handled by Cognito User Pools")


@router.post("/login")
def login_disabled():
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="Login is handled by Cognito; acquire tokens from Cognito and pass them as Authorization: Bearer <token>")



@router.get("/me")
def me(current_user=Depends(get_current_user)):
    """Return the verified Cognito claims for the caller."""
    return {"sub": getattr(current_user, "id", None), "email": getattr(current_user, "email", None), "claims": current_user.claims}



@router.post("/link-profile", response_model=schemas.UserProfileResponse)
def link_profile(payload: schemas.UserProfileUpdate, current_user=Depends(get_current_user)):
    """Link or update a user profile stored in DynamoDB using Cognito identity."""
    # current_user contains claims
    user_id = getattr(current_user, "id", None) or current_user.claims.get("sub")
    email = getattr(current_user, "email", None) or current_user.claims.get("email")
    if not user_id or not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing user identity in token")

    data = payload.dict(exclude_unset=True)
    saved = create_or_update_user(user_id, email, data)
    # Ensure response contains expected fields
    return {
        "user_id": str(saved.get("user_id", user_id)),
        "email": saved.get("email", email),
        "full_name": saved.get("full_name"),
        "phone": saved.get("phone"),
        "age": saved.get("age"),
        "profile_image": saved.get("profile_image"),
        "created_at": saved.get("created_at"),
        "updated_at": saved.get("updated_at"),
    }


@public_router.get("/users/me/profile", response_model=schemas.UserProfileResponse)
def get_my_profile(current_user=Depends(get_current_user)):
    user_id = getattr(current_user, "id", None) or current_user.claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing user identity in token")
    usr = get_user(user_id)
    if not usr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return {
        "user_id": str(usr.get("user_id", user_id)),
        "email": usr.get("email"),
        "full_name": usr.get("full_name"),
        "phone": usr.get("phone"),
        "age": usr.get("age"),
        "profile_image": usr.get("profile_image"),
        "created_at": usr.get("created_at"),
        "updated_at": usr.get("updated_at"),
    }

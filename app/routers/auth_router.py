from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
from pydantic import BaseModel
from pycognito import Cognito
from pycognito.exceptions import SoftwareTokenMFAChallengeException, SMSMFAChallengeException
import os
from ..auth import get_current_user
from .. import schemas
from ..utils.mongo_user import get_user, create_or_update_user

router = APIRouter(prefix="/auth", tags=["auth"])
# Public router for top-level endpoints (not under /auth prefix)
public_router = APIRouter()

# Cognito configuration
USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
CLIENT_ID = os.getenv('COGNITO_APP_CLIENT_ID')
AWS_REGION = os.getenv('AWS_REGION', 'ap-south-1')


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ConfirmSignupRequest(BaseModel):
    email: str
    confirmation_code: str
    password: str


class ResendCodeRequest(BaseModel):
    email: str


@router.get("/info")
def info():
    """Informational endpoint: this application uses AWS Cognito for auth."""
    return {"auth": "cognito", "note": "Registration and login use Cognito User Pools"}


@router.post("/register")
def register(payload: RegisterRequest):
    """Register a new user with AWS Cognito."""
    if not all([USER_POOL_ID, CLIENT_ID, AWS_REGION]):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cognito configuration is missing"
        )
    
    try:
        user = Cognito(
            USER_POOL_ID,
            CLIENT_ID,
            username=payload.email,
            user_pool_region=AWS_REGION
        )
        
        # Register the user
        user.register(username=payload.email, password=payload.password)
        
        return {
            "message": "User registered successfully. Please check your email for verification code.",
            "email": payload.email
        }
    
    except Exception as e:
        error_msg = str(e)
        if "UsernameExistsException" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )
        elif "InvalidPasswordException" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet requirements"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {error_msg}"
            )


@router.post("/confirm-signup")
def confirm_signup(payload: ConfirmSignupRequest):
    """Confirm user signup with verification code."""
    if not all([USER_POOL_ID, CLIENT_ID, AWS_REGION]):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cognito configuration is missing"
        )
    
    try:
        user = Cognito(
            USER_POOL_ID,
            CLIENT_ID,
            username=payload.email,
            user_pool_region=AWS_REGION
        )
        
        # Confirm the signup with the verification code
        user.confirm_sign_up(payload.confirmation_code, username=payload.email)
        
        # Authenticate the user after successful verification
        user.authenticate(password=payload.password)
        
        # Create or update user in DynamoDB
        create_or_update_user(user_id=payload.email, email=payload.email, data={})
        
        return {
            "message": "Email verified successfully",
            "access_token": user.access_token,
            "id_token": user.id_token,
            "refresh_token": user.refresh_token
        }
    
    except Exception as e:
        error_msg = str(e)
        if "CodeMismatchException" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
        elif "ExpiredCodeException" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired"
            )
        elif "NotAuthorizedException" in error_msg and "CONFIRMED" in error_msg:
            # User is already confirmed, just authenticate them
            try:
                user = Cognito(
                    USER_POOL_ID,
                    CLIENT_ID,
                    username=payload.email,
                    user_pool_region=AWS_REGION
                )
                user.authenticate(password=payload.password)
                
                # Create or update user in DynamoDB
                create_or_update_user(user_id=payload.email, email=payload.email, data={})
                
                return {
                    "message": "User already verified. Logged in successfully.",
                    "access_token": user.access_token,
                    "id_token": user.id_token,
                    "refresh_token": user.refresh_token
                }
            except Exception as auth_error:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User already verified but authentication failed: {str(auth_error)}"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Verification failed: {error_msg}"
            )


@router.post("/resend-confirmation-code")
def resend_confirmation_code(payload: ResendCodeRequest):
    """Resend verification code to user's email."""
    if not all([USER_POOL_ID, CLIENT_ID, AWS_REGION]):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cognito configuration is missing"
        )
    
    try:
        user = Cognito(
            USER_POOL_ID,
            CLIENT_ID,
            username=payload.email,
            user_pool_region=AWS_REGION
        )
        
        # Resend the confirmation code
        user.client.resend_confirmation_code(
            ClientId=CLIENT_ID,
            Username=payload.email
        )
        
        return {
            "message": f"Verification code sent to {payload.email}"
        }
    
    except Exception as e:
        error_msg = str(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to resend code: {error_msg}"
        )


@router.post("/login")
def login(payload: LoginRequest):
    """Login a user with AWS Cognito."""
    if not all([USER_POOL_ID, CLIENT_ID, AWS_REGION]):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cognito configuration is missing"
        )
    
    try:
        user = Cognito(
            USER_POOL_ID,
            CLIENT_ID,
            username=payload.email,
            user_pool_region=AWS_REGION
        )
        
        # Authenticate the user
        user.authenticate(password=payload.password)
        
        return {
            "message": "Login successful",
            "access_token": user.access_token,
            "id_token": user.id_token,
            "refresh_token": user.refresh_token
        }
    
    except (SoftwareTokenMFAChallengeException, SMSMFAChallengeException):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="MFA is not supported in this implementation"
        )
    except Exception as e:
        error_msg = str(e)
        if "NotAuthorizedException" in error_msg or "UserNotFoundException" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Login failed: {error_msg}"
            )



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

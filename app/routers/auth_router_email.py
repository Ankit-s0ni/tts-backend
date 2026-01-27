"""
Email-based authentication router (replaces Cognito).
Handles registration, login, email verification, and password reset.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from datetime import timedelta

from ..db import get_db
from ..auth_email import (
    create_user,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_current_verified_user,
    create_verification_code,
    verify_code,
    get_password_hash,
    EmailUser
)
from ..models import User
from ..utils.email_service import (
    send_verification_email,
    send_password_reset_email,
    send_welcome_email
)

router = APIRouter(prefix="/auth", tags=["auth"])
# Public router for top-level endpoints (not under /auth prefix)
public_router = APIRouter()


# Request/Response Models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    
    @validator('password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        """Validate password length for bcrypt compatibility."""
        password_bytes = len(v.encode('utf-8'))
        if password_bytes > 72:
            raise ValueError(f"Password is too long ({password_bytes} bytes). Maximum length is 72 bytes.")
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str


class ResendCodeRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str
    
    @validator('new_password')
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        """Validate password length for bcrypt compatibility."""
        password_bytes = len(v.encode('utf-8'))
        if password_bytes > 72:
            raise ValueError(f"Password is too long ({password_bytes} bytes). Maximum length is 72 bytes.")
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    is_verified: bool
    is_active: bool


@router.get("/info")
def info():
    """Informational endpoint about authentication."""
    return {
        "auth": "email",
        "note": "Registration and login use email/password with verification codes"
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user with email and password.
    Sends a verification code to the email.
    Password requirements: 8-72 bytes (validated by Pydantic).
    """
    try:
        # Create user (will raise ValueError if email exists or password invalid)
        user = create_user(
            db=db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name
        )
        
        # Generate verification code
        code = create_verification_code(
            db=db,
            email=payload.email,
            code_type="email_verification"
        )
        
        # Send verification email
        email_sent = send_verification_email(
            to_email=payload.email,
            verification_code=code,
            user_name=payload.full_name
        )
        
        if not email_sent:
            # Log warning but don't fail registration
            print(f"Warning: Failed to send verification email to {payload.email}")
        
        return {
            "message": "Registration successful. Please check your email for verification code.",
            "email": payload.email,
            "user_id": user.id
        }
        
    except ValueError as e:
        # Handle validation errors (email exists, password too long, etc.)
        error_msg = str(e)
        print(f"Registration validation error: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        # Handle unexpected errors
        error_msg = str(e)
        print(f"Registration error: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {error_msg}"
        )


@router.post("/verify-email")
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    """
    Verify user's email with the verification code.
    """
    # Verify the code
    is_valid = verify_code(
        db=db,
        email=payload.email,
        code=payload.code,
        code_type="email_verification"
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    # Update user verification status
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_verified = True
    db.commit()
    
    # Send welcome email
    send_welcome_email(to_email=payload.email, user_name=user.full_name or "User")
    
    # Generate access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "message": "Email verified successfully",
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/resend-verification-code")
def resend_verification_code(payload: ResendCodeRequest, db: Session = Depends(get_db)):
    """
    Resend verification code to user's email.
    """
    # Check if user exists
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # Don't reveal if user exists or not
        return {"message": f"If an account exists for {payload.email}, a verification code has been sent."}
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Generate new verification code
    code = create_verification_code(
        db=db,
        email=payload.email,
        code_type="email_verification"
    )
    
    # Send verification email
    email_sent = send_verification_email(
        to_email=payload.email,
        verification_code=code,
        user_name=user.full_name
    )
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )
    
    return {"message": f"Verification code sent to {payload.email}"}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email and password.
    Returns access token.
    """
    user = authenticate_user(db=db, email=payload.email, password=payload.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Generate access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Request a password reset code.
    """
    # Check if user exists
    user = db.query(User).filter(User.email == payload.email).first()
    
    # Don't reveal if user exists or not (security best practice)
    if not user:
        return {"message": f"If an account exists for {payload.email}, a password reset code has been sent."}
    
    # Generate reset code
    code = create_verification_code(
        db=db,
        email=payload.email,
        code_type="password_reset"
    )
    
    # Send reset email
    email_sent = send_password_reset_email(
        to_email=payload.email,
        reset_code=code,
        user_name=user.full_name
    )
    
    if not email_sent:
        print(f"Warning: Failed to send password reset email to {payload.email}")
    
    return {"message": f"If an account exists for {payload.email}, a password reset code has been sent."}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password using the reset code.
    Password is automatically validated by Pydantic (8-72 bytes).
    """
    # Verify the reset code
    is_valid = verify_code(
        db=db,
        email=payload.email,
        code=payload.code,
        code_type="password_reset"
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code"
        )
    
    # Update user password
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    
    return {"message": "Password reset successfully"}


@router.get("/me", response_model=UserResponse)
def me(current_user: EmailUser = Depends(get_current_user)):
    """
    Get current user information.
    """
    return {
        "id": int(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_verified": current_user.is_verified,
        "is_active": current_user.is_active
    }


@router.put("/me")
def update_profile(
    payload: dict,
    current_user: EmailUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile (full_name, etc).
    """
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update allowed fields
    if "full_name" in payload and payload["full_name"]:
        user.full_name = payload["full_name"]
    
    db.commit()
    db.refresh(user)
    
    return {
        "id": int(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_verified": user.is_verified,
        "is_active": user.is_active
    }


@router.post("/link-profile")
def link_profile(
    payload: dict,
    current_user: EmailUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile (alias for PUT /auth/me for backward compatibility).
    Accepts: full_name, phone, age, profile_image
    """
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update allowed fields
    if "full_name" in payload and payload["full_name"]:
        user.full_name = payload["full_name"]
    
    db.commit()
    db.refresh(user)
    
    return {
        "id": int(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_verified": user.is_verified,
        "is_active": user.is_active
    }


@public_router.get("/users/me/profile", response_model=UserResponse)
def get_my_profile(current_user: EmailUser = Depends(get_current_verified_user)):
    """
    Get user profile (requires verified email).
    """
    return {
        "id": int(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_verified": current_user.is_verified,
        "is_active": current_user.is_active
    }

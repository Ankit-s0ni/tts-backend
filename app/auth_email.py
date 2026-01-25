"""
Email-based authentication system to replace AWS Cognito.
Handles user registration, login, email verification, and password reset.
"""
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .db import get_db
from .models import User, VerificationCode

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class EmailUser:
    """User object for email-based authentication"""
    def __init__(self, user_db_model: User):
        self.id = str(user_db_model.id)
        self.email = user_db_model.email
        self.full_name = user_db_model.full_name
        self.is_active = user_db_model.is_active
        self.is_verified = user_db_model.is_verified
        self._db_model = user_db_model

    def __repr__(self):
        return f"EmailUser(id={self.id}, email={self.email})"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def generate_verification_code() -> str:
    """Generate a 6-digit verification code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def create_verification_code(
    db: Session,
    email: str,
    code_type: str,
    expiration_minutes: int = 15
) -> str:
    """
    Create a verification code for email verification or password reset.
    
    Args:
        db: Database session
        email: User's email
        code_type: "email_verification" or "password_reset"
        expiration_minutes: Code expiration time in minutes
    
    Returns:
        The generated verification code
    """
    code = generate_verification_code()
    expires_at = datetime.utcnow() + timedelta(minutes=expiration_minutes)
    
    # Invalidate any existing unused codes of the same type for this email
    db.query(VerificationCode).filter(
        VerificationCode.email == email,
        VerificationCode.code_type == code_type,
        VerificationCode.is_used == False
    ).update({"is_used": True})
    
    # Create new verification code
    db_code = VerificationCode(
        email=email,
        code=code,
        code_type=code_type,
        expires_at=expires_at
    )
    db.add(db_code)
    db.commit()
    
    return code


def verify_code(
    db: Session,
    email: str,
    code: str,
    code_type: str
) -> bool:
    """
    Verify a verification code.
    
    Args:
        db: Database session
        email: User's email
        code: The code to verify
        code_type: "email_verification" or "password_reset"
    
    Returns:
        True if code is valid, False otherwise
    """
    db_code = db.query(VerificationCode).filter(
        VerificationCode.email == email,
        VerificationCode.code == code,
        VerificationCode.code_type == code_type,
        VerificationCode.is_used == False
    ).first()
    
    if not db_code:
        return False
    
    # Check if expired
    if datetime.utcnow() > db_code.expires_at:
        return False
    
    # Mark as used
    db_code.is_used = True
    db.commit()
    
    return True


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password.
    
    Returns:
        User model if authentication successful, None otherwise
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> EmailUser:
    """
    Get the current authenticated user from JWT token.
    
    Raises:
        HTTPException: If token is invalid or user not found
    
    Returns:
        EmailUser object
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return EmailUser(user)


def get_current_verified_user(
    current_user: EmailUser = Depends(get_current_user)
) -> EmailUser:
    """
    Get the current user and ensure they are verified.
    
    Raises:
        HTTPException: If user is not verified
    
    Returns:
        EmailUser object
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email to access this resource."
        )
    return current_user


def create_user(db: Session, email: str, password: str, full_name: Optional[str] = None) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session
        email: User's email
        password: Plain text password (will be hashed)
        full_name: User's full name
    
    Returns:
        Created User model
    
    Raises:
        ValueError: If email already exists
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise ValueError("Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(password)
    db_user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        is_verified=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

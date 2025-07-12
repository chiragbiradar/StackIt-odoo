"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging

from ...database import get_db
from ...models.user import User
from ...schemas.user import UserRegister, UserLogin, Token, UserResponse
from ...schemas.common import MessageResponse
from ...auth.password import hash_password, verify_password
from ...auth.jwt import create_user_token
from ...auth.dependencies import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Strong password (8+ characters with uppercase, lowercase, digit)
    - **confirm_password**: Must match password
    - **full_name**: Optional full name
    - **bio**: Optional user biography
    """
    # Check if username already exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        bio=user_data.bio,
        avatar_url=user_data.avatar_url,
        is_active=True,
        is_verified=False  # Email verification required
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"New user registered: {user_data.username}")
    
    # Create and return token
    return create_user_token(db_user)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with username/email and password.
    
    - **username**: Username or email address
    - **password**: User password
    
    Returns JWT access token for authenticated requests.
    """
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    logger.info(f"User logged in: {user.username}")
    
    # Create and return token
    return create_user_token(user)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout current user.
    
    Note: Since we're using stateless JWT tokens, logout is handled client-side
    by removing the token. This endpoint is provided for consistency.
    """
    logger.info(f"User logged out: {current_user.username}")
    
    return MessageResponse(
        message="Successfully logged out",
        success=True
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.
    
    Returns detailed information about the currently authenticated user.
    """
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_active_user)
):
    """
    Refresh the current access token.
    
    Returns a new JWT access token with extended expiration time.
    """
    logger.info(f"Token refreshed for user: {current_user.username}")
    
    return create_user_token(current_user)


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify user email address with verification token.
    
    - **token**: Email verification token
    
    Note: This is a placeholder. In a real implementation, you would:
    1. Generate verification tokens during registration
    2. Send verification emails
    3. Validate tokens and mark users as verified
    """
    # TODO: Implement email verification logic
    # For now, this is a placeholder
    
    return MessageResponse(
        message="Email verification not implemented yet",
        success=False
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Request password reset for email address.
    
    - **email**: User's email address
    
    Note: This is a placeholder. In a real implementation, you would:
    1. Generate password reset tokens
    2. Send password reset emails
    3. Provide reset endpoint to change password
    """
    user = db.query(User).filter(User.email == email).first()
    
    # Always return success to prevent email enumeration
    return MessageResponse(
        message="If the email exists, a password reset link has been sent",
        success=True
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    """
    Reset password with reset token.
    
    - **token**: Password reset token
    - **new_password**: New password
    
    Note: This is a placeholder for password reset functionality.
    """
    # TODO: Implement password reset logic
    
    return MessageResponse(
        message="Password reset not implemented yet",
        success=False
    )

"""
Authentication Service for StackIt Q&A platform.
Handles user registration, login, and authentication.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

# Import database dependencies
from database import get_db
from database.models import User

# Import schemas
from schemas.auth import AuthResponse, Token, UserLogin, UserRegister, UserResponse

# Import authentication utilities
from utils.auth import (
    authenticate_user,
    create_user_token,
    get_current_user_id,
    get_password_hash,
)

# OAuth2 scheme for token extraction
oauth2_scheme = HTTPBearer()

# Create router
router = APIRouter()


# Dependency to get current user from JWT token
async def get_current_user_dependency(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        user_id = get_current_user_id(token.credentials)

        if user_id is None:
            raise credentials_exception

        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception

        return user

    except Exception:
        raise credentials_exception from None


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.

    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Password (minimum 6 characters)
    - **full_name**: Optional full name
    - **bio**: Optional user biography
    """
    try:
        # Check if username already exists
        existing_user = db.query(User).filter(
            (User.username == user_data.username) | (User.email == user_data.email)
        ).first()

        if existing_user:
            if existing_user.username == user_data.username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )

        # Hash the password
        hashed_password = get_password_hash(user_data.password)

        # Create new user
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            bio=user_data.bio,
            is_active=True,
            is_verified=False,
            role="USER",
            reputation_score=0,
            questions_count=0,
            answers_count=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        # Save to database
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Create token
        token_data = create_user_token(new_user)

        # Prepare response
        user_response = UserResponse.model_validate(new_user)
        token_response = Token(**token_data)

        return AuthResponse(
            user=user_response,
            token=token_response,
            message="User registered successfully"
        )

    except HTTPException:
        # Re-raise HTTPExceptions (like the username/email check above)
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        ) from e


@router.post("/login", response_model=AuthResponse)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token.

    - **username**: Username or email address
    - **password**: User password
    """
    try:
        # Authenticate user
        user = authenticate_user(db, login_data.username, login_data.password)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update last login time (optional)
        user.updated_at = datetime.now(timezone.utc)
        db.commit()

        # Create token
        token_data = create_user_token(user)

        # Prepare response
        user_response = UserResponse.model_validate(user)
        token_response = Token(**token_data)

        return AuthResponse(
            user=user_response,
            token=token_response,
            message="Login successful"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during login: {str(e)}"
        ) from e


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(get_current_user_dependency)
):
    """
    Get current authenticated user information.
    Requires valid JWT token in Authorization header.
    """
    return UserResponse.model_validate(current_user)

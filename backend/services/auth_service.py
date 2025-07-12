"""
Authentication service for StackIt Q&A platform.
Integrated from feature/auth branch with adaptations for current structure.
"""
from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..app.database import get_db
from ..app.models.user import User
from ..app.auth.password import hash_password, verify_password
from ..app.auth.jwt import create_access_token, verify_token
from ..app.schemas.user import UserCreate, UserResponse, Token

security = HTTPBearer()


class AuthService:
    """Authentication service class."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def register_user(self, user_data: UserCreate) -> Token:
        """
        Register a new user.
        
        Args:
            user_data: User registration data
            
        Returns:
            Token: JWT token response
            
        Raises:
            HTTPException: If username or email already exists
        """
        # Check if username already exists
        if self.db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        if self.db.query(User).filter(User.email == user_data.email).first():
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
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        # Create token
        return self._create_user_token(db_user)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username/email and password.
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            User: User object if authentication successful, None otherwise
        """
        # Try to find user by username or email
        user = self.db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def login_user(self, username: str, password: str) -> Token:
        """
        Login a user and return JWT token.
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            Token: JWT token response
            
        Raises:
            HTTPException: If authentication fails
        """
        user = self.authenticate_user(username, password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )
        
        return self._create_user_token(user)
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials) -> User:
        """
        Get current user from JWT token.
        
        Args:
            credentials: HTTP authorization credentials
            
        Returns:
            User: Current user object
            
        Raises:
            HTTPException: If authentication fails
        """
        token = credentials.credentials
        token_data = verify_token(token)
        
        user_id = token_data.user_id
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    def _create_user_token(self, user: User) -> Token:
        """
        Create a JWT token for a user.
        
        Args:
            user: User object
            
        Returns:
            Token: JWT token response
        """
        from ..app.config import settings
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        
        token_data = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value
        }
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserResponse.model_validate(user)
        )


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Get authentication service instance."""
    return AuthService(db)


def get_current_user_service(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Get current authenticated user using auth service."""
    return auth_service.get_current_user(credentials)

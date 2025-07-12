"""
User-related Pydantic schemas.
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict, validator
from typing import Optional, List
from datetime import datetime

from ..models.user import UserRole
from .common import BaseResponseModel


class UserBase(BaseModel):
    """Base user schema with common fields."""
    
    username: str = Field(min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(description="User email address")
    full_name: Optional[str] = Field(default=None, max_length=100, description="User's full name")
    bio: Optional[str] = Field(default=None, max_length=1000, description="User biography")
    avatar_url: Optional[str] = Field(default=None, max_length=500, description="Avatar image URL")


class UserCreate(UserBase):
    """Schema for user creation."""
    
    password: str = Field(min_length=8, max_length=100, description="User password")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    """Schema for user updates."""
    
    full_name: Optional[str] = Field(default=None, max_length=100)
    bio: Optional[str] = Field(default=None, max_length=1000)
    avatar_url: Optional[str] = Field(default=None, max_length=500)


class UserResponse(BaseResponseModel):
    """Schema for user responses."""
    
    username: str
    email: EmailStr
    full_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    is_verified: bool
    role: UserRole
    reputation_score: int
    questions_count: int
    answers_count: int
    
    model_config = ConfigDict(from_attributes=True)


class UserProfile(UserResponse):
    """Extended user profile with additional information."""
    
    # Additional profile fields can be added here
    recent_activity: Optional[List[dict]] = Field(default=None, description="Recent user activity")
    badges: Optional[List[str]] = Field(default=None, description="User badges/achievements")


class UserLogin(BaseModel):
    """Schema for user login."""
    
    username: str = Field(description="Username or email")
    password: str = Field(description="User password")


class UserRegister(UserCreate):
    """Schema for user registration."""
    
    confirm_password: str = Field(description="Password confirmation")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Validate that passwords match."""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class Token(BaseModel):
    """JWT token response."""
    
    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(description="Token expiration time in seconds")
    user: UserResponse = Field(description="User information")


class TokenData(BaseModel):
    """Token payload data."""
    
    user_id: int = Field(description="User ID")
    username: str = Field(description="Username")
    role: UserRole = Field(description="User role")
    exp: datetime = Field(description="Token expiration time")


class PasswordChange(BaseModel):
    """Schema for password change."""
    
    current_password: str = Field(description="Current password")
    new_password: str = Field(min_length=8, max_length=100, description="New password")
    confirm_password: str = Field(description="New password confirmation")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Validate that passwords match."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class UserList(BaseModel):
    """Schema for user list items."""
    
    id: int
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    reputation_score: int
    questions_count: int
    answers_count: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserStats(BaseModel):
    """User statistics schema."""
    
    total_questions: int = Field(description="Total questions asked")
    total_answers: int = Field(description="Total answers provided")
    total_votes_received: int = Field(description="Total votes received")
    accepted_answers: int = Field(description="Number of accepted answers")
    reputation_score: int = Field(description="Current reputation score")
    badges_earned: int = Field(description="Number of badges earned")
    join_date: datetime = Field(description="Account creation date")
    last_active: Optional[datetime] = Field(description="Last activity timestamp")

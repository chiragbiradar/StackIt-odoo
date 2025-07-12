"""
Authentication schemas for StackIt Q&A platform.
Pydantic models for authentication requests and responses.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    """Schema for user registration request."""
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, max_length=100, description="Password (minimum 6 characters)")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name (optional)")
    bio: Optional[str] = Field(None, max_length=500, description="User bio (optional)")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "securepassword123",
                "full_name": "John Doe",
                "bio": "Software developer passionate about Q&A platforms"
            }
        }


class UserLogin(BaseModel):
    """Schema for user login request."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "password": "securepassword123"
            }
        }


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class UserResponse(BaseModel):
    """Schema for user data in responses."""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool
    is_verified: bool
    role: str
    reputation_score: int
    questions_count: int
    answers_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "bio": "Software developer",
                "is_active": True,
                "is_verified": False,
                "role": "USER",
                "reputation_score": 0,
                "questions_count": 0,
                "answers_count": 0,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class AuthResponse(BaseModel):
    """Schema for authentication response (login/register)."""
    user: UserResponse
    token: Token
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": 1,
                    "username": "johndoe",
                    "email": "john@example.com",
                    "full_name": "John Doe",
                    "is_active": True,
                    "role": "USER"
                },
                "token": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 1800
                },
                "message": "Login successful"
            }
        }

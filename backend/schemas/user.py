"""
User schemas for StackIt Q&A platform.
Pydantic models for user profile responses.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserProfile(BaseModel):
    """Schema for user profile response."""
    id: int
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
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
                "full_name": "John Doe",
                "bio": "Software developer passionate about Q&A platforms and helping others learn",
                "avatar_url": "https://example.com/avatars/johndoe.jpg",
                "is_active": True,
                "is_verified": True,
                "role": "USER",
                "reputation_score": 1250,
                "questions_count": 15,
                "answers_count": 42,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }

"""
User schemas for StackIt Q&A platform.
Pydantic models for user-related requests and responses.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserProfile(BaseModel):
    """Schema for user profile response."""
    id: int
    username: str
    email: str
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
                "email": "john@example.com",
                "full_name": "John Doe",
                "bio": "Software developer passionate about Q&A platforms",
                "avatar_url": None,
                "is_active": True,
                "is_verified": False,
                "role": "USER",
                "reputation_score": 150,
                "questions_count": 5,
                "answers_count": 12,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class UserStats(BaseModel):
    """Schema for user statistics."""
    questions_count: int
    answers_count: int
    reputation_score: int
    votes_received: int
    accepted_answers: int

    class Config:
        json_schema_extra = {
            "example": {
                "questions_count": 5,
                "answers_count": 12,
                "reputation_score": 150,
                "votes_received": 25,
                "accepted_answers": 3
            }
        }

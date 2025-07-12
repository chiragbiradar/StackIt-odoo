"""
Answer schemas for StackIt Q&A platform.
Pydantic models for answer requests and responses.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AnswerCreate(BaseModel):
    """Schema for creating a new answer."""
    content: str = Field(..., min_length=20, description="Answer content (minimum 20 characters)")
    question_id: int = Field(..., description="ID of the question being answered")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "To implement JWT authentication in FastAPI, you can use the python-jose library along with passlib for password hashing. Here's a step-by-step approach:\n\n1. Install dependencies: pip install python-jose[cryptography] passlib[bcrypt]\n2. Create authentication utilities...",
                "question_id": 1
            }
        }


class AuthorInfo(BaseModel):
    """Schema for answer author information."""
    id: int
    username: str
    full_name: Optional[str] = None
    reputation_score: int

    class Config:
        from_attributes = True


class AnswerResponse(BaseModel):
    """Schema for answer response."""
    id: int
    content: str
    vote_score: int
    comment_count: int
    is_accepted: bool
    question_id: int
    author: AuthorInfo
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "content": "To implement JWT authentication in FastAPI...",
                "vote_score": 8,
                "comment_count": 2,
                "is_accepted": True,
                "question_id": 1,
                "author": {
                    "id": 2,
                    "username": "janedoe",
                    "full_name": "Jane Doe",
                    "reputation_score": 250
                },
                "created_at": "2024-01-01T11:00:00Z",
                "updated_at": "2024-01-01T11:00:00Z"
            }
        }


class AcceptAnswerResponse(BaseModel):
    """Schema for answer acceptance response."""
    message: str
    answer_id: int
    is_accepted: bool

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Answer accepted successfully",
                "answer_id": 1,
                "is_accepted": True
            }
        }

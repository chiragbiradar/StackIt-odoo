"""
Question schemas for StackIt Q&A platform.
Pydantic models for question requests and responses.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class QuestionCreate(BaseModel):
    """Schema for creating a new question."""
    title: str = Field(..., min_length=10, max_length=200, description="Question title (10-200 characters)")
    description: str = Field(..., min_length=20, description="Question description (minimum 20 characters)")
    tag_names: List[str] = Field(..., min_items=1, max_items=5, description="List of tag names (1-5 tags)")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "How to implement authentication in FastAPI?",
                "description": "I'm building a FastAPI application and need to implement JWT-based authentication. What's the best approach for handling user login, token generation, and protecting routes?",
                "tag_names": ["fastapi", "authentication", "jwt", "python"]
            }
        }


class AuthorInfo(BaseModel):
    """Schema for question/answer author information."""
    id: int
    username: str
    full_name: Optional[str] = None
    reputation_score: int

    class Config:
        from_attributes = True


class TagInfo(BaseModel):
    """Schema for tag information in question responses."""
    id: int
    name: str
    color: Optional[str] = None

    class Config:
        from_attributes = True


class QuestionResponse(BaseModel):
    """Schema for question response with full details."""
    id: int
    title: str
    description: str
    view_count: int
    vote_score: int
    answer_count: int
    is_closed: bool
    has_accepted_answer: bool
    author: AuthorInfo
    tags: List[TagInfo]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "How to implement authentication in FastAPI?",
                "description": "I'm building a FastAPI application...",
                "view_count": 42,
                "vote_score": 5,
                "answer_count": 3,
                "is_closed": False,
                "has_accepted_answer": True,
                "author": {
                    "id": 1,
                    "username": "johndoe",
                    "full_name": "John Doe",
                    "reputation_score": 150
                },
                "tags": [
                    {"id": 1, "name": "fastapi", "color": "#009688"},
                    {"id": 2, "name": "authentication", "color": "#FF5722"}
                ],
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z"
            }
        }


class QuestionListItem(BaseModel):
    """Schema for question in list view (simplified)."""
    id: int
    title: str
    description: str
    view_count: int
    vote_score: int
    answer_count: int
    has_accepted_answer: bool
    author: AuthorInfo
    tags: List[TagInfo]
    created_at: datetime

    class Config:
        from_attributes = True


class QuestionList(BaseModel):
    """Schema for paginated question list response."""
    questions: List[QuestionListItem]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

    class Config:
        json_schema_extra = {
            "example": {
                "questions": [
                    {
                        "id": 1,
                        "title": "How to implement authentication in FastAPI?",
                        "description": "I'm building a FastAPI application...",
                        "view_count": 42,
                        "vote_score": 5,
                        "answer_count": 3,
                        "has_accepted_answer": True,
                        "author": {
                            "id": 1,
                            "username": "johndoe",
                            "full_name": "John Doe",
                            "reputation_score": 150
                        },
                        "tags": [
                            {"id": 1, "name": "fastapi", "color": "#009688"}
                        ],
                        "created_at": "2024-01-01T10:00:00Z"
                    }
                ],
                "total": 25,
                "page": 1,
                "per_page": 10,
                "has_next": True,
                "has_prev": False
            }
        }

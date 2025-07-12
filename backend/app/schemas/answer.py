"""
Answer-related Pydantic schemas.
"""
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List
from datetime import datetime

from .common import BaseResponseModel
from .user import UserList


class AnswerBase(BaseModel):
    """Base answer schema with common fields."""
    
    content: str = Field(min_length=20, description="Answer content in rich text")
    
    @validator('content')
    def validate_content(cls, v):
        """Validate answer content."""
        if not v.strip():
            raise ValueError('Answer content cannot be empty')
        return v.strip()


class AnswerCreate(AnswerBase):
    """Schema for answer creation."""
    
    question_id: int = Field(description="ID of the question being answered")


class AnswerUpdate(BaseModel):
    """Schema for answer updates."""
    
    content: Optional[str] = Field(default=None, min_length=20)
    
    @validator('content')
    def validate_content(cls, v):
        """Validate answer content."""
        if v is not None and not v.strip():
            raise ValueError('Answer content cannot be empty')
        return v.strip() if v else v


class AnswerResponse(BaseResponseModel):
    """Schema for answer responses."""
    
    content: str
    vote_score: int
    comment_count: int
    is_accepted: bool
    question_id: int
    author_id: int
    
    # Related data
    author: UserList
    
    model_config = ConfigDict(from_attributes=True)


class AnswerList(BaseModel):
    """Schema for answer list items."""
    
    id: int
    content: str
    vote_score: int
    comment_count: int
    is_accepted: bool
    question_id: int
    created_at: datetime
    updated_at: datetime
    
    # Related data
    author: UserList
    
    model_config = ConfigDict(from_attributes=True)


class AnswerDetail(AnswerResponse):
    """Detailed answer schema with additional information."""
    
    # Additional fields for detailed view
    user_vote: Optional[bool] = Field(default=None, description="Current user's vote (True=upvote, False=downvote, None=no vote)")
    can_accept: bool = Field(default=False, description="Whether current user can accept this answer")
    can_edit: bool = Field(default=False, description="Whether current user can edit this answer")
    can_delete: bool = Field(default=False, description="Whether current user can delete this answer")


class AnswerAccept(BaseModel):
    """Schema for accepting an answer."""
    
    is_accepted: bool = Field(description="Whether to accept or unaccept the answer")


class AnswerSearch(BaseModel):
    """Schema for answer search parameters."""
    
    query: Optional[str] = Field(default=None, min_length=1, max_length=200, description="Search query")
    question_id: Optional[int] = Field(default=None, description="Filter by question ID")
    author_id: Optional[int] = Field(default=None, description="Filter by author ID")
    is_accepted: Optional[bool] = Field(default=None, description="Filter by accepted status")
    min_score: Optional[int] = Field(default=None, description="Minimum vote score")
    sort_by: str = Field(default="created_at", description="Sort field")
    order: str = Field(default="desc", regex="^(asc|desc)$", description="Sort order")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")


class AnswerStats(BaseModel):
    """Answer statistics schema."""
    
    total_votes: int = Field(description="Total votes received")
    upvotes: int = Field(description="Number of upvotes")
    downvotes: int = Field(description="Number of downvotes")
    vote_score: int = Field(description="Net vote score")
    total_comments: int = Field(description="Total number of comments")
    view_count: int = Field(description="Number of times viewed")
    is_accepted: bool = Field(description="Whether answer is accepted")
    acceptance_date: Optional[datetime] = Field(description="Date when answer was accepted")
    last_edited: Optional[datetime] = Field(description="Last edit timestamp")


class AnswerActivity(BaseModel):
    """Answer activity item schema."""
    
    activity_type: str = Field(description="Type of activity")
    user: UserList = Field(description="User who performed the activity")
    timestamp: datetime = Field(description="Activity timestamp")
    description: str = Field(description="Activity description")
    details: Optional[dict] = Field(description="Additional activity details")


class AnswerRanking(BaseModel):
    """Answer ranking schema for sorting."""
    
    answer_id: int
    score: float = Field(description="Calculated ranking score")
    vote_score: int
    age_hours: float = Field(description="Age in hours")
    comment_count: int
    is_accepted: bool
    author_reputation: int

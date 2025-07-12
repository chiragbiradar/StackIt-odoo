"""
Comment-related Pydantic schemas.
"""
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List
from datetime import datetime

from .common import BaseResponseModel
from .user import UserList


class CommentBase(BaseModel):
    """Base comment schema with common fields."""
    
    content: str = Field(min_length=5, max_length=500, description="Comment content")
    
    @validator('content')
    def validate_content(cls, v):
        """Validate comment content."""
        if not v.strip():
            raise ValueError('Comment content cannot be empty')
        return v.strip()


class CommentCreate(CommentBase):
    """Schema for comment creation."""
    
    answer_id: int = Field(description="ID of the answer being commented on")


class CommentUpdate(BaseModel):
    """Schema for comment updates."""
    
    content: Optional[str] = Field(default=None, min_length=5, max_length=500)
    
    @validator('content')
    def validate_content(cls, v):
        """Validate comment content."""
        if v is not None and not v.strip():
            raise ValueError('Comment content cannot be empty')
        return v.strip() if v else v


class CommentResponse(BaseResponseModel):
    """Schema for comment responses."""
    
    content: str
    answer_id: int
    author_id: int
    
    # Related data
    author: UserList
    
    model_config = ConfigDict(from_attributes=True)


class CommentList(BaseModel):
    """Schema for comment list items."""
    
    id: int
    content: str
    answer_id: int
    created_at: datetime
    updated_at: datetime
    
    # Related data
    author: UserList
    
    model_config = ConfigDict(from_attributes=True)


class CommentDetail(CommentResponse):
    """Detailed comment schema with additional information."""
    
    # Additional fields for detailed view
    can_edit: bool = Field(default=False, description="Whether current user can edit this comment")
    can_delete: bool = Field(default=False, description="Whether current user can delete this comment")
    is_edited: bool = Field(default=False, description="Whether comment has been edited")


class CommentSearch(BaseModel):
    """Schema for comment search parameters."""
    
    query: Optional[str] = Field(default=None, min_length=1, max_length=200, description="Search query")
    answer_id: Optional[int] = Field(default=None, description="Filter by answer ID")
    author_id: Optional[int] = Field(default=None, description="Filter by author ID")
    sort_by: str = Field(default="created_at", description="Sort field")
    order: str = Field(default="asc", regex="^(asc|desc)$", description="Sort order")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")


class CommentStats(BaseModel):
    """Comment statistics schema."""
    
    total_comments: int = Field(description="Total number of comments")
    comments_today: int = Field(description="Comments posted today")
    comments_this_week: int = Field(description="Comments posted this week")
    comments_this_month: int = Field(description="Comments posted this month")
    average_comments_per_answer: float = Field(description="Average comments per answer")
    most_commented_answer_id: Optional[int] = Field(description="ID of most commented answer")
    most_active_commenter_id: Optional[int] = Field(description="ID of most active commenter")


class CommentActivity(BaseModel):
    """Comment activity schema."""
    
    comment_id: int
    answer_id: int
    question_id: int
    question_title: str
    content_preview: str = Field(description="First 100 characters of comment")
    timestamp: datetime
    author: UserList
    answer_author: UserList

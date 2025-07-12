"""
Question-related Pydantic schemas.
"""
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List
from datetime import datetime

from .common import BaseResponseModel
from .user import UserList
from .tag import TagResponse


class QuestionBase(BaseModel):
    """Base question schema with common fields."""
    
    title: str = Field(min_length=10, max_length=200, description="Question title")
    description: str = Field(min_length=20, description="Question description in rich text")
    
    @validator('title')
    def validate_title(cls, v):
        """Validate question title."""
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        """Validate question description."""
        if not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()


class QuestionCreate(QuestionBase):
    """Schema for question creation."""
    
    tag_names: List[str] = Field(min_items=1, max_items=5, description="List of tag names")
    
    @validator('tag_names')
    def validate_tags(cls, v):
        """Validate tag names."""
        if not v:
            raise ValueError('At least one tag is required')
        
        # Remove duplicates and empty strings
        cleaned_tags = list(set(tag.strip().lower() for tag in v if tag.strip()))
        
        if not cleaned_tags:
            raise ValueError('At least one valid tag is required')
        
        if len(cleaned_tags) > 5:
            raise ValueError('Maximum 5 tags allowed')
        
        return cleaned_tags


class QuestionUpdate(BaseModel):
    """Schema for question updates."""
    
    title: Optional[str] = Field(default=None, min_length=10, max_length=200)
    description: Optional[str] = Field(default=None, min_length=20)
    tag_names: Optional[List[str]] = Field(default=None, max_items=5)
    is_closed: Optional[bool] = Field(default=None, description="Whether question is closed")
    
    @validator('title')
    def validate_title(cls, v):
        """Validate question title."""
        if v is not None and not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip() if v else v
    
    @validator('description')
    def validate_description(cls, v):
        """Validate question description."""
        if v is not None and not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip() if v else v


class QuestionResponse(BaseResponseModel):
    """Schema for question responses."""
    
    title: str
    description: str
    view_count: int
    vote_score: int
    answer_count: int
    is_closed: bool
    has_accepted_answer: bool
    author_id: int
    accepted_answer_id: Optional[int]
    
    # Related data
    author: UserList
    tags: List[TagResponse]
    
    model_config = ConfigDict(from_attributes=True)


class QuestionList(BaseModel):
    """Schema for question list items."""
    
    id: int
    title: str
    view_count: int
    vote_score: int
    answer_count: int
    is_closed: bool
    has_accepted_answer: bool
    created_at: datetime
    updated_at: datetime
    
    # Related data
    author: UserList
    tags: List[TagResponse]
    
    model_config = ConfigDict(from_attributes=True)


class QuestionDetail(QuestionResponse):
    """Detailed question schema with additional information."""
    
    # Additional fields for detailed view
    recent_activity: Optional[List[dict]] = Field(default=None, description="Recent activity on question")
    related_questions: Optional[List["QuestionList"]] = Field(default=None, description="Related questions")


class QuestionSearch(BaseModel):
    """Schema for question search parameters."""
    
    query: Optional[str] = Field(default=None, min_length=1, max_length=200, description="Search query")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tag names")
    author_id: Optional[int] = Field(default=None, description="Filter by author ID")
    has_accepted_answer: Optional[bool] = Field(default=None, description="Filter by accepted answer status")
    is_closed: Optional[bool] = Field(default=None, description="Filter by closed status")
    sort_by: str = Field(default="created_at", description="Sort field")
    order: str = Field(default="desc", regex="^(asc|desc)$", description="Sort order")
    date_from: Optional[datetime] = Field(default=None, description="Filter from date")
    date_to: Optional[datetime] = Field(default=None, description="Filter to date")


class QuestionStats(BaseModel):
    """Question statistics schema."""
    
    total_views: int = Field(description="Total question views")
    total_votes: int = Field(description="Total votes on question answers")
    total_answers: int = Field(description="Total number of answers")
    total_comments: int = Field(description="Total comments on answers")
    unique_contributors: int = Field(description="Number of unique contributors")
    average_answer_score: float = Field(description="Average score of answers")
    first_answer_time: Optional[datetime] = Field(description="Time of first answer")
    last_activity: datetime = Field(description="Last activity timestamp")


class QuestionActivity(BaseModel):
    """Question activity item schema."""
    
    activity_type: str = Field(description="Type of activity")
    user: UserList = Field(description="User who performed the activity")
    timestamp: datetime = Field(description="Activity timestamp")
    description: str = Field(description="Activity description")
    related_id: Optional[int] = Field(description="Related entity ID")


# Forward reference resolution
QuestionDetail.model_rebuild()

"""
Common Pydantic schemas used across the application.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Generic, TypeVar, List, Optional, Any, Dict
from datetime import datetime

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""
    
    items: List[T] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    size: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        size: int
    ) -> "PaginatedResponse[T]":
        """Create a paginated response."""
        pages = (total + size - 1) // size  # Ceiling division
        
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )


class MessageResponse(BaseModel):
    """Simple message response."""
    
    message: str = Field(description="Response message")
    success: bool = Field(default=True, description="Operation success status")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    detail: str = Field(description="Error detail message")
    error_code: Optional[str] = Field(default=None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(description="Service status")
    database: str = Field(description="Database connection status")
    environment: str = Field(description="Environment name")
    version: str = Field(description="API version")
    timestamp: float = Field(description="Response timestamp")


class SearchParams(BaseModel):
    """Search parameters for search endpoints."""
    
    q: str = Field(min_length=1, max_length=200, description="Search query")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")
    sort_by: str = Field(default="relevance", description="Sort criteria")
    order: str = Field(default="desc", regex="^(asc|desc)$", description="Sort order")


class BaseTimestampModel(BaseModel):
    """Base model with timestamp fields."""
    
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class BaseResponseModel(BaseTimestampModel):
    """Base response model with ID and timestamps."""
    
    id: int = Field(description="Unique identifier")


class StatsResponse(BaseModel):
    """Statistics response model."""
    
    total_users: int = Field(description="Total number of users")
    total_questions: int = Field(description="Total number of questions")
    total_answers: int = Field(description="Total number of answers")
    total_votes: int = Field(description="Total number of votes")
    total_comments: int = Field(description="Total number of comments")
    active_users_today: int = Field(description="Active users today")
    questions_today: int = Field(description="Questions asked today")
    answers_today: int = Field(description="Answers posted today")


class BulkOperationResponse(BaseModel):
    """Response for bulk operations."""
    
    success_count: int = Field(description="Number of successful operations")
    error_count: int = Field(description="Number of failed operations")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of errors")
    total: int = Field(description="Total number of operations attempted")
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total == 0:
            return 0.0
        return (self.success_count / self.total) * 100

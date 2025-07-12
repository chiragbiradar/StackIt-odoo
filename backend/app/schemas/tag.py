"""
Tag-related Pydantic schemas.
"""
from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List
from datetime import datetime

from .common import BaseResponseModel


class TagBase(BaseModel):
    """Base tag schema with common fields."""
    
    name: str = Field(min_length=1, max_length=50, description="Tag name")
    description: Optional[str] = Field(default=None, max_length=500, description="Tag description")
    color: Optional[str] = Field(default=None, regex="^#[0-9A-Fa-f]{6}$", description="Hex color code")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate tag name."""
        # Convert to lowercase and remove extra spaces
        cleaned_name = v.strip().lower().replace(' ', '-')
        
        if not cleaned_name:
            raise ValueError('Tag name cannot be empty')
        
        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not all(c.isalnum() or c in '-_' for c in cleaned_name):
            raise ValueError('Tag name can only contain letters, numbers, hyphens, and underscores')
        
        return cleaned_name


class TagCreate(TagBase):
    """Schema for tag creation."""
    pass


class TagUpdate(BaseModel):
    """Schema for tag updates."""
    
    description: Optional[str] = Field(default=None, max_length=500)
    color: Optional[str] = Field(default=None, regex="^#[0-9A-Fa-f]{6}$")


class TagResponse(BaseResponseModel):
    """Schema for tag responses."""
    
    name: str
    description: Optional[str]
    color: Optional[str]
    usage_count: int
    
    model_config = ConfigDict(from_attributes=True)


class TagList(BaseModel):
    """Schema for tag list items."""
    
    id: int
    name: str
    description: Optional[str]
    color: Optional[str]
    usage_count: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TagUsage(BaseModel):
    """Schema for tag usage statistics."""
    
    tag: TagResponse
    usage_count: int
    recent_usage: int = Field(description="Usage in last 30 days")
    trending_score: float = Field(description="Trending score based on recent activity")


class TagSearch(BaseModel):
    """Schema for tag search parameters."""
    
    query: Optional[str] = Field(default=None, min_length=1, max_length=50, description="Search query")
    sort_by: str = Field(default="usage_count", description="Sort field")
    order: str = Field(default="desc", regex="^(asc|desc)$", description="Sort order")
    min_usage: Optional[int] = Field(default=None, ge=0, description="Minimum usage count")


class TagStats(BaseModel):
    """Tag statistics schema."""
    
    total_tags: int = Field(description="Total number of tags")
    most_used_tags: List[TagUsage] = Field(description="Most frequently used tags")
    trending_tags: List[TagUsage] = Field(description="Currently trending tags")
    new_tags_this_month: int = Field(description="New tags created this month")
    average_usage_per_tag: float = Field(description="Average usage count per tag")


class TagCloud(BaseModel):
    """Tag cloud data schema."""
    
    name: str
    count: int
    weight: float = Field(description="Relative weight for display (0-1)")
    color: Optional[str]
    url: str = Field(description="URL to tag page")


class TagSuggestion(BaseModel):
    """Tag suggestion schema."""
    
    name: str
    description: Optional[str]
    usage_count: int
    relevance_score: float = Field(description="Relevance score for the suggestion")
    is_new: bool = Field(description="Whether this is a new tag suggestion")


class BulkTagOperation(BaseModel):
    """Schema for bulk tag operations."""
    
    tag_names: List[str] = Field(min_items=1, max_items=20, description="List of tag names")
    operation: str = Field(regex="^(create|delete|merge)$", description="Operation type")
    target_tag: Optional[str] = Field(default=None, description="Target tag for merge operations")
    
    @validator('tag_names')
    def validate_tag_names(cls, v):
        """Validate tag names."""
        cleaned_names = []
        for name in v:
            cleaned_name = name.strip().lower().replace(' ', '-')
            if cleaned_name and cleaned_name not in cleaned_names:
                cleaned_names.append(cleaned_name)
        
        if not cleaned_names:
            raise ValueError('At least one valid tag name is required')
        
        return cleaned_names

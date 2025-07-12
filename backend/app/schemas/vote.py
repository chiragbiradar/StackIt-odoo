"""
Vote-related Pydantic schemas.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

from .common import BaseResponseModel
from .user import UserList


class VoteCreate(BaseModel):
    """Schema for vote creation."""
    
    answer_id: int = Field(description="ID of the answer being voted on")
    is_upvote: bool = Field(description="True for upvote, False for downvote")


class VoteUpdate(BaseModel):
    """Schema for vote updates."""
    
    is_upvote: bool = Field(description="True for upvote, False for downvote")


class VoteResponse(BaseResponseModel):
    """Schema for vote responses."""
    
    is_upvote: bool
    user_id: int
    answer_id: int
    
    # Related data
    user: UserList
    
    model_config = ConfigDict(from_attributes=True)


class VoteStats(BaseModel):
    """Vote statistics schema."""
    
    total_votes: int = Field(description="Total number of votes")
    upvotes: int = Field(description="Number of upvotes")
    downvotes: int = Field(description="Number of downvotes")
    net_score: int = Field(description="Net vote score (upvotes - downvotes)")
    upvote_percentage: float = Field(description="Percentage of upvotes")


class UserVoteHistory(BaseModel):
    """User's voting history schema."""
    
    total_votes_cast: int = Field(description="Total votes cast by user")
    upvotes_cast: int = Field(description="Upvotes cast by user")
    downvotes_cast: int = Field(description="Downvotes cast by user")
    votes_received: int = Field(description="Total votes received on user's answers")
    upvotes_received: int = Field(description="Upvotes received on user's answers")
    downvotes_received: int = Field(description="Downvotes received on user's answers")
    net_reputation: int = Field(description="Net reputation from votes")


class VoteActivity(BaseModel):
    """Vote activity schema."""
    
    vote_id: int
    answer_id: int
    question_id: int
    question_title: str
    is_upvote: bool
    timestamp: datetime
    voter: UserList
    answer_author: UserList

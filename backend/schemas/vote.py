"""
Vote schemas for StackIt Q&A platform.
Pydantic models for vote requests and responses.
"""
from pydantic import BaseModel, Field


class VoteCreate(BaseModel):
    """Schema for creating or updating a vote."""
    is_upvote: bool = Field(..., description="True for upvote, False for downvote")

    class Config:
        json_schema_extra = {
            "example": {
                "is_upvote": True
            }
        }


class VoteResponse(BaseModel):
    """Schema for vote response."""
    message: str
    answer_id: int
    is_upvote: bool
    new_vote_score: int
    user_reputation_change: int

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Vote cast successfully",
                "answer_id": 1,
                "is_upvote": True,
                "new_vote_score": 9,
                "user_reputation_change": 10
            }
        }


class VoteRemoveResponse(BaseModel):
    """Schema for vote removal response."""
    message: str
    answer_id: int
    new_vote_score: int
    user_reputation_change: int

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Vote removed successfully",
                "answer_id": 1,
                "new_vote_score": 8,
                "user_reputation_change": -10
            }
        }

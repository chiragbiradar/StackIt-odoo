"""
Tag schemas for StackIt Q&A platform.
Pydantic models for tag responses.
"""
from typing import List, Optional

from pydantic import BaseModel


class TagResponse(BaseModel):
    """Schema for tag response."""
    id: int
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    usage_count: int

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "fastapi",
                "description": "A modern, fast web framework for building APIs with Python",
                "color": "#009688",
                "usage_count": 42
            }
        }


class TagListResponse(BaseModel):
    """Schema for tag list response."""
    tags: List[TagResponse]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "tags": [
                    {
                        "id": 1,
                        "name": "fastapi",
                        "description": "A modern, fast web framework for building APIs with Python",
                        "color": "#009688",
                        "usage_count": 42
                    },
                    {
                        "id": 2,
                        "name": "python",
                        "description": "A high-level programming language",
                        "color": "#3776AB",
                        "usage_count": 156
                    }
                ],
                "total": 2
            }
        }

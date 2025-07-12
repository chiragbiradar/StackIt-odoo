"""
Base model with common fields and functionality.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models."""
    
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the record was created"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the record was last updated"
    )


class BaseModel(Base, TimestampMixin):
    """Abstract base model with common fields."""
    
    __abstract__ = True
    
    id = Column(
        Integer, 
        primary_key=True, 
        index=True,
        comment="Primary key identifier"
    )

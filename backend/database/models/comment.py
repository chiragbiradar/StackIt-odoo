"""
Comment model for storing comments on answers.
"""
from sqlalchemy import Column, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel


class Comment(BaseModel):
    """Comment model for storing comments on answers."""
    
    __tablename__ = "comments"
    
    # Comment content
    content = Column(
        Text, 
        nullable=False,
        comment="Text content of the comment"
    )
    
    # Foreign keys
    answer_id = Column(
        Integer, 
        ForeignKey("answers.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="Reference to the answer this comment belongs to"
    )
    author_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="Reference to the user who wrote this comment"
    )
    
    # Relationships
    answer = relationship("Answer", back_populates="comments")
    author = relationship("User", back_populates="comments")
    
    def __repr__(self):
        return f"<Comment(id={self.id}, answer_id={self.answer_id}, author_id={self.author_id})>"

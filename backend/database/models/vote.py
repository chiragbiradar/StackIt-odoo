"""
Vote model for storing user votes on answers.
"""
from sqlalchemy import Boolean, Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import BaseModel


class Vote(BaseModel):
    """Vote model for storing user votes on answers."""

    __tablename__ = "votes"

    # Vote information
    is_upvote = Column(
        Boolean,
        nullable=False,
        comment="True for upvote, False for downvote"
    )

    # Foreign keys
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the user who cast the vote"
    )
    answer_id = Column(
        Integer,
        ForeignKey("answers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the answer being voted on"
    )

    # Relationships
    user = relationship("User", back_populates="votes")
    answer = relationship("Answer", back_populates="votes")

    # Constraints - ensure one vote per user per answer
    __table_args__ = (
        UniqueConstraint('user_id', 'answer_id', name='uq_user_answer_vote'),
    )

    def __repr__(self):
        vote_type = "upvote" if self.is_upvote else "downvote"
        return f"<Vote(id={self.id}, user_id={self.user_id}, answer_id={self.answer_id}, type={vote_type})>"

"""
Answer model for storing user answers to questions.
"""
from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class Answer(BaseModel):
    """Answer model for storing user answers to questions."""

    __tablename__ = "answers"

    # Answer content
    content = Column(
        Text,
        nullable=False,
        comment="Rich text content of the answer"
    )

    # Answer metadata
    vote_score = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Net vote score (upvotes - downvotes)"
    )
    comment_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of comments on this answer"
    )

    # Answer status
    is_accepted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this answer is accepted by the question author"
    )

    # Foreign keys
    question_id = Column(
        Integer,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the question this answer belongs to"
    )
    author_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the user who wrote this answer"
    )

    # Relationships
    question = relationship(
        "Question",
        back_populates="answers",
        foreign_keys=[question_id]
    )
    author = relationship("User", back_populates="answers")
    votes = relationship(
        "Vote",
        back_populates="answer",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    comments = relationship(
        "Comment",
        back_populates="answer",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    # Table arguments for indexes and constraints
    __table_args__ = (
        # Index for answers by question (most common query)
        Index('ix_answers_question_created', 'question_id', 'created_at'),
        # Index for accepted answers
        Index('ix_answers_accepted', 'is_accepted', 'question_id'),
        # Index for answers by vote score
        Index('ix_answers_vote_score_desc', 'vote_score'),
        # Index for user's answers
        Index('ix_answers_author_created', 'author_id', 'created_at'),
    )

    def __repr__(self):
        return f"<Answer(id={self.id}, question_id={self.question_id}, author_id={self.author_id}, is_accepted={self.is_accepted})>"

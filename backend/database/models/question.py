"""
Question model for storing user questions.
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship

from .base import BaseModel


class Question(BaseModel):
    """Question model for storing user questions."""
    
    __tablename__ = "questions"
    
    # Question content
    title = Column(
        String(200), 
        nullable=False, 
        index=True,
        comment="Question title - short and descriptive"
    )
    description = Column(
        Text, 
        nullable=False,
        comment="Rich text description of the question"
    )
    
    # Question metadata
    view_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of times this question has been viewed"
    )
    vote_score = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Net vote score (upvotes - downvotes)"
    )
    answer_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of answers to this question"
    )
    
    # Question status
    is_closed = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the question is closed for new answers"
    )
    has_accepted_answer = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this question has an accepted answer"
    )
    
    # Foreign keys
    author_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True,
        comment="Reference to the user who asked the question"
    )
    accepted_answer_id = Column(
        Integer,
        ForeignKey("answers.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to the accepted answer (if any)"
    )
    
    # Relationships
    author = relationship("User", back_populates="questions")
    answers = relationship(
        "Answer", 
        back_populates="question", 
        cascade="all, delete-orphan",
        foreign_keys="Answer.question_id",
        lazy="dynamic"
    )
    accepted_answer = relationship(
        "Answer",
        foreign_keys=[accepted_answer_id],
        post_update=True
    )
    question_tags = relationship(
        "QuestionTag", 
        back_populates="question", 
        cascade="all, delete-orphan"
    )
    
    # Table arguments for indexes and constraints
    __table_args__ = (
        # Composite index for listing questions by creation date and status
        Index('ix_questions_created_status', 'created_at', 'is_closed'),
        # Index for popular questions (by vote score)
        Index('ix_questions_vote_score_desc', 'vote_score'),
        # Index for questions with accepted answers
        Index('ix_questions_accepted_answers', 'has_accepted_answer', 'created_at'),
        # Index for author's questions
        Index('ix_questions_author_created', 'author_id', 'created_at'),
        # Note: Advanced PostgreSQL indexes (GIN, trigram) can be added later via migrations
    )

    # Computed properties
    @property
    def tags(self):
        """Get list of tags associated with this question."""
        return [qt.tag for qt in self.question_tags]

    def __repr__(self):
        return f"<Question(id={self.id}, title='{self.title[:50]}...', author_id={self.author_id})>"

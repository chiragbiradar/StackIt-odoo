"""
Tag model for categorizing questions.
"""
from sqlalchemy import Column, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import BaseModel


class Tag(BaseModel):
    """Tag model for categorizing questions."""

    __tablename__ = "tags"

    # Tag information
    name = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique tag name (e.g., 'python', 'javascript')"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Description of what this tag represents"
    )
    color = Column(
        String(7),  # Hex color code
        nullable=True,
        comment="Hex color code for tag display (e.g., '#FF5733')"
    )

    # Tag statistics
    usage_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of times this tag has been used"
    )

    # Relationships
    question_tags = relationship(
        "QuestionTag",
        back_populates="tag",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}', usage_count={self.usage_count})>"


class QuestionTag(BaseModel):
    """Association table for many-to-many relationship between Questions and Tags."""

    __tablename__ = "question_tags"

    # Foreign keys
    question_id = Column(
        Integer,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the question"
    )
    tag_id = Column(
        Integer,
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to the tag"
    )

    # Relationships
    question = relationship("Question", back_populates="question_tags")
    tag = relationship("Tag", back_populates="question_tags")

    # Constraints
    __table_args__ = (
        UniqueConstraint('question_id', 'tag_id', name='uq_question_tag'),
    )

    def __repr__(self):
        return f"<QuestionTag(question_id={self.question_id}, tag_id={self.tag_id})>"

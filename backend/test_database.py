#!/usr/bin/env python3
"""
Database testing script for StackIt application.
Tests database connectivity, schema creation, and basic operations.
"""
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db, check_database_connection
from app.models import User, Question, Answer, Tag, Vote, Notification, Comment
from app.models.user import UserRole
from app.models.notification import NotificationType
from app.config import get_test_database_url
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDatabase:
    """Test database functionality."""
    
    @classmethod
    def setup_class(cls):
        """Set up test database."""
        cls.engine = create_engine(get_test_database_url())
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        
        # Create all tables
        Base.metadata.create_all(bind=cls.engine)
        
    @classmethod
    def teardown_class(cls):
        """Clean up test database."""
        Base.metadata.drop_all(bind=cls.engine)
        cls.engine.dispose()
    
    def setup_method(self):
        """Set up each test method."""
        self.db = self.SessionLocal()
    
    def teardown_method(self):
        """Clean up each test method."""
        self.db.rollback()
        self.db.close()
    
    def test_database_connection(self):
        """Test database connection."""
        assert check_database_connection()
    
    def test_create_user(self):
        """Test user creation."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            role=UserRole.USER
        )
        self.db.add(user)
        self.db.commit()
        
        # Verify user was created
        created_user = self.db.query(User).filter(User.username == "testuser").first()
        assert created_user is not None
        assert created_user.email == "test@example.com"
        assert created_user.role == UserRole.USER
    
    def test_create_tag(self):
        """Test tag creation."""
        tag = Tag(
            name="python",
            description="Python programming language",
            color="#3776ab"
        )
        self.db.add(tag)
        self.db.commit()
        
        # Verify tag was created
        created_tag = self.db.query(Tag).filter(Tag.name == "python").first()
        assert created_tag is not None
        assert created_tag.description == "Python programming language"
    
    def test_create_question_with_tags(self):
        """Test question creation with tags."""
        # Create user
        user = User(
            username="questioner",
            email="questioner@example.com",
            hashed_password="hashed_password"
        )
        self.db.add(user)
        self.db.flush()
        
        # Create tag
        tag = Tag(name="testing", description="Testing related")
        self.db.add(tag)
        self.db.flush()
        
        # Create question
        question = Question(
            title="How to test database?",
            description="I need help with database testing",
            author_id=user.id
        )
        self.db.add(question)
        self.db.flush()
        
        # Add tag to question
        from app.models.tag import QuestionTag
        question_tag = QuestionTag(question_id=question.id, tag_id=tag.id)
        self.db.add(question_tag)
        self.db.commit()
        
        # Verify question and tag relationship
        created_question = self.db.query(Question).filter(Question.title == "How to test database?").first()
        assert created_question is not None
        assert len(created_question.question_tags) == 1
        assert created_question.question_tags[0].tag.name == "testing"
    
    def test_create_answer_and_vote(self):
        """Test answer creation and voting."""
        # Create users
        questioner = User(username="questioner", email="q@example.com", hashed_password="pass")
        answerer = User(username="answerer", email="a@example.com", hashed_password="pass")
        voter = User(username="voter", email="v@example.com", hashed_password="pass")
        
        self.db.add_all([questioner, answerer, voter])
        self.db.flush()
        
        # Create question
        question = Question(
            title="Test question",
            description="Test description",
            author_id=questioner.id
        )
        self.db.add(question)
        self.db.flush()
        
        # Create answer
        answer = Answer(
            content="This is a test answer",
            question_id=question.id,
            author_id=answerer.id
        )
        self.db.add(answer)
        self.db.flush()
        
        # Create vote
        vote = Vote(
            is_upvote=True,
            user_id=voter.id,
            answer_id=answer.id
        )
        self.db.add(vote)
        self.db.commit()
        
        # Verify relationships
        created_answer = self.db.query(Answer).filter(Answer.content == "This is a test answer").first()
        assert created_answer is not None
        assert created_answer.question.title == "Test question"
        assert created_answer.author.username == "answerer"
        assert len(list(created_answer.votes)) == 1
        assert list(created_answer.votes)[0].is_upvote is True
    
    def test_create_comment(self):
        """Test comment creation."""
        # Create user and answer (simplified setup)
        user = User(username="commenter", email="c@example.com", hashed_password="pass")
        questioner = User(username="q", email="q@example.com", hashed_password="pass")
        answerer = User(username="a", email="a@example.com", hashed_password="pass")
        
        self.db.add_all([user, questioner, answerer])
        self.db.flush()
        
        question = Question(title="Q", description="D", author_id=questioner.id)
        self.db.add(question)
        self.db.flush()
        
        answer = Answer(content="A", question_id=question.id, author_id=answerer.id)
        self.db.add(answer)
        self.db.flush()
        
        # Create comment
        comment = Comment(
            content="This is a comment",
            answer_id=answer.id,
            author_id=user.id
        )
        self.db.add(comment)
        self.db.commit()
        
        # Verify comment
        created_comment = self.db.query(Comment).filter(Comment.content == "This is a comment").first()
        assert created_comment is not None
        assert created_comment.answer.content == "A"
        assert created_comment.author.username == "commenter"
    
    def test_create_notification(self):
        """Test notification creation."""
        # Create users
        recipient = User(username="recipient", email="r@example.com", hashed_password="pass")
        sender = User(username="sender", email="s@example.com", hashed_password="pass")
        
        self.db.add_all([recipient, sender])
        self.db.flush()
        
        # Create notification
        notification = Notification(
            title="New Answer",
            message="Someone answered your question",
            notification_type=NotificationType.ANSWER_TO_QUESTION,
            user_id=recipient.id,
            triggered_by_user_id=sender.id
        )
        self.db.add(notification)
        self.db.commit()
        
        # Verify notification
        created_notification = self.db.query(Notification).filter(
            Notification.title == "New Answer"
        ).first()
        assert created_notification is not None
        assert created_notification.user.username == "recipient"
        assert created_notification.triggered_by_user.username == "sender"
        assert created_notification.is_read is False
    
    def test_unique_constraints(self):
        """Test unique constraints."""
        # Test unique username
        user1 = User(username="unique", email="u1@example.com", hashed_password="pass")
        user2 = User(username="unique", email="u2@example.com", hashed_password="pass")
        
        self.db.add(user1)
        self.db.commit()
        
        self.db.add(user2)
        with pytest.raises(Exception):  # Should raise integrity error
            self.db.commit()
        
        self.db.rollback()
        
        # Test unique email
        user3 = User(username="unique2", email="same@example.com", hashed_password="pass")
        user4 = User(username="unique3", email="same@example.com", hashed_password="pass")
        
        self.db.add(user3)
        self.db.commit()
        
        self.db.add(user4)
        with pytest.raises(Exception):  # Should raise integrity error
            self.db.commit()
    
    def test_cascade_deletes(self):
        """Test cascade delete functionality."""
        # Create user with question and answer
        user = User(username="cascade_test", email="cascade@example.com", hashed_password="pass")
        self.db.add(user)
        self.db.flush()
        
        question = Question(title="Cascade Test", description="Test", author_id=user.id)
        self.db.add(question)
        self.db.flush()
        
        answer = Answer(content="Answer", question_id=question.id, author_id=user.id)
        self.db.add(answer)
        self.db.flush()
        
        vote = Vote(is_upvote=True, user_id=user.id, answer_id=answer.id)
        self.db.add(vote)
        self.db.commit()
        
        # Delete user should cascade
        self.db.delete(user)
        self.db.commit()
        
        # Verify cascaded deletes
        assert self.db.query(Question).filter(Question.title == "Cascade Test").first() is None
        assert self.db.query(Answer).filter(Answer.content == "Answer").first() is None
        assert self.db.query(Vote).filter(Vote.user_id == user.id).first() is None


def run_manual_tests():
    """Run manual tests for database functionality."""
    logger.info("Starting manual database tests...")
    
    try:
        # Test database connection
        logger.info("Testing database connection...")
        if check_database_connection():
            logger.info("✅ Database connection successful")
        else:
            logger.error("❌ Database connection failed")
            return False
        
        # Test table creation
        logger.info("Testing table creation...")
        engine = create_engine(get_test_database_url())
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tables created successfully")
        
        # Test basic operations
        logger.info("Testing basic CRUD operations...")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            # Create a test user
            user = User(
                username="manual_test",
                email="manual@test.com",
                hashed_password="test_password",
                role=UserRole.USER
            )
            db.add(user)
            db.commit()
            
            # Query the user
            created_user = db.query(User).filter(User.username == "manual_test").first()
            if created_user:
                logger.info("✅ User creation and query successful")
            else:
                logger.error("❌ User creation or query failed")
                return False
            
            # Clean up
            db.delete(created_user)
            db.commit()
            logger.info("✅ User deletion successful")
            
        finally:
            db.close()
        
        # Clean up tables
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        logger.info("✅ Tables dropped successfully")
        
        logger.info("✅ All manual tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Manual tests failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database testing")
    parser.add_argument("--manual", action="store_true", help="Run manual tests")
    parser.add_argument("--pytest", action="store_true", help="Run pytest tests")
    
    args = parser.parse_args()
    
    if args.manual:
        success = run_manual_tests()
        sys.exit(0 if success else 1)
    elif args.pytest:
        # Run pytest
        pytest.main([__file__, "-v"])
    else:
        # Run both
        logger.info("Running manual tests...")
        manual_success = run_manual_tests()
        
        logger.info("Running pytest tests...")
        pytest_result = pytest.main([__file__, "-v"])
        
        if manual_success and pytest_result == 0:
            logger.info("✅ All tests passed!")
            sys.exit(0)
        else:
            logger.error("❌ Some tests failed!")
            sys.exit(1)

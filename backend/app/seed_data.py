"""
Seed data for StackIt application.
Provides initial data for development and testing.
"""
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import logging
from datetime import datetime

from .models import User, Tag, Question, Answer, Vote, Notification
from .models.user import UserRole
from .models.notification import NotificationType

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_default_users(db: Session):
    """Create default users for the application."""
    users_data = [
        {
            "username": "admin",
            "email": "admin@stackit.com",
            "password": "admin123",
            "full_name": "System Administrator",
            "bio": "System administrator account",
            "role": UserRole.ADMIN,
            "is_verified": True,
            "reputation_score": 1000
        },
        {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "password123",
            "full_name": "John Doe",
            "bio": "Software developer passionate about Python and web development",
            "role": UserRole.USER,
            "is_verified": True,
            "reputation_score": 150
        },
        {
            "username": "jane_smith",
            "email": "jane@example.com",
            "password": "password123",
            "full_name": "Jane Smith",
            "bio": "Full-stack developer with expertise in React and FastAPI",
            "role": UserRole.USER,
            "is_verified": True,
            "reputation_score": 200
        },
        {
            "username": "mike_wilson",
            "email": "mike@example.com",
            "password": "password123",
            "full_name": "Mike Wilson",
            "bio": "DevOps engineer and database specialist",
            "role": UserRole.USER,
            "is_verified": True,
            "reputation_score": 75
        }
    ]
    
    created_users = []
    for user_data in users_data:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == user_data["username"]).first()
        if existing_user:
            logger.info(f"User {user_data['username']} already exists, skipping...")
            created_users.append(existing_user)
            continue
        
        # Create new user
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
            full_name=user_data["full_name"],
            bio=user_data["bio"],
            role=user_data["role"],
            is_verified=user_data["is_verified"],
            reputation_score=user_data["reputation_score"]
        )
        db.add(user)
        created_users.append(user)
        logger.info(f"Created user: {user_data['username']}")
    
    db.commit()
    return created_users


def create_default_tags(db: Session):
    """Create default tags for the application."""
    tags_data = [
        {"name": "python", "description": "Python programming language", "color": "#3776ab"},
        {"name": "javascript", "description": "JavaScript programming language", "color": "#f7df1e"},
        {"name": "react", "description": "React JavaScript library", "color": "#61dafb"},
        {"name": "fastapi", "description": "FastAPI Python web framework", "color": "#009688"},
        {"name": "postgresql", "description": "PostgreSQL database", "color": "#336791"},
        {"name": "html", "description": "HyperText Markup Language", "color": "#e34f26"},
        {"name": "css", "description": "Cascading Style Sheets", "color": "#1572b6"},
        {"name": "sql", "description": "Structured Query Language", "color": "#4479a1"},
        {"name": "git", "description": "Version control system", "color": "#f05032"},
        {"name": "docker", "description": "Containerization platform", "color": "#2496ed"},
        {"name": "api", "description": "Application Programming Interface", "color": "#ff6b6b"},
        {"name": "database", "description": "Database related questions", "color": "#4caf50"},
        {"name": "web-development", "description": "Web development topics", "color": "#ff9800"},
        {"name": "backend", "description": "Backend development", "color": "#9c27b0"},
        {"name": "frontend", "description": "Frontend development", "color": "#e91e63"}
    ]
    
    created_tags = []
    for tag_data in tags_data:
        # Check if tag already exists
        existing_tag = db.query(Tag).filter(Tag.name == tag_data["name"]).first()
        if existing_tag:
            logger.info(f"Tag {tag_data['name']} already exists, skipping...")
            created_tags.append(existing_tag)
            continue
        
        # Create new tag
        tag = Tag(
            name=tag_data["name"],
            description=tag_data["description"],
            color=tag_data["color"]
        )
        db.add(tag)
        created_tags.append(tag)
        logger.info(f"Created tag: {tag_data['name']}")
    
    db.commit()
    return created_tags


def create_sample_questions(db: Session, users: list, tags: list):
    """Create sample questions for demonstration."""
    questions_data = [
        {
            "title": "How to set up FastAPI with PostgreSQL?",
            "description": """I'm trying to set up a FastAPI application with PostgreSQL database. 
            I've installed the required packages but I'm getting connection errors. 
            
            Here's my current setup:
            ```python
            from fastapi import FastAPI
            from sqlalchemy import create_engine
            
            app = FastAPI()
            engine = create_engine("postgresql://user:pass@localhost/db")
            ```
            
            What am I missing? Any help would be appreciated!""",
            "author": users[1],  # john_doe
            "tags": ["fastapi", "postgresql", "python"]
        },
        {
            "title": "React state management best practices",
            "description": """What are the current best practices for state management in React applications? 
            I'm working on a medium-sized application and wondering whether to use:
            
            1. Built-in useState and useContext
            2. Redux Toolkit
            3. Zustand
            4. Jotai
            
            What would you recommend and why?""",
            "author": users[2],  # jane_smith
            "tags": ["react", "javascript", "frontend"]
        },
        {
            "title": "SQL query optimization for large datasets",
            "description": """I have a PostgreSQL query that's running very slowly on a table with 10M+ records:
            
            ```sql
            SELECT u.username, COUNT(q.id) as question_count
            FROM users u
            LEFT JOIN questions q ON u.id = q.author_id
            WHERE u.created_at > '2023-01-01'
            GROUP BY u.id, u.username
            ORDER BY question_count DESC;
            ```
            
            The query takes over 30 seconds to execute. How can I optimize this?""",
            "author": users[3],  # mike_wilson
            "tags": ["sql", "postgresql", "database"]
        }
    ]
    
    created_questions = []
    for question_data in questions_data:
        # Check if question already exists
        existing_question = db.query(Question).filter(Question.title == question_data["title"]).first()
        if existing_question:
            logger.info(f"Question '{question_data['title']}' already exists, skipping...")
            created_questions.append(existing_question)
            continue
        
        # Create new question
        question = Question(
            title=question_data["title"],
            description=question_data["description"],
            author_id=question_data["author"].id,
            view_count=0,
            vote_score=0,
            answer_count=0
        )
        db.add(question)
        db.flush()  # Get the question ID
        
        # Add tags to question
        for tag_name in question_data["tags"]:
            tag = next((t for t in tags if t.name == tag_name), None)
            if tag:
                from .models.tag import QuestionTag
                question_tag = QuestionTag(question_id=question.id, tag_id=tag.id)
                db.add(question_tag)
                tag.usage_count += 1
        
        created_questions.append(question)
        logger.info(f"Created question: {question_data['title']}")
    
    db.commit()
    return created_questions


def seed_database(db: Session):
    """Seed the database with initial data."""
    logger.info("Starting database seeding...")
    
    try:
        # Create users
        users = create_default_users(db)
        logger.info(f"Created {len(users)} users")
        
        # Create tags
        tags = create_default_tags(db)
        logger.info(f"Created {len(tags)} tags")
        
        # Create sample questions
        questions = create_sample_questions(db, users, tags)
        logger.info(f"Created {len(questions)} questions")
        
        logger.info("✅ Database seeding completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error seeding database: {e}")
        db.rollback()
        raise

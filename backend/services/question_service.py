"""
Question Service for StackIt Q&A platform.
Handles question creation, listing, and retrieval.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

# Import database dependencies
from database import get_db
from database.models import Question, QuestionTag, Tag, User

# Import schemas
from schemas.question import (
    AuthorInfo,
    QuestionCreate,
    QuestionList,
    QuestionListItem,
    QuestionResponse,
    TagInfo,
)

# Import authentication
from services.auth_service import get_current_user_dependency

# Import notification functions
from utils.notification import extract_mentions, notify_mention

# Create router
router = APIRouter()


def get_or_create_tags(db: Session, tag_names: List[str]) -> List[Tag]:
    """Get existing tags or create new ones."""
    tags = []
    for tag_name in tag_names:
        clean_tag_name = tag_name.lower().strip()

        # Try to find existing tag
        tag = db.query(Tag).filter(Tag.name == clean_tag_name).first()

        if not tag:
            # Create new tag
            tag = Tag(name=clean_tag_name, usage_count=0)
            db.add(tag)
            db.flush()  # Get the ID without committing

        # Increment usage count
        tag.usage_count += 1
        tags.append(tag)

    return tags


@router.post("/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    question_data: QuestionCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Create a new question.

    - **title**: Question title (10-200 characters)
    - **description**: Question description (minimum 20 characters)
    - **tag_names**: List of tag names (1-5 tags)
    """
    try:
        # Get or create tags
        tags = get_or_create_tags(db, question_data.tag_names)

        # Create question
        new_question = Question(
            title=question_data.title,
            description=question_data.description,
            author_id=current_user.id
        )

        db.add(new_question)
        db.flush()  # Get the question ID

        # Create question-tag associations
        for tag in tags:
            question_tag = QuestionTag(
                question_id=new_question.id,
                tag_id=tag.id
            )
            db.add(question_tag)

        # Update user's question count
        current_user.questions_count += 1

        db.commit()
        db.refresh(new_question)

        # Handle mention notifications
        try:
            mentions = extract_mentions(question_data.description)
            for username in mentions:
                await notify_mention(
                    db=db,
                    mentioned_username=username,
                    mentioning_user_id=current_user.id,
                    content=question_data.description,
                    related_question_id=new_question.id
                )
        except Exception as e:
            # Log error but don't fail the question creation
            print(f"Error sending mention notifications: {e}")

        # Load the question with all relationships for response
        question_with_relations = db.query(Question).options(
            joinedload(Question.author),
            joinedload(Question.question_tags).joinedload(QuestionTag.tag)
        ).filter(Question.id == new_question.id).first()

        # Build response
        author_info = AuthorInfo(
            id=question_with_relations.author.id,
            username=question_with_relations.author.username,
            full_name=question_with_relations.author.full_name,
            reputation_score=question_with_relations.author.reputation_score
        )

        tag_info = [
            TagInfo(
                id=qt.tag.id,
                name=qt.tag.name,
                color=qt.tag.color
            )
            for qt in question_with_relations.question_tags
        ]

        return QuestionResponse(
            id=question_with_relations.id,
            title=question_with_relations.title,
            description=question_with_relations.description,
            view_count=question_with_relations.view_count,
            vote_score=question_with_relations.vote_score,
            answer_count=question_with_relations.answer_count,
            is_closed=question_with_relations.is_closed,
            has_accepted_answer=question_with_relations.has_accepted_answer,
            author=author_info,
            tags=tag_info,
            created_at=question_with_relations.created_at,
            updated_at=question_with_relations.updated_at
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating question: {str(e)}"
        ) from e


@router.get("/questions", response_model=QuestionList)
async def list_questions(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=50, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    List all questions with pagination.

    - **page**: Page number (starts from 1)
    - **per_page**: Number of questions per page (1-50)
    """
    try:
        # Calculate offset
        offset = (page - 1) * per_page

        # Get total count
        total = db.query(Question).count()

        # Get questions with relationships
        questions = db.query(Question).options(
            joinedload(Question.author),
            joinedload(Question.question_tags).joinedload(QuestionTag.tag)
        ).order_by(desc(Question.created_at)).offset(offset).limit(per_page).all()

        # Build response items
        question_items = []
        for question in questions:
            author_info = AuthorInfo(
                id=question.author.id,
                username=question.author.username,
                full_name=question.author.full_name,
                reputation_score=question.author.reputation_score
            )

            tag_info = [
                TagInfo(
                    id=qt.tag.id,
                    name=qt.tag.name,
                    color=qt.tag.color
                )
                for qt in question.question_tags
            ]

            question_items.append(QuestionListItem(
                id=question.id,
                title=question.title,
                description=question.description,
                view_count=question.view_count,
                vote_score=question.vote_score,
                answer_count=question.answer_count,
                has_accepted_answer=question.has_accepted_answer,
                author=author_info,
                tags=tag_info,
                created_at=question.created_at
            ))

        # Calculate pagination info
        has_next = (offset + per_page) < total
        has_prev = page > 1

        return QuestionList(
            questions=question_items,
            total=total,
            page=page,
            per_page=per_page,
            has_next=has_next,
            has_prev=has_prev
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching questions: {str(e)}"
        ) from e


@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific question by ID.

    - **question_id**: The ID of the question to retrieve
    """
    try:
        # Get question with all relationships
        question = db.query(Question).options(
            joinedload(Question.author),
            joinedload(Question.question_tags).joinedload(QuestionTag.tag)
        ).filter(Question.id == question_id).first()

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )

        # Increment view count
        question.view_count += 1
        db.commit()

        # Build response
        author_info = AuthorInfo(
            id=question.author.id,
            username=question.author.username,
            full_name=question.author.full_name,
            reputation_score=question.author.reputation_score
        )

        tag_info = [
            TagInfo(
                id=qt.tag.id,
                name=qt.tag.name,
                color=qt.tag.color
            )
            for qt in question.question_tags
        ]

        return QuestionResponse(
            id=question.id,
            title=question.title,
            description=question.description,
            view_count=question.view_count,
            vote_score=question.vote_score,
            answer_count=question.answer_count,
            is_closed=question.is_closed,
            has_accepted_answer=question.has_accepted_answer,
            author=author_info,
            tags=tag_info,
            created_at=question.created_at,
            updated_at=question.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching question: {str(e)}"
        ) from e

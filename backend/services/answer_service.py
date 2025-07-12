"""
Answer Service for StackIt Q&A platform.
Handles answer creation and acceptance.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

# Import database dependencies
from database import get_db
from database.models import Answer, Question, User

# Import schemas
from schemas.answer import AcceptAnswerResponse, AnswerCreate, AnswerResponse, AuthorInfo

# Import authentication
from services.auth_service import get_current_user_dependency

# Create router
router = APIRouter()


@router.post("/answers", response_model=AnswerResponse, status_code=status.HTTP_201_CREATED)
async def create_answer(
    answer_data: AnswerCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Create a new answer for a question.
    
    - **content**: Answer content (minimum 20 characters)
    - **question_id**: ID of the question being answered
    """
    try:
        # Check if question exists and is not closed
        question = db.query(Question).filter(Question.id == answer_data.question_id).first()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        if question.is_closed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot answer a closed question"
            )
        
        # Create answer
        new_answer = Answer(
            content=answer_data.content,
            question_id=answer_data.question_id,
            author_id=current_user.id
        )
        
        db.add(new_answer)
        
        # Update question answer count
        question.answer_count += 1
        
        # Update user's answer count
        current_user.answers_count += 1
        
        db.commit()
        db.refresh(new_answer)
        
        # Load the answer with author for response
        answer_with_author = db.query(Answer).options(
            joinedload(Answer.author)
        ).filter(Answer.id == new_answer.id).first()
        
        # Build response
        author_info = AuthorInfo(
            id=answer_with_author.author.id,
            username=answer_with_author.author.username,
            full_name=answer_with_author.author.full_name,
            reputation_score=answer_with_author.author.reputation_score
        )
        
        return AnswerResponse(
            id=answer_with_author.id,
            content=answer_with_author.content,
            vote_score=answer_with_author.vote_score,
            comment_count=answer_with_author.comment_count,
            is_accepted=answer_with_author.is_accepted,
            question_id=answer_with_author.question_id,
            author=author_info,
            created_at=answer_with_author.created_at,
            updated_at=answer_with_author.updated_at
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating answer: {str(e)}"
        ) from e


@router.put("/answers/{answer_id}/accept", response_model=AcceptAnswerResponse)
async def accept_answer(
    answer_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Accept an answer (only question owner can accept).
    
    - **answer_id**: ID of the answer to accept
    """
    try:
        # Get answer with question and author
        answer = db.query(Answer).options(
            joinedload(Answer.question),
            joinedload(Answer.author)
        ).filter(Answer.id == answer_id).first()
        
        if not answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Answer not found"
            )
        
        # Check if current user is the question owner
        if answer.question.author_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the question author can accept answers"
            )
        
        # Check if question is closed
        if answer.question.is_closed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot accept answers for a closed question"
            )
        
        # If there's already an accepted answer, unaccept it
        if answer.question.has_accepted_answer:
            current_accepted = db.query(Answer).filter(
                Answer.question_id == answer.question_id,
                Answer.is_accepted == True
            ).first()
            
            if current_accepted:
                current_accepted.is_accepted = False
                # Decrease reputation for previously accepted answer author
                if current_accepted.author:
                    current_accepted.author.reputation_score = max(0, current_accepted.author.reputation_score - 15)
        
        # Accept the new answer
        answer.is_accepted = True
        answer.question.has_accepted_answer = True
        answer.question.accepted_answer_id = answer.id
        
        # Increase reputation for answer author (15 points for accepted answer)
        if answer.author:
            answer.author.reputation_score += 15
        
        db.commit()
        
        return AcceptAnswerResponse(
            message="Answer accepted successfully",
            answer_id=answer.id,
            is_accepted=True
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error accepting answer: {str(e)}"
        ) from e

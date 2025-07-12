"""
Vote Service for StackIt Q&A platform.
Handles voting on answers (upvote/downvote).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

# Import database dependencies
from database import get_db
from database.models import Answer, User, Vote

# Import schemas
from schemas.vote import VoteCreate, VoteRemoveResponse, VoteResponse

# Import authentication
from services.auth_service import get_current_user_dependency

# Create router
router = APIRouter()


@router.post("/answers/{answer_id}/vote", response_model=VoteResponse)
async def vote_on_answer(
    answer_id: int,
    vote_data: VoteCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Vote on an answer (upvote or downvote).

    - **answer_id**: ID of the answer to vote on
    - **is_upvote**: True for upvote, False for downvote
    """
    try:
        # Get answer with author
        answer = db.query(Answer).options(
            joinedload(Answer.author)
        ).filter(Answer.id == answer_id).first()

        if not answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Answer not found"
            )

        # Prevent self-voting
        if answer.author_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot vote on your own answer"
            )

        # Check if user has already voted on this answer
        existing_vote = db.query(Vote).filter(
            Vote.user_id == current_user.id,
            Vote.answer_id == answer_id
        ).first()

        reputation_change = 0

        if existing_vote:
            # User is changing their vote
            old_is_upvote = existing_vote.is_upvote

            # Update the vote
            existing_vote.is_upvote = vote_data.is_upvote

            # Calculate vote score change
            if old_is_upvote and not vote_data.is_upvote:
                # Changed from upvote to downvote
                answer.vote_score -= 2
                reputation_change = -20  # -10 for removing upvote, -10 for adding downvote
            elif not old_is_upvote and vote_data.is_upvote:
                # Changed from downvote to upvote
                answer.vote_score += 2
                reputation_change = 20   # +10 for removing downvote, +10 for adding upvote
            # If same vote type, no change needed

        else:
            # New vote
            new_vote = Vote(
                user_id=current_user.id,
                answer_id=answer_id,
                is_upvote=vote_data.is_upvote
            )
            db.add(new_vote)

            # Update vote score
            if vote_data.is_upvote:
                answer.vote_score += 1
                reputation_change = 10
            else:
                answer.vote_score -= 1
                reputation_change = -2  # Downvotes give less negative reputation

        # Update answer author's reputation (if not the same user)
        if answer.author and reputation_change != 0:
            answer.author.reputation_score = max(0, answer.author.reputation_score + reputation_change)

        db.commit()

        return VoteResponse(
            message="Vote cast successfully",
            answer_id=answer_id,
            is_upvote=vote_data.is_upvote,
            new_vote_score=answer.vote_score,
            user_reputation_change=reputation_change
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error casting vote: {str(e)}"
        ) from e


@router.delete("/answers/{answer_id}/vote", response_model=VoteRemoveResponse)
async def remove_vote(
    answer_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Remove user's vote from an answer.

    - **answer_id**: ID of the answer to remove vote from
    """
    try:
        # Get answer with author
        answer = db.query(Answer).options(
            joinedload(Answer.author)
        ).filter(Answer.id == answer_id).first()

        if not answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Answer not found"
            )

        # Find user's vote
        vote = db.query(Vote).filter(
            Vote.user_id == current_user.id,
            Vote.answer_id == answer_id
        ).first()

        if not vote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vote not found"
            )

        # Calculate reputation change
        reputation_change = 0
        if vote.is_upvote:
            answer.vote_score -= 1
            reputation_change = -10
        else:
            answer.vote_score += 1
            reputation_change = 2

        # Update answer author's reputation
        if answer.author and reputation_change != 0:
            answer.author.reputation_score = max(0, answer.author.reputation_score + reputation_change)

        # Remove the vote
        db.delete(vote)
        db.commit()

        return VoteRemoveResponse(
            message="Vote removed successfully",
            answer_id=answer_id,
            new_vote_score=answer.vote_score,
            user_reputation_change=reputation_change
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing vote: {str(e)}"
        ) from e

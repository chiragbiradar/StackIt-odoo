"""
Vote management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from ...database import get_db
from ...models.vote import Vote
from ...models.answer import Answer
from ...models.user import User
from ...schemas.vote import VoteCreate, VoteUpdate, VoteResponse
from ...schemas.common import MessageResponse
from ...auth.dependencies import require_auth, get_permission_checker

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=VoteResponse, status_code=status.HTTP_201_CREATED)
async def create_vote(
    vote_data: VoteCreate,
    current_user: User = Depends(require_auth),
    permission_checker = Depends(get_permission_checker),
    db: Session = Depends(get_db)
):
    """
    Cast a vote on an answer.
    
    - **answer_id**: ID of the answer to vote on
    - **is_upvote**: True for upvote, False for downvote
    
    Users cannot vote on their own answers.
    Only one vote per user per answer is allowed.
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required to vote"
        )
    
    # Check if answer exists
    answer = db.query(Answer).filter(Answer.id == vote_data.answer_id).first()
    
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found"
        )
    
    # Check permissions
    if not permission_checker.can_vote_on_answer(vote_data.answer_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot vote on your own answer"
        )
    
    # Check if user already voted on this answer
    existing_vote = db.query(Vote).filter(
        and_(
            Vote.answer_id == vote_data.answer_id,
            Vote.user_id == current_user.id
        )
    ).first()
    
    if existing_vote:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already voted on this answer. Use PUT to update your vote."
        )
    
    # Create vote
    vote = Vote(
        is_upvote=vote_data.is_upvote,
        user_id=current_user.id,
        answer_id=vote_data.answer_id
    )
    
    db.add(vote)
    
    # Update answer vote score
    if vote_data.is_upvote:
        answer.vote_score += 1
    else:
        answer.vote_score -= 1
    
    db.commit()
    db.refresh(vote)
    
    vote_type = "upvote" if vote_data.is_upvote else "downvote"
    logger.info(f"{vote_type} cast by {current_user.username} on answer {vote_data.answer_id}")
    
    return vote


@router.put("/{vote_id}", response_model=VoteResponse)
async def update_vote(
    vote_id: int,
    vote_update: VoteUpdate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Update an existing vote.
    
    - **vote_id**: Vote ID to update
    - **is_upvote**: True for upvote, False for downvote
    
    Only the vote owner can update their vote.
    """
    vote = db.query(Vote).filter(Vote.id == vote_id).first()
    
    if not vote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vote not found"
        )
    
    # Check ownership
    if vote.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own votes"
        )
    
    # If vote type is changing, update answer score
    if vote.is_upvote != vote_update.is_upvote:
        answer = db.query(Answer).filter(Answer.id == vote.answer_id).first()
        
        if vote.is_upvote and not vote_update.is_upvote:
            # Changed from upvote to downvote
            answer.vote_score -= 2
        elif not vote.is_upvote and vote_update.is_upvote:
            # Changed from downvote to upvote
            answer.vote_score += 2
        
        vote.is_upvote = vote_update.is_upvote
    
    db.commit()
    db.refresh(vote)
    
    vote_type = "upvote" if vote_update.is_upvote else "downvote"
    logger.info(f"Vote updated to {vote_type} by {current_user.username}")
    
    return vote


@router.delete("/{vote_id}", response_model=MessageResponse)
async def delete_vote(
    vote_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Delete a vote (remove vote from answer).
    
    - **vote_id**: Vote ID to delete
    
    Only the vote owner can delete their vote.
    """
    vote = db.query(Vote).filter(Vote.id == vote_id).first()
    
    if not vote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vote not found"
        )
    
    # Check ownership
    if vote.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only delete your own votes"
        )
    
    # Update answer vote score
    answer = db.query(Answer).filter(Answer.id == vote.answer_id).first()
    if answer:
        if vote.is_upvote:
            answer.vote_score -= 1
        else:
            answer.vote_score += 1
    
    # Delete vote
    db.delete(vote)
    db.commit()
    
    logger.info(f"Vote deleted by {current_user.username}")
    
    return MessageResponse(
        message="Vote removed successfully",
        success=True
    )


@router.get("/answer/{answer_id}/my-vote", response_model=VoteResponse)
async def get_my_vote_on_answer(
    answer_id: int,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """
    Get current user's vote on a specific answer.
    
    - **answer_id**: Answer ID to check vote for
    
    Returns the user's vote if it exists, otherwise 404.
    """
    vote = db.query(Vote).filter(
        and_(
            Vote.answer_id == answer_id,
            Vote.user_id == current_user.id
        )
    ).first()
    
    if not vote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No vote found for this answer"
        )
    
    return vote

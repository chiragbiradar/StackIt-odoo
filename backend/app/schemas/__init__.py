"""
Pydantic schemas for request/response models.
"""
from .user import (
    UserBase, UserCreate, UserUpdate, UserResponse, UserProfile,
    UserLogin, UserRegister, Token, TokenData
)
from .question import (
    QuestionBase, QuestionCreate, QuestionUpdate, QuestionResponse,
    QuestionList, QuestionDetail
)
from .answer import (
    AnswerBase, AnswerCreate, AnswerUpdate, AnswerResponse,
    AnswerList, AnswerDetail
)
from .tag import (
    TagBase, TagCreate, TagUpdate, TagResponse,
    TagList, TagUsage
)
from .vote import (
    VoteCreate, VoteResponse, VoteUpdate
)
from .comment import (
    CommentBase, CommentCreate, CommentUpdate, CommentResponse,
    CommentList
)
from .notification import (
    NotificationBase, NotificationResponse, NotificationList,
    NotificationUpdate
)
from .common import (
    PaginationParams, PaginatedResponse, MessageResponse,
    ErrorResponse, HealthResponse
)

__all__ = [
    # User schemas
    "UserBase", "UserCreate", "UserUpdate", "UserResponse", "UserProfile",
    "UserLogin", "UserRegister", "Token", "TokenData",
    
    # Question schemas
    "QuestionBase", "QuestionCreate", "QuestionUpdate", "QuestionResponse",
    "QuestionList", "QuestionDetail",
    
    # Answer schemas
    "AnswerBase", "AnswerCreate", "AnswerUpdate", "AnswerResponse",
    "AnswerList", "AnswerDetail",
    
    # Tag schemas
    "TagBase", "TagCreate", "TagUpdate", "TagResponse",
    "TagList", "TagUsage",
    
    # Vote schemas
    "VoteCreate", "VoteResponse", "VoteUpdate",
    
    # Comment schemas
    "CommentBase", "CommentCreate", "CommentUpdate", "CommentResponse",
    "CommentList",
    
    # Notification schemas
    "NotificationBase", "NotificationResponse", "NotificationList",
    "NotificationUpdate",
    
    # Common schemas
    "PaginationParams", "PaginatedResponse", "MessageResponse",
    "ErrorResponse", "HealthResponse"
]

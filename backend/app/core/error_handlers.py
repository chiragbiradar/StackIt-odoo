"""
Global error handlers for FastAPI application.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError as PydanticValidationError
import logging
from typing import Union

from ..config import settings
from .exceptions import (
    StackItException, ValidationError, AuthenticationError, AuthorizationError,
    NotFoundError, ConflictError, DatabaseError, RateLimitError,
    BusinessLogicError, ExternalServiceError
)

logger = logging.getLogger(__name__)


async def stackit_exception_handler(request: Request, exc: StackItException) -> JSONResponse:
    """Handle custom StackIt exceptions."""
    
    # Map exception types to HTTP status codes
    status_code_map = {
        ValidationError: status.HTTP_400_BAD_REQUEST,
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        NotFoundError: status.HTTP_404_NOT_FOUND,
        ConflictError: status.HTTP_409_CONFLICT,
        DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
        BusinessLogicError: status.HTTP_400_BAD_REQUEST,
        ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
    }
    
    status_code = status_code_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Log the error
    logger.error(f"StackIt exception: {exc.message}", extra={
        "error_code": exc.error_code,
        "details": exc.details,
        "request_url": str(request.url),
        "request_method": request.method
    })
    
    # Prepare response
    response_data = {
        "detail": exc.message,
        "error_code": exc.error_code,
        "type": type(exc).__name__
    }
    
    # Add details in debug mode
    if settings.debug and exc.details:
        response_data["details"] = exc.details
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    
    logger.warning(f"Validation error: {exc.errors()}", extra={
        "request_url": str(request.url),
        "request_method": request.method
    })
    
    # Format validation errors
    errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    response_data = {
        "detail": "Validation error",
        "error_code": "VALIDATION_ERROR",
        "type": "RequestValidationError",
        "errors": errors
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors."""
    
    logger.error(f"Database error: {str(exc)}", extra={
        "request_url": str(request.url),
        "request_method": request.method,
        "exception_type": type(exc).__name__
    }, exc_info=True)
    
    # Handle specific SQLAlchemy errors
    if isinstance(exc, IntegrityError):
        # Extract constraint information if possible
        error_message = "Data integrity constraint violation"
        error_code = "INTEGRITY_ERROR"
        status_code = status.HTTP_409_CONFLICT
        
        # Try to extract more specific information
        if "UNIQUE constraint failed" in str(exc):
            error_message = "Duplicate entry - this value already exists"
        elif "FOREIGN KEY constraint failed" in str(exc):
            error_message = "Referenced resource does not exist"
        elif "NOT NULL constraint failed" in str(exc):
            error_message = "Required field is missing"
            
    else:
        error_message = "Database operation failed"
        error_code = "DATABASE_ERROR"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    response_data = {
        "detail": error_message,
        "error_code": error_code,
        "type": "DatabaseError"
    }
    
    # Add technical details in debug mode
    if settings.debug:
        response_data["technical_details"] = str(exc)
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    
    logger.warning(f"HTTP exception: {exc.detail}", extra={
        "status_code": exc.status_code,
        "request_url": str(request.url),
        "request_method": request.method
    })
    
    response_data = {
        "detail": exc.detail,
        "error_code": f"HTTP_{exc.status_code}",
        "type": "HTTPException"
    }
    
    # Add headers if present
    headers = getattr(exc, 'headers', None)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers=headers
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    
    logger.error(f"Unexpected error: {str(exc)}", extra={
        "request_url": str(request.url),
        "request_method": request.method,
        "exception_type": type(exc).__name__
    }, exc_info=True)
    
    if settings.debug:
        # In debug mode, show the actual error
        response_data = {
            "detail": str(exc),
            "error_code": "INTERNAL_ERROR",
            "type": type(exc).__name__,
            "traceback": str(exc.__traceback__) if hasattr(exc, '__traceback__') else None
        }
    else:
        # In production, show generic error
        response_data = {
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "type": "InternalServerError"
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app."""
    
    # Custom StackIt exceptions
    app.add_exception_handler(StackItException, stackit_exception_handler)
    
    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(PydanticValidationError, validation_exception_handler)
    
    # Database errors
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # HTTP exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    
    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered successfully")

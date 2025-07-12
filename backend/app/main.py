"""
StackIt FastAPI Application
Main application entry point with configuration, middleware, and routing.
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from typing import Dict, Any

from .config import settings
from .database import engine, check_database_connection, get_db
from .models.base import Base
from .core.logging import setup_logging
from .core.error_handlers import register_exception_handlers

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting StackIt API...")
    
    # Check database connection
    if not check_database_connection():
        logger.error("Database connection failed!")
        raise RuntimeError("Database connection failed")
    
    logger.info("Database connection successful")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down StackIt API...")


# Create FastAPI application
app = FastAPI(
    title="StackIt API",
    description="A minimal Q&A forum platform API",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.stackit.com"]
    )

# Register exception handlers
register_exception_handlers(app)


# Custom middleware for request logging
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all HTTP requests."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Response: {response.status_code} - {process_time:.4f}s"
    )
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    if settings.debug:
        # In debug mode, show the actual error
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": str(exc),
                "type": type(exc).__name__
            }
        )
    else:
        # In production, show generic error
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"}
        )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check(db=Depends(get_db)) -> Dict[str, Any]:
    """
    Health check endpoint to verify API and database status.
    """
    try:
        # Check database connection
        db_status = check_database_connection()
        
        return {
            "status": "healthy" if db_status else "unhealthy",
            "database": "connected" if db_status else "disconnected",
            "environment": settings.environment,
            "version": "1.0.0",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable"
        )


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """
    Root endpoint with API information.
    """
    return {
        "message": "Welcome to StackIt API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
        "health": "/health"
    }


# API version info
@app.get("/api/v1", tags=["API Info"])
async def api_info() -> Dict[str, Any]:
    """
    API version information.
    """
    return {
        "name": "StackIt API",
        "version": "1.0.0",
        "description": "A minimal Q&A forum platform API",
        "environment": settings.environment,
        "features": [
            "User authentication and authorization",
            "Question and answer management",
            "Voting system",
            "Tagging system",
            "Real-time notifications",
            "Comment system",
            "Full-text search"
        ]
    }


# Import and register API routers
# Note: These will be created in the next steps
try:
    from .api.v1.auth import router as auth_router
    from .api.v1.users import router as users_router
    from .api.v1.questions import router as questions_router
    from .api.v1.answers import router as answers_router
    from .api.v1.tags import router as tags_router
    from .api.v1.notifications import router as notifications_router
    from .api.v1.comments import router as comments_router
    
    # Register routers with API v1 prefix
    app.include_router(auth_router, prefix=settings.api_v1_prefix, tags=["Authentication"])
    app.include_router(users_router, prefix=settings.api_v1_prefix, tags=["Users"])
    app.include_router(questions_router, prefix=settings.api_v1_prefix, tags=["Questions"])
    app.include_router(answers_router, prefix=settings.api_v1_prefix, tags=["Answers"])
    app.include_router(tags_router, prefix=settings.api_v1_prefix, tags=["Tags"])
    app.include_router(notifications_router, prefix=settings.api_v1_prefix, tags=["Notifications"])
    app.include_router(comments_router, prefix=settings.api_v1_prefix, tags=["Comments"])
    
    logger.info("All API routers registered successfully")
    
except ImportError as e:
    logger.warning(f"Some API routers not available yet: {e}")
    logger.info("API routers will be registered when implemented")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.environment == "production" else "debug"
    )

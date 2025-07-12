"""
StackIt Q&A Platform - FastAPI Server
Main entry point for the StackIt backend application.
"""
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import configuration (if needed later)
# from utils.config import settings
# Import database
from database import check_database_connection, create_tables

# Import middleware
from middleware import ResponseCacheMiddleware
from services.answer_service import router as answer_router

# Import API routes
from services.auth_service import router as auth_router
from services.cache_service import router as cache_router
from services.notification_service import router as notification_router
from services.question_service import router as question_router
from services.user_service import router as user_router
from services.vote_service import router as vote_router

# Import notification service
from utils.notification import (
    cleanup_notification_service,
    initialize_notification_service,
)

# from services.user_service import router as user_router
# from services.question_service import router as question_router
# from services.answer_service import router as answer_router
# from services.tag_service import router as tag_router
# from services.notification_service import router as notification_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 Starting StackIt Q&A Platform...")

    # Check database connection
    if not check_database_connection():
        print("❌ Database connection failed!")
        raise HTTPException(status_code=500, detail="Database connection failed")

    print("✅ Database connection successful")

    # Create tables if they don't exist
    try:
        create_tables()
        print("✅ Database tables ready")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise HTTPException(status_code=500, detail="Database setup failed") from e

    # Initialize notification service
    try:
        await initialize_notification_service()
        print("✅ Notification service ready")
    except Exception as e:
        print(f"❌ Error initializing notification service: {e}")
        # Don't fail startup if notifications fail
        print("⚠️ Continuing without real-time notifications")

    print("🎉 StackIt backend is ready!")
    yield

    # Cleanup on shutdown
    try:
        await cleanup_notification_service()
        print("✅ Notification service stopped")
    except Exception as e:
        print(f"❌ Error stopping notification service: {e}")

    # Shutdown
    print("👋 Shutting down StackIt backend...")


# Create FastAPI application
app = FastAPI(
    title="StackIt Q&A Platform API",
    description="A minimal question-and-answer platform API built with FastAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Add response caching middleware
app.add_middleware(
    ResponseCacheMiddleware,
    cache_dir="./cache",
    default_expire=300,  # 5 minutes default
    exclude_paths=[
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/metrics",
        "/auth",  # Don't cache auth endpoints
        "/notifications"  # Don't cache user-specific notifications
    ]
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        db_healthy = check_database_connection()

        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "version": "1.0.0"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "version": "1.0.0"
            }
        )


# Cache management endpoints are now in services/cache_service.py


# Include API routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(notification_router, prefix="/notifications", tags=["Notifications"])
app.include_router(question_router, tags=["Questions"])
app.include_router(answer_router, tags=["Answers"])
app.include_router(vote_router, tags=["Votes"])
app.include_router(cache_router, tags=["Cache Management"])


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

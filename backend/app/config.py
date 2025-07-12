"""
Database and application configuration settings.
"""
import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = Field(
        default="postgresql://stackit:stackit@localhost:5432/stackit_db",
        description="Complete database URL"
    )
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="stackit_db", description="Database name")
    db_user: str = Field(default="stackit", description="Database user")
    db_password: str = Field(default="stackit", description="Database password")
    
    # Application Configuration
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT tokens"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, 
        description="Access token expiration time in minutes"
    )
    
    # Environment
    environment: str = Field(default="development", description="Application environment")
    debug: bool = Field(default=True, description="Debug mode")
    
    # Cache Configuration
    cache_dir: str = Field(default="./cache", description="Cache directory path")
    
    # Notification Configuration
    notification_channel: str = Field(
        default="stackit_notifications",
        description="PostgreSQL notification channel name"
    )
    
    # API Configuration
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get the database URL for SQLAlchemy."""
    return settings.database_url


def get_test_database_url() -> str:
    """Get the test database URL."""
    if settings.environment == "test":
        return settings.database_url.replace(settings.db_name, f"{settings.db_name}_test")
    return settings.database_url.replace(settings.db_name, f"{settings.db_name}_test")

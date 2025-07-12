import os

from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    # Database Configuration
    database_url: str = os.getenv('DATABASE_URL', 'sqlite:///./stackit_test.db')
    db_host: str = os.getenv('DB_HOST', 'localhost')
    db_port: str = os.getenv('DB_PORT', '5432')
    db_name: str = os.getenv('DB_NAME', 'stackit_db')
    db_user: str = os.getenv('DB_USER', 'postgres')
    db_password: str = os.getenv('DB_PASSWORD', '1234')

    # JWT Configuration
    secret_key: str = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    algorithm: str = os.getenv('ALGORITHM', 'HS256')
    access_token_expire_minutes: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))

    # Application Configuration
    environment: str = os.getenv('ENVIRONMENT', 'development')
    debug: bool = os.getenv('DEBUG', 'True').lower() == 'true'

# Global settings instance
settings = Settings()

def get_database_url() -> str:
    """Get the database URL for SQLAlchemy."""
    return settings.database_url

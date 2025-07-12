"""
Configuration utilities for StackIt application.
Integrated from feature/auth branch.
"""
import os
from typing import Any, Dict, Optional
from pathlib import Path


def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> str:
    """
    Get environment variable with optional default and required validation.
    
    Args:
        key: Environment variable key
        default: Default value if not found
        required: Whether the variable is required
        
    Returns:
        Environment variable value
        
    Raises:
        ValueError: If required variable is not found
    """
    value = os.getenv(key, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' not found")
    
    return value


def get_database_url() -> str:
    """
    Get database URL from environment variables.
    
    Returns:
        Database URL string
    """
    # Try to get full DATABASE_URL first
    database_url = get_env_var("DATABASE_URL")
    
    if database_url:
        return database_url
    
    # Build from individual components
    host = get_env_var("DB_HOST", "localhost")
    port = get_env_var("DB_PORT", "5432")
    name = get_env_var("DB_NAME", "stackit_db")
    user = get_env_var("DB_USER", "stackit")
    password = get_env_var("DB_PASSWORD", "stackit")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def get_test_database_url() -> str:
    """
    Get test database URL.
    
    Returns:
        Test database URL string
    """
    # Try to get test-specific URL first
    test_url = get_env_var("TEST_DATABASE_URL")
    
    if test_url:
        return test_url
    
    # Build test URL from regular database URL
    base_url = get_database_url()
    
    # Replace database name with test database
    if "stackit_db" in base_url:
        return base_url.replace("stackit_db", "stackit_test")
    else:
        # Append _test to the database name
        parts = base_url.rsplit("/", 1)
        if len(parts) == 2:
            return f"{parts[0]}/{parts[1]}_test"
    
    return base_url


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to project root
    """
    current_file = Path(__file__)
    # Go up from utils/config.py to backend/ to project root
    return current_file.parent.parent.parent


def get_backend_root() -> Path:
    """
    Get the backend directory.
    
    Returns:
        Path to backend directory
    """
    return get_project_root() / "backend"


def load_env_file(env_file: Optional[str] = None) -> Dict[str, str]:
    """
    Load environment variables from .env file.
    
    Args:
        env_file: Path to .env file (optional)
        
    Returns:
        Dictionary of environment variables
    """
    if env_file is None:
        env_file = get_backend_root() / ".env"
    else:
        env_file = Path(env_file)
    
    env_vars = {}
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
    
    return env_vars


def get_cors_origins() -> list:
    """
    Get CORS origins from environment.
    
    Returns:
        List of allowed CORS origins
    """
    origins_str = get_env_var("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
    return [origin.strip() for origin in origins_str.split(",")]


def is_development() -> bool:
    """
    Check if running in development environment.
    
    Returns:
        True if development environment
    """
    env = get_env_var("ENVIRONMENT", "development").lower()
    return env in ["development", "dev", "local"]


def is_production() -> bool:
    """
    Check if running in production environment.
    
    Returns:
        True if production environment
    """
    env = get_env_var("ENVIRONMENT", "development").lower()
    return env in ["production", "prod"]


def is_testing() -> bool:
    """
    Check if running in testing environment.
    
    Returns:
        True if testing environment
    """
    env = get_env_var("ENVIRONMENT", "development").lower()
    return env in ["testing", "test"] or get_env_var("TESTING", "false").lower() == "true"


def get_log_level() -> str:
    """
    Get logging level from environment.
    
    Returns:
        Log level string
    """
    if is_production():
        return get_env_var("LOG_LEVEL", "INFO")
    else:
        return get_env_var("LOG_LEVEL", "DEBUG")


def get_cache_config() -> Dict[str, Any]:
    """
    Get cache configuration.
    
    Returns:
        Cache configuration dictionary
    """
    return {
        "cache_dir": get_env_var("CACHE_DIR", "./cache"),
        "cache_ttl": int(get_env_var("CACHE_TTL", "3600")),  # 1 hour default
        "cache_enabled": get_env_var("CACHE_ENABLED", "true").lower() == "true"
    }


def get_notification_config() -> Dict[str, Any]:
    """
    Get notification configuration.
    
    Returns:
        Notification configuration dictionary
    """
    return {
        "channel": get_env_var("NOTIFICATION_CHANNEL", "stackit_notifications"),
        "enabled": get_env_var("NOTIFICATIONS_ENABLED", "true").lower() == "true",
        "email_enabled": get_env_var("EMAIL_NOTIFICATIONS_ENABLED", "false").lower() == "true"
    }

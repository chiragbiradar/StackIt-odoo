"""
Server utilities for StackIt application.
Integrated from feature/auth branch.
"""
import uvicorn
from typing import Optional
import logging

from .config import is_development, is_production, get_env_var

logger = logging.getLogger(__name__)


def run_server(
    app_module: str = "app.main:app",
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: Optional[bool] = None,
    workers: Optional[int] = None,
    log_level: Optional[str] = None
) -> None:
    """
    Run the FastAPI server with appropriate configuration.
    
    Args:
        app_module: Module path to FastAPI app
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload (default: True in development)
        workers: Number of worker processes (default: 1 in development, 4 in production)
        log_level: Log level (default: debug in development, info in production)
    """
    # Set defaults based on environment
    if reload is None:
        reload = is_development()
    
    if workers is None:
        workers = 1 if is_development() else 4
    
    if log_level is None:
        log_level = "debug" if is_development() else "info"
    
    # Override with environment variables
    host = get_env_var("HOST", host)
    port = int(get_env_var("PORT", str(port)))
    
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Environment: {'development' if is_development() else 'production'}")
    logger.info(f"Reload: {reload}, Workers: {workers}, Log level: {log_level}")
    
    if is_production() and reload:
        logger.warning("Auto-reload is enabled in production - this is not recommended")
    
    uvicorn.run(
        app_module,
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,  # Can't use workers with reload
        log_level=log_level,
        access_log=True,
        use_colors=is_development()
    )


def get_server_info() -> dict:
    """
    Get server configuration information.
    
    Returns:
        Dictionary with server configuration
    """
    return {
        "host": get_env_var("HOST", "0.0.0.0"),
        "port": int(get_env_var("PORT", "8000")),
        "environment": get_env_var("ENVIRONMENT", "development"),
        "debug": is_development(),
        "reload": is_development(),
        "workers": 1 if is_development() else 4,
        "log_level": "debug" if is_development() else "info"
    }


if __name__ == "__main__":
    # Allow running this module directly to start the server
    run_server()

"""
Logging configuration for the StackIt application.
"""
import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any

from ..config import settings


def setup_logging() -> None:
    """Set up logging configuration for the application."""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Logging configuration
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(lineno)d %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO" if settings.environment == "production" else "DEBUG",
                "formatter": "default",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": log_dir / "stackit.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": log_dir / "stackit_errors.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": "INFO" if settings.environment == "production" else "DEBUG",
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "app": {
                "level": "DEBUG",
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "sqlalchemy.engine": {
                "level": "INFO" if settings.debug else "WARNING",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "sqlalchemy.dialects": {
                "level": "WARNING",
                "handlers": ["file"],
                "propagate": False
            },
            "sqlalchemy.pool": {
                "level": "WARNING",
                "handlers": ["file"],
                "propagate": False
            },
            "sqlalchemy.orm": {
                "level": "WARNING",
                "handlers": ["file"],
                "propagate": False
            }
        }
    }
    
    # Apply logging configuration
    logging.config.dictConfig(logging_config)
    
    # Set up request ID logging (for tracing requests)
    setup_request_logging()


def setup_request_logging() -> None:
    """Set up request ID logging for tracing requests."""
    
    class RequestIDFilter(logging.Filter):
        """Add request ID to log records."""
        
        def filter(self, record):
            # Try to get request ID from context (would need to be set in middleware)
            request_id = getattr(record, 'request_id', None)
            if not request_id:
                import uuid
                request_id = str(uuid.uuid4())[:8]
            
            record.request_id = request_id
            return True
    
    # Add request ID filter to all handlers
    for handler in logging.getLogger().handlers:
        handler.addFilter(RequestIDFilter())


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to other classes."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger instance for this class."""
        return logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")


# Performance logging utilities
class PerformanceLogger:
    """Utility class for performance logging."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_slow_query(self, query: str, duration: float, threshold: float = 1.0):
        """Log slow database queries."""
        if duration > threshold:
            self.logger.warning(
                f"Slow query detected: {duration:.3f}s",
                extra={
                    "query": query,
                    "duration": duration,
                    "threshold": threshold
                }
            )
    
    def log_api_performance(self, endpoint: str, method: str, duration: float, status_code: int):
        """Log API endpoint performance."""
        level = logging.WARNING if duration > 2.0 else logging.INFO
        self.logger.log(
            level,
            f"API {method} {endpoint} - {status_code} - {duration:.3f}s",
            extra={
                "endpoint": endpoint,
                "method": method,
                "duration": duration,
                "status_code": status_code
            }
        )


# Security logging utilities
class SecurityLogger:
    """Utility class for security-related logging."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_authentication_attempt(self, username: str, success: bool, ip_address: str = None):
        """Log authentication attempts."""
        level = logging.INFO if success else logging.WARNING
        message = f"Authentication {'successful' if success else 'failed'} for user: {username}"
        
        self.logger.log(
            level,
            message,
            extra={
                "username": username,
                "success": success,
                "ip_address": ip_address,
                "event_type": "authentication"
            }
        )
    
    def log_authorization_failure(self, username: str, resource: str, action: str, ip_address: str = None):
        """Log authorization failures."""
        self.logger.warning(
            f"Authorization denied for user {username} accessing {resource} with action {action}",
            extra={
                "username": username,
                "resource": resource,
                "action": action,
                "ip_address": ip_address,
                "event_type": "authorization_failure"
            }
        )
    
    def log_suspicious_activity(self, description: str, username: str = None, ip_address: str = None, **kwargs):
        """Log suspicious activities."""
        self.logger.error(
            f"Suspicious activity detected: {description}",
            extra={
                "username": username,
                "ip_address": ip_address,
                "event_type": "suspicious_activity",
                **kwargs
            }
        )

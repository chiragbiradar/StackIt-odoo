"""
Cache management service for StackIt Q&A Platform.
Provides endpoints to manage response cache.
"""

from diskcache import Cache
from fastapi import APIRouter, HTTPException

# Create router
router = APIRouter(prefix="/cache", tags=["Cache Management"])

# Cache instance
cache = Cache("./cache")


@router.get("/stats")
async def get_cache_stats():
    """
    Get cache statistics.

    Returns:
    - Cache size (number of entries)
    - Cache volume (disk space used)
    - Cache directory path
    """
    try:
        return {
            "size": len(cache),
            "volume": cache.volume(),
            "directory": cache.directory,
            "status": "active"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache stats: {str(e)}"
        ) from e


@router.delete("/clear")
async def clear_cache():
    """
    Clear all cached responses.

    This will remove all cached data and force fresh requests
    to hit the database until cache is rebuilt.
    """
    try:
        cache.clear()
        return {
            "message": "Cache cleared successfully",
            "status": "cleared"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        ) from e


@router.delete("/clear/{pattern}")
async def clear_cache_pattern(pattern: str):
    """
    Clear cache entries matching a pattern.

    Args:
    - pattern: Pattern to match cache keys (e.g., "questions", "users")

    Note: This is a simplified implementation.
    For production, you'd implement proper pattern matching.
    """
    try:
        cleared_count = 0
        keys_to_delete = []

        # Find keys that contain the pattern
        for key in cache.iterkeys():
            if pattern in str(key):
                keys_to_delete.append(key)

        # Delete matching keys
        for key in keys_to_delete:
            del cache[key]
            cleared_count += 1

        return {
            "message": f"Cleared {cleared_count} cache entries matching '{pattern}'",
            "pattern": pattern,
            "cleared_count": cleared_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache pattern: {str(e)}"
        ) from e


@router.get("/info")
async def get_cache_info():
    """
    Get detailed cache information and configuration.

    Returns cache settings and middleware configuration details.
    """
    try:
        return {
            "cache_directory": "./cache",
            "middleware_config": {
                "default_expire": 300,
                "endpoint_expiry": {
                    "/questions": 600,
                    "/answers": 300,
                    "/users": 1800,
                    "/tags": 3600
                },
                "excluded_paths": [
                    "/docs",
                    "/redoc",
                    "/openapi.json",
                    "/health",
                    "/metrics",
                    "/auth",
                    "/notifications"
                ]
            },
            "cache_stats": {
                "size": len(cache),
                "volume": cache.volume()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache info: {str(e)}"
        ) from e

"""
Response caching middleware using diskcache.
Caches GET requests to improve performance.
"""

import hashlib
import json
from typing import Callable

from diskcache import Cache
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """
    Middleware to cache GET responses using diskcache.

    Features:
    - Caches only GET requests
    - Configurable cache expiry time
    - Excludes certain endpoints from caching
    - Uses request URL and query params as cache key
    """

    def __init__(
        self,
        app,
        cache_dir: str = "./cache",
        default_expire: int = 300,  # 5 minutes default
        exclude_paths: list = None
    ):
        super().__init__(app)
        self.cache = Cache(directory=cache_dir)
        self.default_expire = default_expire
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics"
        ]

    def _should_cache(self, request: Request) -> bool:
        """Determine if the request should be cached."""
        # Only cache GET requests
        if request.method != "GET":
            return False

        # Skip excluded paths
        path = request.url.path
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False

        # Skip if Authorization header present (user-specific data)
        if "authorization" in request.headers:
            return False

        return True

    def _generate_cache_key(self, request: Request) -> str:
        """Generate a unique cache key for the request."""
        # Include path, query params, and relevant headers
        key_data = {
            "path": request.url.path,
            "query": str(request.query_params),
            "method": request.method
        }

        # Create hash of the key data
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cache_expiry(self, request: Request) -> int:
        """Get cache expiry time based on the endpoint."""
        path = request.url.path

        # Different expiry times for different endpoints
        if path.startswith("/questions"):
            return 600  # 10 minutes for questions
        elif path.startswith("/answers"):
            return 300  # 5 minutes for answers
        elif path.startswith("/users"):
            return 1800  # 30 minutes for user data
        elif path.startswith("/tags"):
            return 3600  # 1 hour for tags
        else:
            return self.default_expire

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and handle caching."""

        # Check if we should cache this request
        if not self._should_cache(request):
            return await call_next(request)

        # Generate cache key
        cache_key = self._generate_cache_key(request)

        # Try to get cached response
        cached_response = self.cache.get(cache_key)
        if cached_response is not None:
            # Return cached response
            return Response(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers=cached_response["headers"],
                media_type=cached_response["media_type"]
            )

        # No cached response, process the request
        response = await call_next(request)
        HTTP_200_OK = 200
        # Cache successful responses
        if response.status_code == HTTP_200_OK:
            # Read response content
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # Prepare cache data
            cache_data = {
                "content": response_body,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": response.media_type
            }

            # Store in cache with expiry
            expiry = self._get_cache_expiry(request)
            self.cache.set(cache_key, cache_data, expire=expiry)

            # Create new response with the body
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=response.headers,
                media_type=response.media_type
            )

        return response

    def clear_cache(self, pattern: str = None):
        """Clear cache entries. If pattern provided, clear matching keys only."""
        if pattern:
            # Clear specific pattern (would need implementation)
            pass
        else:
            # Clear all cache
            self.cache.clear()

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "volume": self.cache.volume(),
            "directory": self.cache.directory
        }

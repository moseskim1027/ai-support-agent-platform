"""Rate limiting middleware using SlowAPI"""

import logging

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings

logger = logging.getLogger(__name__)


def get_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting

    Uses:
    1. User ID from auth token if authenticated
    2. API key if present
    3. Remote IP address as fallback

    Args:
        request: FastAPI request object

    Returns:
        str: Identifier for rate limiting
    """
    # Try to get user from auth (will be implemented with JWT)
    user = getattr(request.state, "user", None)
    if user:
        return f"user:{user.get('sub', user.get('id', 'unknown'))}"

    # Try to get API key from header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key[:10]}"

    # Fallback to IP address
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_identifier,
    default_limits=(
        ["100/minute", "1000/hour", "5000/day"] if settings.is_production else ["1000/minute"]
    ),
    storage_uri=settings.redis_url,
    strategy="fixed-window",
    headers_enabled=True,
)


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Custom handler for rate limit exceeded errors

    Args:
        request: FastAPI request
        exc: RateLimitExceeded exception

    Returns:
        Response: JSON response with rate limit info
    """
    logger.warning(f"Rate limit exceeded for {get_identifier(request)} on {request.url.path}")

    return Response(
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": exc.detail,
        },
        status_code=429,
        headers={
            "Retry-After": str(exc.detail),
            "X-RateLimit-Limit": request.state.view_rate_limit,
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(exc.detail),
        },
    )

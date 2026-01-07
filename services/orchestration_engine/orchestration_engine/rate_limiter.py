"""
Rate Limiting Module

Provides simple rate limiting for API endpoints.
Uses in-memory storage by default, can be extended with Redis for distributed systems.
"""

import time
from collections import defaultdict
from typing import Optional, Callable
from functools import wraps
from fastapi import HTTPException, Request, status


class RateLimiter:
    """
    Simple token bucket rate limiter.

    Can be used as a FastAPI dependency for rate limiting endpoints.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute
            requests_per_hour: Maximum requests allowed per hour
            burst_limit: Maximum burst requests allowed in short succession
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit

        # In-memory storage for rate tracking
        # For production, consider using Redis
        self._minute_requests: dict = defaultdict(list)
        self._hour_requests: dict = defaultdict(list)

    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Try to get user ID from authenticated request
        if hasattr(request.state, 'user') and request.state.user:
            return f"user:{request.state.user.id}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        return f"ip:{request.client.host if request.client else 'unknown'}"

    def _clean_old_requests(self, requests_list: list, window_seconds: int) -> list:
        """Remove requests older than the time window."""
        current_time = time.time()
        cutoff = current_time - window_seconds
        return [req_time for req_time in requests_list if req_time > cutoff]

    def check_rate_limit(self, client_id: str) -> tuple[bool, dict]:
        """
        Check if client is within rate limits.

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        current_time = time.time()

        # Clean old requests
        self._minute_requests[client_id] = self._clean_old_requests(
            self._minute_requests[client_id], 60
        )
        self._hour_requests[client_id] = self._clean_old_requests(
            self._hour_requests[client_id], 3600
        )

        minute_count = len(self._minute_requests[client_id])
        hour_count = len(self._hour_requests[client_id])

        # Check limits
        if minute_count >= self.requests_per_minute:
            return False, {
                "limit": self.requests_per_minute,
                "window": "minute",
                "remaining": 0,
                "reset": int(60 - (current_time - self._minute_requests[client_id][0]))
            }

        if hour_count >= self.requests_per_hour:
            return False, {
                "limit": self.requests_per_hour,
                "window": "hour",
                "remaining": 0,
                "reset": int(3600 - (current_time - self._hour_requests[client_id][0]))
            }

        # Check burst (requests in last 5 seconds)
        recent_requests = [
            req_time for req_time in self._minute_requests[client_id]
            if current_time - req_time < 5
        ]
        if len(recent_requests) >= self.burst_limit:
            return False, {
                "limit": self.burst_limit,
                "window": "burst",
                "remaining": 0,
                "reset": 5
            }

        return True, {
            "minute_remaining": self.requests_per_minute - minute_count,
            "hour_remaining": self.requests_per_hour - hour_count
        }

    def record_request(self, client_id: str):
        """Record a request for the given client."""
        current_time = time.time()
        self._minute_requests[client_id].append(current_time)
        self._hour_requests[client_id].append(current_time)

    async def __call__(self, request: Request):
        """FastAPI dependency for rate limiting."""
        client_id = self._get_client_id(request)
        is_allowed, info = self.check_rate_limit(client_id)

        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {info.get('reset', 60)} seconds.",
                headers={
                    "X-RateLimit-Limit": str(info.get('limit', 0)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info.get('reset', 60)),
                    "Retry-After": str(info.get('reset', 60))
                }
            )

        # Record this request
        self.record_request(client_id)

        # Add rate limit headers to response
        request.state.rate_limit_info = info
        return True


# Create default rate limiters for different endpoint types
default_rate_limiter = RateLimiter(
    requests_per_minute=60,
    requests_per_hour=1000,
    burst_limit=10
)

# Stricter rate limiter for auth endpoints
auth_rate_limiter = RateLimiter(
    requests_per_minute=10,
    requests_per_hour=100,
    burst_limit=3
)

# More permissive rate limiter for read-only endpoints
read_rate_limiter = RateLimiter(
    requests_per_minute=120,
    requests_per_hour=5000,
    burst_limit=20
)

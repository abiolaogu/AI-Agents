"""
Rate Limiting Module

Provides rate limiting for API endpoints with support for both
in-memory and Redis-based distributed rate limiting.

For production deployments with multiple instances, use Redis-based
rate limiting by setting RATE_LIMIT_REDIS_ENABLED=true.
"""

import os
import time
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Optional, Tuple, Dict, Any
from fastapi import HTTPException, Request, status

logger = logging.getLogger(__name__)


class BaseRateLimiter(ABC):
    """Abstract base class for rate limiters."""

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

    @abstractmethod
    def check_rate_limit(self, client_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if client is within rate limits."""
        pass

    @abstractmethod
    def record_request(self, client_id: str):
        """Record a request for the given client."""
        pass

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


class InMemoryRateLimiter(BaseRateLimiter):
    """
    In-memory rate limiter using token bucket algorithm.

    Suitable for single-instance deployments or development.
    For multi-instance production deployments, use RedisRateLimiter.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10
    ):
        super().__init__(requests_per_minute, requests_per_hour, burst_limit)
        self._minute_requests: Dict[str, list] = defaultdict(list)
        self._hour_requests: Dict[str, list] = defaultdict(list)

    def _clean_old_requests(self, requests_list: list, window_seconds: int) -> list:
        """Remove requests older than the time window."""
        current_time = time.time()
        cutoff = current_time - window_seconds
        return [req_time for req_time in requests_list if req_time > cutoff]

    def check_rate_limit(self, client_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if client is within rate limits."""
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


class RedisRateLimiter(BaseRateLimiter):
    """
    Redis-based distributed rate limiter using sliding window algorithm.

    Suitable for multi-instance production deployments where rate limiting
    needs to be consistent across all instances.

    Requires redis-py: pip install redis
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10,
        redis_url: Optional[str] = None,
        key_prefix: str = "rate_limit"
    ):
        super().__init__(requests_per_minute, requests_per_hour, burst_limit)
        self.key_prefix = key_prefix
        self._redis_client = None

        # Initialize Redis connection
        redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            import redis
            self._redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self._redis_client.ping()
            logger.info(f"Redis rate limiter connected to {redis_url}")
        except ImportError:
            logger.warning("redis-py not installed. Falling back to in-memory rate limiting.")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Falling back to in-memory rate limiting.")

        # Fallback to in-memory if Redis is not available
        if self._redis_client is None:
            self._fallback = InMemoryRateLimiter(
                requests_per_minute, requests_per_hour, burst_limit
            )
        else:
            self._fallback = None

    def _get_redis_key(self, client_id: str, window: str) -> str:
        """Generate Redis key for the given client and time window."""
        return f"{self.key_prefix}:{window}:{client_id}"

    def check_rate_limit(self, client_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Check if client is within rate limits using Redis."""
        if self._fallback:
            return self._fallback.check_rate_limit(client_id)

        current_time = time.time()
        pipe = self._redis_client.pipeline()

        # Keys for different windows
        minute_key = self._get_redis_key(client_id, "minute")
        hour_key = self._get_redis_key(client_id, "hour")
        burst_key = self._get_redis_key(client_id, "burst")

        try:
            # Remove expired entries and count remaining (sliding window)
            minute_cutoff = current_time - 60
            hour_cutoff = current_time - 3600
            burst_cutoff = current_time - 5

            pipe.zremrangebyscore(minute_key, 0, minute_cutoff)
            pipe.zremrangebyscore(hour_key, 0, hour_cutoff)
            pipe.zremrangebyscore(burst_key, 0, burst_cutoff)

            pipe.zcard(minute_key)
            pipe.zcard(hour_key)
            pipe.zcard(burst_key)

            results = pipe.execute()

            # Results: [removed_minute, removed_hour, removed_burst, count_minute, count_hour, count_burst]
            minute_count = results[3]
            hour_count = results[4]
            burst_count = results[5]

            # Check limits
            if minute_count >= self.requests_per_minute:
                # Get oldest entry to calculate reset time
                oldest = self._redis_client.zrange(minute_key, 0, 0, withscores=True)
                reset = int(60 - (current_time - oldest[0][1])) if oldest else 60
                return False, {
                    "limit": self.requests_per_minute,
                    "window": "minute",
                    "remaining": 0,
                    "reset": max(1, reset)
                }

            if hour_count >= self.requests_per_hour:
                oldest = self._redis_client.zrange(hour_key, 0, 0, withscores=True)
                reset = int(3600 - (current_time - oldest[0][1])) if oldest else 3600
                return False, {
                    "limit": self.requests_per_hour,
                    "window": "hour",
                    "remaining": 0,
                    "reset": max(1, reset)
                }

            if burst_count >= self.burst_limit:
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

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # On Redis error, allow the request (fail open)
            return True, {"error": str(e)}

    def record_request(self, client_id: str):
        """Record a request for the given client in Redis."""
        if self._fallback:
            return self._fallback.record_request(client_id)

        current_time = time.time()
        pipe = self._redis_client.pipeline()

        try:
            # Add to sorted sets with current timestamp as score
            minute_key = self._get_redis_key(client_id, "minute")
            hour_key = self._get_redis_key(client_id, "hour")
            burst_key = self._get_redis_key(client_id, "burst")

            # Use timestamp as both score and member (with some uniqueness)
            member = f"{current_time}:{id(current_time)}"

            pipe.zadd(minute_key, {member: current_time})
            pipe.zadd(hour_key, {member: current_time})
            pipe.zadd(burst_key, {member: current_time})

            # Set expiry on keys to auto-cleanup
            pipe.expire(minute_key, 120)  # 2 minutes
            pipe.expire(hour_key, 7200)   # 2 hours
            pipe.expire(burst_key, 30)    # 30 seconds

            pipe.execute()

        except Exception as e:
            logger.error(f"Redis rate limit record failed: {e}")


def create_rate_limiter(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000,
    burst_limit: int = 10
) -> BaseRateLimiter:
    """
    Factory function to create the appropriate rate limiter.

    Uses Redis if RATE_LIMIT_REDIS_ENABLED=true, otherwise uses in-memory.
    """
    use_redis = os.getenv("RATE_LIMIT_REDIS_ENABLED", "false").lower() == "true"

    if use_redis:
        return RedisRateLimiter(
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
            burst_limit=burst_limit
        )
    else:
        return InMemoryRateLimiter(
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
            burst_limit=burst_limit
        )


# Create default rate limiters for different endpoint types
# These will automatically use Redis if RATE_LIMIT_REDIS_ENABLED=true
default_rate_limiter = create_rate_limiter(
    requests_per_minute=int(os.getenv("RATE_LIMIT_DEFAULT_PER_MINUTE", "60")),
    requests_per_hour=int(os.getenv("RATE_LIMIT_DEFAULT_PER_HOUR", "1000")),
    burst_limit=10
)

# Stricter rate limiter for auth endpoints
auth_rate_limiter = create_rate_limiter(
    requests_per_minute=int(os.getenv("RATE_LIMIT_AUTH_PER_MINUTE", "10")),
    requests_per_hour=int(os.getenv("RATE_LIMIT_AUTH_PER_HOUR", "100")),
    burst_limit=3
)

# More permissive rate limiter for read-only endpoints
read_rate_limiter = create_rate_limiter(
    requests_per_minute=int(os.getenv("RATE_LIMIT_READ_PER_MINUTE", "120")),
    requests_per_hour=int(os.getenv("RATE_LIMIT_READ_PER_HOUR", "5000")),
    burst_limit=20
)


# Backward compatibility alias
RateLimiter = InMemoryRateLimiter

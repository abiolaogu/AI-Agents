"""
API Gateway Authentication & Authorization Middleware
Secures access to all 1,500 agents
"""

import jwt
import time
import redis
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import wraps
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

security = HTTPBearer()


class AuthManager:
    """Authentication and authorization manager"""

    def __init__(
        self,
        jwt_secret: str,
        redis_client: redis.Redis,
        token_expiry: int = 3600
    ):
        self.jwt_secret = jwt_secret
        self.redis = redis_client
        self.token_expiry = token_expiry

    def create_token(self, user_id: str, roles: list[str], permissions: list[str]) -> str:
        """Create JWT token"""
        payload = {
            "user_id": user_id,
            "roles": roles,
            "permissions": permissions,
            "iat": int(time.time()),
            "exp": int(time.time()) + self.token_expiry
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        return token

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            # Check if token is blacklisted
            if self.redis.exists(f"blacklist:{token}"):
                logger.warning("Attempted use of blacklisted token")
                return None

            # Decode and verify token
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])

            # Additional validation
            if payload.get("exp", 0) < time.time():
                return None

            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Expired token")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def blacklist_token(self, token: str):
        """Blacklist a token (for logout)"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            exp = payload.get("exp", 0)
            ttl = max(0, exp - int(time.time()))

            self.redis.setex(f"blacklist:{token}", ttl, "1")
            logger.info("Token blacklisted")
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")

    def has_permission(self, token_payload: Dict[str, Any], required_permission: str) -> bool:
        """Check if user has required permission"""
        user_permissions = token_payload.get("permissions", [])
        user_roles = token_payload.get("roles", [])

        # Admin role has all permissions
        if "admin" in user_roles:
            return True

        return required_permission in user_permissions

    def rate_limit_check(self, user_id: str, limit: int = 100, window: int = 60) -> bool:
        """Check rate limit for user"""
        key = f"rate_limit:{user_id}"
        current = self.redis.incr(key)

        if current == 1:
            self.redis.expire(key, window)

        if current > limit:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False

        return True


class APIKeyAuth:
    """API Key authentication for programmatic access"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def create_api_key(self, user_id: str, name: str, permissions: list[str]) -> str:
        """Create API key for user"""
        import secrets

        api_key = f"sk-{secrets.token_urlsafe(32)}"
        key_data = {
            "user_id": user_id,
            "name": name,
            "permissions": ",".join(permissions),
            "created_at": int(time.time())
        }

        self.redis.hset(f"api_key:{api_key}", mapping=key_data)
        logger.info(f"Created API key for user {user_id}")

        return api_key

    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key"""
        key_data = self.redis.hgetall(f"api_key:{api_key}")

        if not key_data:
            return None

        return {
            "user_id": key_data.get(b"user_id", b"").decode(),
            "name": key_data.get(b"name", b"").decode(),
            "permissions": key_data.get(b"permissions", b"").decode().split(",")
        }

    def revoke_api_key(self, api_key: str):
        """Revoke API key"""
        self.redis.delete(f"api_key:{api_key}")
        logger.info(f"Revoked API key: {api_key}")


# FastAPI dependency for authentication
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    auth_manager: AuthManager = Depends()
) -> Dict[str, Any]:
    """FastAPI dependency to get current authenticated user"""

    token = credentials.credentials

    # Try JWT token
    payload = auth_manager.verify_token(token)
    if payload:
        # Check rate limit
        if not auth_manager.rate_limit_check(payload["user_id"]):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )
        return payload

    # Try API key
    api_key_auth = APIKeyAuth(auth_manager.redis)
    api_key_data = api_key_auth.verify_api_key(token)

    if api_key_data:
        return api_key_data

    raise HTTPException(
        status_code=401,
        detail="Invalid authentication credentials"
    )


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: Dict = Depends(get_current_user), **kwargs):
            auth_manager = AuthManager(jwt_secret="secret", redis_client=redis.Redis())

            if not auth_manager.has_permission(current_user, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {permission} required"
                )

            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


# Example usage in agent API
"""
from fastapi import FastAPI, Depends
from auth_middleware import get_current_user, require_permission

app = FastAPI()

@app.post("/api/v1/execute")
@require_permission("agent:execute")
async def execute_task(
    request: AgentRequest,
    current_user: Dict = Depends(get_current_user)
):
    # Execute agent task
    pass
"""

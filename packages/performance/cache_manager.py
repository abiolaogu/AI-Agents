"""
Advanced Multi-Tier Caching System
L1: Redis (hot cache), L2: Hazelcast (warm cache), L3: Qdrant (semantic cache)
"""

from typing import Any, Optional, Callable, Dict
import asyncio
import hashlib
import json
import time
from functools import wraps
from dataclasses import dataclass
import redis.asyncio as redis
from enum import Enum

class CacheTier(Enum):
    """Cache tier levels"""
    L1_HOT = "l1_hot"           # Redis - sub-ms latency
    L2_WARM = "l2_warm"         # Hazelcast - few ms latency
    L3_SEMANTIC = "l3_semantic" # Qdrant - semantic search
    L4_CDN = "l4_cdn"           # CloudFlare - edge caching

@dataclass
class CacheConfig:
    """Cache configuration"""
    ttl_seconds: int = 3600
    tier: CacheTier = CacheTier.L1_HOT
    namespace: str = "default"
    semantic_threshold: float = 0.95
    compress: bool = True
    serializer: str = "json"  # json, msgpack, pickle

class MultiTierCacheManager:
    """Advanced multi-tier caching system"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        hazelcast_config: Optional[Dict] = None,
        qdrant_manager: Optional[Any] = None
    ):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.hazelcast_client = None
        self.qdrant_manager = qdrant_manager

        # Performance metrics
        self.stats = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "l3_hits": 0,
            "l3_misses": 0,
            "total_requests": 0
        }

    async def initialize(self):
        """Initialize all cache tiers"""
        # L1: Redis
        self.redis_client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=1000
        )

        # L2: Hazelcast (optional)
        try:
            import hazelcast
            self.hazelcast_client = hazelcast.HazelcastClient(
                cluster_members=["localhost:5701"],
                lifecycle_listeners=[self._hazelcast_lifecycle_listener]
            )
        except ImportError:
            print("Hazelcast not available, skipping L2 cache")

        print("✓ Multi-tier cache initialized")

    def _hazelcast_lifecycle_listener(self, state):
        """Hazelcast lifecycle listener"""
        print(f"Hazelcast state: {state}")

    async def get(
        self,
        key: str,
        config: Optional[CacheConfig] = None
    ) -> Optional[Any]:
        """Get value from cache (checks all tiers)"""
        config = config or CacheConfig()
        self.stats["total_requests"] += 1

        # L1: Redis (fastest)
        value = await self._get_from_redis(key, config)
        if value is not None:
            self.stats["l1_hits"] += 1
            return value
        self.stats["l1_misses"] += 1

        # L2: Hazelcast
        if self.hazelcast_client and config.tier.value >= CacheTier.L2_WARM.value:
            value = await self._get_from_hazelcast(key, config)
            if value is not None:
                self.stats["l2_hits"] += 1
                # Populate L1 for next time
                await self._set_to_redis(key, value, config)
                return value
            self.stats["l2_misses"] += 1

        # L3: Semantic cache (Qdrant)
        if self.qdrant_manager and config.tier == CacheTier.L3_SEMANTIC:
            value = await self._get_from_semantic_cache(key, config)
            if value is not None:
                self.stats["l3_hits"] += 1
                # Populate upper tiers
                await self._set_to_redis(key, value, config)
                if self.hazelcast_client:
                    await self._set_to_hazelcast(key, value, config)
                return value
            self.stats["l3_misses"] += 1

        return None

    async def set(
        self,
        key: str,
        value: Any,
        config: Optional[CacheConfig] = None
    ):
        """Set value in cache (all configured tiers)"""
        config = config or CacheConfig()

        # Set in all tiers
        await self._set_to_redis(key, value, config)

        if self.hazelcast_client and config.tier.value >= CacheTier.L2_WARM.value:
            await self._set_to_hazelcast(key, value, config)

        if self.qdrant_manager and config.tier == CacheTier.L3_SEMANTIC:
            await self._set_to_semantic_cache(key, value, config)

    async def delete(self, key: str):
        """Delete from all cache tiers"""
        if self.redis_client:
            await self.redis_client.delete(key)
        if self.hazelcast_client:
            map_instance = self.hazelcast_client.get_map("cache").blocking()
            await asyncio.to_thread(map_instance.remove, key)

    async def _get_from_redis(self, key: str, config: CacheConfig) -> Optional[Any]:
        """Get from Redis (L1)"""
        if not self.redis_client:
            return None

        cache_key = self._make_cache_key(key, config)
        value = await self.redis_client.get(cache_key)

        if value:
            return self._deserialize(value, config)
        return None

    async def _set_to_redis(self, key: str, value: Any, config: CacheConfig):
        """Set to Redis (L1)"""
        if not self.redis_client:
            return

        cache_key = self._make_cache_key(key, config)
        serialized = self._serialize(value, config)

        await self.redis_client.setex(
            cache_key,
            config.ttl_seconds,
            serialized
        )

    async def _get_from_hazelcast(self, key: str, config: CacheConfig) -> Optional[Any]:
        """Get from Hazelcast (L2)"""
        if not self.hazelcast_client:
            return None

        try:
            map_instance = self.hazelcast_client.get_map("cache").blocking()
            value = await asyncio.to_thread(
                map_instance.get,
                self._make_cache_key(key, config)
            )
            if value:
                return self._deserialize(value, config)
        except Exception as e:
            print(f"Hazelcast get error: {e}")

        return None

    async def _set_to_hazelcast(self, key: str, value: Any, config: CacheConfig):
        """Set to Hazelcast (L2)"""
        if not self.hazelcast_client:
            return

        try:
            map_instance = self.hazelcast_client.get_map("cache").blocking()
            await asyncio.to_thread(
                map_instance.put,
                self._make_cache_key(key, config),
                self._serialize(value, config),
                config.ttl_seconds
            )
        except Exception as e:
            print(f"Hazelcast set error: {e}")

    async def _get_from_semantic_cache(self, key: str, config: CacheConfig) -> Optional[Any]:
        """Get from semantic cache (L3)"""
        if not self.qdrant_manager:
            return None

        result = await self.qdrant_manager.semantic_cache_get(
            collection_name="semantic_cache",
            query=key,
            similarity_threshold=config.semantic_threshold,
            ttl_hours=config.ttl_seconds // 3600
        )

        return result.get("result") if result else None

    async def _set_to_semantic_cache(self, key: str, value: Any, config: CacheConfig):
        """Set to semantic cache (L3)"""
        if not self.qdrant_manager:
            return

        await self.qdrant_manager.semantic_cache_set(
            collection_name="semantic_cache",
            query=key,
            result=value,
            metadata={"namespace": config.namespace}
        )

    def _make_cache_key(self, key: str, config: CacheConfig) -> str:
        """Create namespaced cache key"""
        return f"{config.namespace}:{key}"

    def _serialize(self, value: Any, config: CacheConfig) -> str:
        """Serialize value for storage"""
        if config.serializer == "json":
            return json.dumps(value)
        elif config.serializer == "msgpack":
            import msgpack
            return msgpack.packb(value, use_bin_type=True)
        elif config.serializer == "pickle":
            import pickle  # nosec B403
            import base64
            return base64.b64encode(pickle.dumps(value)).decode()  # nosec B301
        else:
            return str(value)

    def _deserialize(self, value: str, config: CacheConfig) -> Any:
        """Deserialize value from storage"""
        if config.serializer == "json":
            return json.loads(value)
        elif config.serializer == "msgpack":
            import msgpack
            return msgpack.unpackb(value, raw=False)
        elif config.serializer == "pickle":
            import pickle  # nosec B403
            import base64
            return pickle.loads(base64.b64decode(value))  # nosec B301
        else:
            return value

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total = self.stats["total_requests"]
        if total == 0:
            return self.stats

        return {
            **self.stats,
            "l1_hit_rate": self.stats["l1_hits"] / total * 100,
            "l2_hit_rate": self.stats["l2_hits"] / total * 100,
            "l3_hit_rate": self.stats["l3_hits"] / total * 100,
            "overall_hit_rate": (
                self.stats["l1_hits"] + self.stats["l2_hits"] + self.stats["l3_hits"]
            ) / total * 100
        }

    async def close(self):
        """Close all cache connections"""
        if self.redis_client:
            await self.redis_client.close()
        if self.hazelcast_client:
            self.hazelcast_client.shutdown()


def cached(
    ttl: int = 3600,
    tier: CacheTier = CacheTier.L1_HOT,
    namespace: str = "default",
    key_builder: Optional[Callable] = None
):
    """Decorator for caching function results"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hashlib.sha256(str((args, kwargs)).encode()).hexdigest()}"

            # Try to get from cache
            cache_manager = MultiTierCacheManager()
            await cache_manager.initialize()

            config = CacheConfig(
                ttl_seconds=ttl,
                tier=tier,
                namespace=namespace
            )

            cached_result = await cache_manager.get(cache_key, config)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache_manager.set(cache_key, result, config)

            return result

        return wrapper
    return decorator


# Global cache manager instance
cache_manager = MultiTierCacheManager()

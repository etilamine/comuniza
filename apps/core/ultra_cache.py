"""
Ultra Cache System - Multi-level caching with Redis and L1 memory cache.
Provides enterprise-grade caching with intelligent segmentation and graceful fallbacks.
"""

import time
import hashlib
import json
import pickle
import threading
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Union
from collections import defaultdict, OrderedDict


class CompatibleCache:
    """Fallback cache with compatible interface."""

    def __init__(self, cache=None):
        from django.core.cache import caches
        self.cache = cache or caches['default']

    def generate_cache_key(self, prefix, *args, **kwargs):
        """Generate cache key using same logic as UltimateCache."""
        key_parts = [str(prefix)]

        # Add positional args
        key_parts.extend([str(arg) for arg in args])

        # Add keyword args in sorted order for consistency
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])

        return f"{':'.join(key_parts)}"

    def get(self, key, default=None, loader_func=None, ttl=None, segment=None):
        """Get value from cache with optional loader_func for cache-aside pattern."""
        value = self.cache.get(key, None)

        # Cache hit
        if value is not None:
            return value

        # Cache miss - use loader_func if provided
        if loader_func is not None:
            try:
                value = loader_func()
                if value is not None:
                    # Cache the result with optional TTL
                    self.cache.set(key, value, ttl)
                return value
            except Exception:
                # Let exceptions propagate but don't cache failures
                raise

        return default

    def set(self, key, value, timeout=None):
        return self.cache.set(key, value, timeout)

    def delete(self, key):
        return self.cache.delete(key)

    def get_many(self, keys):
        return self.cache.get_many(keys)

    def set_many(self, mapping, timeout=None):
        return self.cache.set_many(mapping, timeout)

    def delete_many(self, keys):
        return self.cache.delete_many(keys)

    def invalidate_pattern(self, pattern):
        """Invalidate cache keys matching pattern."""
        try:
            keys = self.cache.keys(f"*{pattern}*")
            if keys:
                self.cache.delete_many(keys)
        except (AttributeError, NotImplementedError, Exception):
            # Fallback for cache backends that don't support keys()
            pass

    def __getattr__(self, name):
        """Delegate any other method calls to the cache object."""
        return getattr(self.cache, name)


class L1Cache:
    """L1: In-memory cache with LRU eviction and metrics."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        self.access_times = {}
        self.lock = threading.RLock()
        self.metrics = CacheMetrics()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                self.access_times[key] = time.time()
                value, timestamp = self.cache[key]
                if self._is_expired(timestamp):
                    self._remove(key)
                    return None
                self.cache.move_to_end(key)
                return value
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        with self.lock:
            timestamp = time.time()
            self.cache[key] = (value, timestamp + (ttl_seconds or self.ttl_seconds))
            self.access_times[key] = timestamp
            self._evict_if_needed()
            return True

    def delete(self, key: str) -> bool:
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
                return True
            return False

    def clear(self):
        with self.lock:
            self.cache.clear()
            self.access_times.clear()

    def size(self) -> int:
        return len(self.cache)

    def _is_expired(self, timestamp: float) -> bool:
        return time.time() > timestamp

    def _evict_if_needed(self):
        while len(self.cache) > self.max_size:
            oldest_key = next(iter(self.cache))
            self._remove(oldest_key)

    def _remove(self, key: str):
        if key in self.cache:
            del self.cache[key]
        if key in self.access_times:
            del self.access_times[key]


class L2Cache:
    """L2: Redis cache with distributed access."""

    def __init__(self, ttl_seconds: int = 3600):
        try:
            import redis
        except ImportError:
            raise ImportError("Redis client not available")

        # Use Docker Redis service with database 3 for L2 cache
        self.redis_client = redis.Redis(
            host='redis',
            port=6379,
            db=3,  # Dedicated database for L2 cache
            password=None,
            decode_responses=False,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        self.ttl_seconds = ttl_seconds
        self.metrics = CacheMetrics()
        self.key_prefix = "comuniza_l2:"

    def get(self, key: str) -> Optional[Any]:
        try:
            start_time = time.time()
            redis_key = f"{self.key_prefix}{key}"
            data = self.redis_client.get(redis_key)

            if data is not None:
                self.metrics.record_hit(time.time() - start_time)
                return pickle.loads(data)
            else:
                self.metrics.record_miss()
                return None
        except Exception as e:
            self.metrics.record_error()
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        try:
            redis_key = f"{self.key_prefix}{key}"
            serialized_value = pickle.dumps(value)
            ttl = ttl_seconds or self.ttl_seconds

            result = self.redis_client.setex(redis_key, ttl, serialized_value)
            return result
        except Exception:
            self.metrics.record_error()
            return False

    def delete(self, key: str) -> bool:
        try:
            redis_key = f"{self.key_prefix}{key}"
            result = self.redis_client.delete(redis_key)
            return bool(result)
        except Exception:
            self.metrics.record_error()
            return False

    def clear(self):
        try:
            keys = self.redis_client.keys(f"{self.key_prefix}*")
            if keys:
                self.redis_client.delete(*keys)
        except Exception:
            self.metrics.record_error()
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern in Redis."""
        try:
            redis_pattern = f"{self.key_prefix}{pattern}*"
            keys = self.redis_client.keys(redis_pattern)
            if keys:
                self.redis_client.delete(*keys)
        except Exception:
            self.metrics.record_error()


class CacheMetrics:
    """Metrics collection for cache performance analysis."""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.lock = threading.Lock()

    def record_hit(self, response_time: float):
        with self.lock:
            self.hits += 1

    def record_miss(self):
        with self.lock:
            self.misses += 1

    def record_error(self):
        with self.lock:
            self.errors += 1

    def get_hit_rate(self) -> float:
        with self.lock:
            total = self.hits + self.misses
            return self.hits / total if total > 0 else 0.0

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            return {
                'hits': self.hits,
                'misses': self.misses,
                'errors': self.errors,
                'hit_rate': self.get_hit_rate()
            }


class UltimateCache:
    """Multi-level cache combining L1 (memory) and L2 (Redis) with intelligent routing."""

    def __init__(self, l1_size: int = 1000, l2_ttl: int = 3600):
        self.l1 = L1Cache(max_size=l1_size, ttl_seconds=l2_ttl // 10)  # L1 expires faster
        try:
            self.l2 = L2Cache(ttl_seconds=l2_ttl)
        except Exception:
            self.l2 = None

        self.metrics = CacheMetrics()
        self.segments = {
            'hot': 1,      # Frequently accessed data
            'warm': 5,     # Moderately accessed data
            'cold': 10,     # Rarely accessed data
        }

    def _get_segment_from_key(self, key: str) -> str:
        """Determine cache segment based on key characteristics."""
        key_hash = hash(key) % 20

        if any(prefix in key for prefix in ['user_', 'badge_', 'leaderboard']):
            return 'hot'
        elif any(prefix in key for prefix in ['item_', 'group_', 'loan_']):
            key_hash = hash(key) % 3
            return ['hot', 'warm', 'cold'][key_hash]
        else:
            return 'cold'

    def _should_use_l2(self, segment: str) -> bool:
        """Determine if L2 cache should be used based on segment."""
        return segment != 'hot' and self.l2 is not None

    def get(self, key: str, default: Any = None, loader_func=None, ttl: Optional[int] = None, segment: Optional[str] = None) -> Any:
        """Get value from cache with multi-level strategy and cache-aside pattern support.

        Args:
            key: Cache key to retrieve
            default: Default value if cache miss and no loader_func
            loader_func: Callable to compute value on cache miss
            ttl: Time-to-live in seconds for cached value
            segment: Cache segment ('hot', 'warm', 'cold') - auto-detected if not provided
        """
        # Determine segment
        if segment is None:
            segment = self._get_segment_from_key(key)

        # Try L1 first
        value = self.l1.get(key)
        if value is not None:
            self.metrics.record_hit(0.001)  # L1 hit is very fast
            return value

        # Try L2 if appropriate
        if self._should_use_l2(segment):
            value = self.l2.get(key)
            if value is not None:
                # Promote to L1 if L2 hit
                self.l1.set(key, value, ttl_seconds=ttl or self.segments[segment])
                self.metrics.record_hit(0.005)  # L2 hit
                return value

        # Cache miss - use loader_func if provided
        if loader_func is not None:
            try:
                value = loader_func()
                if value is not None:
                    # Cache the computed value
                    self.set(key, value, ttl_seconds=ttl)
                return value
            except Exception:
                # Let exceptions propagate but don't cache failures
                raise

        self.metrics.record_miss()
        return default

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set value in cache with intelligent segment allocation."""
        segment = self._get_segment_from_key(key)

        # Always set in L1 (fast)
        self.l1.set(key, value, ttl_seconds or self.segments[segment])

        # Also set in L2 if appropriate for persistence
        if self._should_use_l2(segment):
            self.l2.set(key, value, ttl_seconds)

        return True

    def delete(self, key: str) -> bool:
        """Delete value from all cache levels."""
        l1_deleted = self.l1.delete(key)
        l2_deleted = self.l2.delete(key) if self.l2 else False
        return l1_deleted or l2_deleted

    def clear(self):
        """Clear all cache levels."""
        self.l1.clear()
        if self.l2:
            self.l2.clear()

    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern across all levels."""
        # Strip trailing :* for prefix matching (e.g., "items_list:*" → "items_list")
        clean_pattern = pattern.rstrip(':*')
        
        # L1: Use startswith for proper prefix matching
        keys_to_delete = [key for key in list(self.l1.cache.keys()) 
                         if key.startswith(clean_pattern)]
        for key in keys_to_delete:
            self.l1.delete(key)

        # L2: Use Redis pattern deletion
        if self.l2:
            self.l2.invalidate_pattern(clean_pattern)

    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate standardized cache key."""
        key_parts = [str(prefix)]

        # Add positional args
        key_parts.extend([str(arg) for arg in args])

        # Add keyword args in sorted order for consistency
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])

        return f"{':'.join(key_parts)}"

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = {
            'l1_size': self.l1.size(),
            'l2_available': self.l2 is not None,
            'metrics': self.metrics.get_stats(),
        }
        return stats


# Global cache instance - deferred initialization
ultimate_cache = None


def get_ultimate_cache():
    """Get or create ultimate cache instance with lazy initialization."""
    global ultimate_cache
    if ultimate_cache is None:
        try:
            ultimate_cache = UltimateCache()
        except Exception as e:
            # Return a compatible cache wrapper instead
            ultimate_cache = CompatibleCache()
    return ultimate_cache


def cache_ttl(tier: str) -> int:
    """Get TTL based on cache tier."""
    ttl_map = {
        'hot': 1800,    # 30 minutes
        'warm': 3600,   # 1 hour
        'cold': 7200,   # 2 hours
    }
    return ttl_map.get(tier, 3600)

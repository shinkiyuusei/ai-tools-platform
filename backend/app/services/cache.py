"""
Caching service for performance optimization
Implements multi-level caching with Redis and intelligent cache invalidation
"""
import json
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
from datetime import timedelta


class CacheService:
    """
    High-performance caching service with:
    - Multi-level caching (Redis + memory)
    - Intelligent cache invalidation
    - Cache warming strategies
    - Cache analytics
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.local_cache = {}  # Simple in-memory cache for hot data
        self.local_cache_ttl = 60  # 60 seconds for local cache
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (local first, then Redis)"""
        # Check local cache first
        if key in self.local_cache:
            return self.local_cache[key]['data']
        
        # Check Redis
        value = self.redis.get(key)
        if value:
            try:
                data = json.loads(value)
                # Store in local cache
                self.local_cache[key] = {
                    'data': data,
                    'expires': None
                }
                return data
            except json.JSONDecodeError:
                return value
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL"""
        # Store in Redis
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        result = self.redis.setex(key, ttl, value)
        
        # Store in local cache
        self.local_cache[key] = {
            'data': value if not isinstance(value, str) else json.loads(value),
            'expires': None
        }
        
        return result
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        # Remove from local cache
        if key in self.local_cache:
            del self.local_cache[key]
        
        # Remove from Redis
        return self.redis.delete(key) > 0
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        # Remove matching keys from local cache
        keys_to_delete = [k for k in self.local_cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self.local_cache[key]
        
        # Remove from Redis
        keys = self.redis.keys(pattern)
        if keys:
            return self.redis.delete(*keys)
        return 0
    
    def invalidate_by_prefix(self, prefix: str) -> int:
        """Invalidate all cache keys with given prefix"""
        return self.delete_pattern(f"{prefix}*")
    
    def cache_function_result(
        self, 
        ttl: int = 300,
        key_prefix: str = "",
        key_generator: Optional[Callable] = None
    ):
        """
        Decorator to cache function results
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_generator:
                    cache_key = key_generator(*args, **kwargs)
                else:
                    # Default key generation based on function name and arguments
                    key_parts = [key_prefix, func.__name__]
                    key_parts.extend([str(arg) for arg in args])
                    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
                    key_string = ":".join(key_parts)
                    cache_key = f"func:{hashlib.md5(key_string.encode()).hexdigest()}"
                
                # Try to get from cache
                cached = self.get(cache_key)
                if cached is not None:
                    return cached
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator
    
    def warm_cache(self, keys: list, data_loader: Callable):
        """
        Warm cache by pre-loading data
        """
        for key in keys:
            if not self.get(key):
                try:
                    data = data_loader(key)
                    if data:
                        self.set(key, data)
                except Exception as e:
                    print(f"Failed to warm cache for key {key}: {e}")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        redis_info = self.redis.info('stats')
        return {
            'local_cache_size': len(self.local_cache),
            'redis_hits': redis_info.get('keyspace_hits', 0),
            'redis_misses': redis_info.get('keyspace_misses', 0),
            'hit_rate': redis_info.get('keyspace_hits', 0) / max(
                redis_info.get('keyspace_hits', 0) + redis_info.get('keyspace_misses', 1), 1
            )
        }


# Cache key generators for common use cases
def generate_tool_cache_key(tool_id: int) -> str:
    """Generate cache key for tool data"""
    return f"tool:{tool_id}"


def generate_user_cache_key(user_id: int) -> str:
    """Generate cache key for user data"""
    return f"user:{user_id}"


def generate_ranking_cache_key(period: str, category_id: Optional[int] = None) -> str:
    """Generate cache key for ranking data"""
    cat_part = f":cat:{category_id}" if category_id else ""
    return f"ranking:{period}{cat_part}"


def generate_recommendation_cache_key(user_id: int, category_id: Optional[int] = None) -> str:
    """Generate cache key for recommendations"""
    cat_part = f":cat:{category_id}" if category_id else ""
    return f"recommend:{user_id}{cat_part}"

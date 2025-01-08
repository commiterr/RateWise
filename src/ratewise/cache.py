"""Cache backends for RateWise."""

import hashlib
import json
import time
import threading
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, Tuple, Callable

import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """A cache entry with value and metadata."""

    value: Any
    created_at: float
    ttl: float
    etag: Optional[str] = None
    last_accessed: Optional[float] = None

    @property
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl <= 0:
            return False
        return (time.time() - self.created_at) >= self.ttl

    @property
    def ttl_remaining(self) -> float:
        """Get remaining TTL in seconds."""
        if self.ttl <= 0:
            return float("inf")
        remaining = self.ttl - (time.time() - self.created_at)
        return max(0, remaining)


@dataclass
class CacheStats:
    """Statistics for cache operations."""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0

    @property
    def total_requests(self) -> int:
        """Total cache requests."""
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        """Cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    def reset(self) -> None:
        """Reset all statistics."""
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.evictions = 0


class CacheBackend(ABC):
    """Abstract cache backend interface."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: float = 0) -> None:
        """Set value in cache."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all entries."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        pass


class InMemoryCache(CacheBackend):
    """In-memory cache with TTL and LRU eviction."""

    def __init__(
        self,
        ttl: float = 300.0,
        max_size: int = 1000,
        namespace: str = "",
    ) -> None:
        """Initialize in-memory cache.
        
        Args:
            ttl: Default TTL in seconds (0 = no expiration).
            max_size: Maximum number of entries.
            namespace: Key prefix namespace.
        """
        self.default_ttl = ttl
        self.max_size = max_size
        self.namespace = namespace
        
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats()

    def _make_key(self, key: str) -> str:
        """Create namespaced key."""
        if self.namespace:
            return f"{self.namespace}:{key}"
        return key

    def _evict_expired(self) -> None:
        """Remove expired entries."""
        expired_keys = [
            k for k, v in self._cache.items() if v.is_expired
        ]
        for key in expired_keys:
            del self._cache[key]
            self._stats.evictions += 1

    def _evict_lru(self) -> None:
        """Evict least recently used entries if over max size."""
        while len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
            self._stats.evictions += 1

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        full_key = self._make_key(key)
        
        with self._lock:
            self._evict_expired()
            
            entry = self._cache.get(full_key)
            if entry is None:
                self._stats.misses += 1
                return None
            
            if entry.is_expired:
                del self._cache[full_key]
                self._stats.misses += 1
                return None
            
            self._cache.move_to_end(full_key)
            entry.last_accessed = time.time()
            self._stats.hits += 1
            
            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        etag: Optional[str] = None,
    ) -> None:
        """Set value in cache."""
        full_key = self._make_key(key)
        effective_ttl = ttl if ttl is not None else self.default_ttl
        
        with self._lock:
            self._evict_lru()
            
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=effective_ttl,
                etag=etag,
                last_accessed=time.time(),
            )
            
            self._cache[full_key] = entry
            self._cache.move_to_end(full_key)
            self._stats.sets += 1

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        full_key = self._make_key(key)
        
        with self._lock:
            if full_key in self._cache:
                del self._cache[full_key]
                self._stats.deletes += 1
                return True
            return False

    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._cache.clear()

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        full_key = self._make_key(key)
        
        with self._lock:
            entry = self._cache.get(full_key)
            if entry is None:
                return False
            if entry.is_expired:
                del self._cache[full_key]
                return False
            return True

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._stats

    def get_entry(self, key: str) -> Optional[CacheEntry]:
        """Get full cache entry including metadata."""
        full_key = self._make_key(key)
        
        with self._lock:
            return self._cache.get(full_key)

    @property
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


class RedisCache(CacheBackend):
    """Redis cache backend."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ttl: float = 300.0,
        namespace: str = "ratewise",
    ) -> None:
        """Initialize Redis cache.
        
        Args:
            host: Redis host.
            port: Redis port.
            db: Redis database number.
            password: Redis password.
            ttl: Default TTL in seconds.
            namespace: Key prefix namespace.
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.default_ttl = ttl
        self.namespace = namespace
        
        self._client = None
        self._stats = CacheStats()

    def _get_client(self):
        """Get or create Redis client."""
        if self._client is None:
            try:
                import redis
                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    decode_responses=True,
                )
            except ImportError:
                raise ImportError(
                    "Redis client not installed. "
                    "Install with: pip install redis"
                )
        return self._client

    def _make_key(self, key: str) -> str:
        """Create namespaced key."""
        return f"{self.namespace}:{key}"

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        full_key = self._make_key(key)
        client = self._get_client()
        
        value = client.get(full_key)
        if value is None:
            self._stats.misses += 1
            return None
        
        self._stats.hits += 1
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
    ) -> None:
        """Set value in cache."""
        full_key = self._make_key(key)
        effective_ttl = ttl if ttl is not None else self.default_ttl
        client = self._get_client()
        
        serialized = json.dumps(value) if not isinstance(value, str) else value
        
        if effective_ttl > 0:
            client.setex(full_key, int(effective_ttl), serialized)
        else:
            client.set(full_key, serialized)
        
        self._stats.sets += 1

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        full_key = self._make_key(key)
        client = self._get_client()
        
        result = client.delete(full_key)
        if result:
            self._stats.deletes += 1
        return bool(result)

    def clear(self) -> None:
        """Clear all entries in namespace."""
        client = self._get_client()
        pattern = f"{self.namespace}:*"
        
        cursor = 0
        while True:
            cursor, keys = client.scan(cursor, match=pattern, count=100)
            if keys:
                client.delete(*keys)
            if cursor == 0:
                break

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        full_key = self._make_key(key)
        client = self._get_client()
        return bool(client.exists(full_key))

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._stats


def generate_cache_key(
    method: str,
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    include_headers: Optional[list] = None,
) -> str:
    """Generate a cache key from request parameters.
    
    Args:
        method: HTTP method.
        url: Request URL.
        params: Query parameters.
        headers: Request headers.
        include_headers: Header names to include in key.
        
    Returns:
        Cache key string.
    """
    key_parts = [method.upper(), url]
    
    if params:
        sorted_params = sorted(params.items())
        key_parts.append(json.dumps(sorted_params))
    
    if headers and include_headers:
        header_parts = [
            (k, headers.get(k, ""))
            for k in sorted(include_headers)
            if k in headers
        ]
        if header_parts:
            key_parts.append(json.dumps(header_parts))
    
    key_string = "|".join(key_parts)
    return hashlib.sha256(key_string.encode()).hexdigest()


def cached(
    ttl: float = 300.0,
    cache: Optional[CacheBackend] = None,
    key_func: Optional[Callable[..., str]] = None,
) -> Callable:
    """Decorator to cache function results.
    
    Args:
        ttl: Cache TTL in seconds.
        cache: Cache backend to use.
        key_func: Function to generate cache key.
        
    Returns:
        Decorator function.
    """
    _cache = cache or InMemoryCache(ttl=ttl)

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_parts = [func.__name__]
                key_parts.extend(str(a) for a in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.sha256(
                    "|".join(key_parts).encode()
                ).hexdigest()
            
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            _cache.set(cache_key, result, ttl=ttl)
            return result
        
        wrapper.cache = _cache
        wrapper.invalidate = lambda key: _cache.delete(key)
        return wrapper

    return decorator


def parse_cache_control(header_value: Optional[str]) -> Dict[str, Any]:
    """Parse Cache-Control header.
    
    Args:
        header_value: Cache-Control header value.
        
    Returns:
        Dictionary of directives.
    """
    if not header_value:
        return {}
    
    directives: Dict[str, Any] = {}
    
    for part in header_value.split(","):
        part = part.strip()
        if "=" in part:
            key, value = part.split("=", 1)
            key = key.strip().lower()
            value = value.strip().strip('"')
            try:
                directives[key] = int(value)
            except ValueError:
                directives[key] = value
        else:
            directives[part.lower()] = True
    
    return directives

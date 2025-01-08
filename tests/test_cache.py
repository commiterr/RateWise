"""Tests for cache functionality."""

import pytest
import time
from unittest.mock import Mock, patch

from ratewise.cache import (
    CacheEntry,
    CacheStats,
    InMemoryCache,
    RedisCache,
    generate_cache_key,
    cached,
    parse_cache_control,
)


class TestCacheEntry:
    """Tests for CacheEntry."""

    def test_not_expired_when_fresh(self):
        """Test entry is not expired when fresh."""
        entry = CacheEntry(
            value="test",
            created_at=time.time(),
            ttl=60.0,
        )
        
        assert entry.is_expired is False

    def test_expired_after_ttl(self):
        """Test entry is expired after TTL."""
        entry = CacheEntry(
            value="test",
            created_at=time.time() - 120,
            ttl=60.0,
        )
        
        assert entry.is_expired is True

    def test_never_expires_with_zero_ttl(self):
        """Test entry never expires with TTL of 0."""
        entry = CacheEntry(
            value="test",
            created_at=time.time() - 1000000,
            ttl=0,
        )
        
        assert entry.is_expired is False

    def test_ttl_remaining(self):
        """Test TTL remaining calculation."""
        entry = CacheEntry(
            value="test",
            created_at=time.time(),
            ttl=60.0,
        )
        
        remaining = entry.ttl_remaining
        assert 59 <= remaining <= 60


class TestCacheStats:
    """Tests for CacheStats."""

    def test_initial_values(self):
        """Test initial statistics are zero."""
        stats = CacheStats()
        
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.hit_rate == 0.0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats(hits=7, misses=3)
        
        assert stats.hit_rate == 0.7

    def test_reset(self):
        """Test resetting statistics."""
        stats = CacheStats(hits=10, misses=5)
        stats.reset()
        
        assert stats.hits == 0
        assert stats.misses == 0


class TestInMemoryCache:
    """Tests for InMemoryCache."""

    def test_set_and_get(self):
        """Test setting and getting values."""
        cache = InMemoryCache()
        
        cache.set("key1", "value1")
        result = cache.get("key1")
        
        assert result == "value1"

    def test_get_missing_key(self):
        """Test getting missing key returns None."""
        cache = InMemoryCache()
        
        result = cache.get("nonexistent")
        
        assert result is None

    def test_delete(self):
        """Test deleting a key."""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        
        deleted = cache.delete("key1")
        
        assert deleted is True
        assert cache.get("key1") is None

    def test_exists(self):
        """Test checking if key exists."""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        
        assert cache.exists("key1") is True
        assert cache.exists("key2") is False

    def test_clear(self):
        """Test clearing all entries."""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        assert cache.size == 0

    def test_ttl_expiration(self):
        """Test TTL expiration."""
        cache = InMemoryCache(ttl=0.05)
        cache.set("key1", "value1")
        
        time.sleep(0.1)
        
        result = cache.get("key1")
        assert result is None

    def test_lru_eviction(self):
        """Test LRU eviction when max size reached."""
        cache = InMemoryCache(max_size=3)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")
        
        assert cache.get("key1") is None
        assert cache.get("key4") == "value4"

    def test_namespace(self):
        """Test key namespacing."""
        cache = InMemoryCache(namespace="myapp")
        cache.set("key1", "value1")
        
        entry = cache.get_entry("key1")
        assert entry is not None

    def test_stats_tracking(self):
        """Test statistics are tracked."""
        cache = InMemoryCache()
        
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("key2")
        
        stats = cache.get_stats()
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.sets == 1

    def test_custom_ttl_per_key(self):
        """Test setting custom TTL per key."""
        cache = InMemoryCache(ttl=60.0)
        
        cache.set("key1", "value1", ttl=0.05)
        
        time.sleep(0.1)
        
        assert cache.get("key1") is None


class TestGenerateCacheKey:
    """Tests for generate_cache_key function."""

    def test_same_inputs_same_key(self):
        """Test same inputs produce same key."""
        key1 = generate_cache_key("GET", "https://api.example.com/users")
        key2 = generate_cache_key("GET", "https://api.example.com/users")
        
        assert key1 == key2

    def test_different_methods_different_keys(self):
        """Test different methods produce different keys."""
        key1 = generate_cache_key("GET", "https://api.example.com/users")
        key2 = generate_cache_key("POST", "https://api.example.com/users")
        
        assert key1 != key2

    def test_includes_params(self):
        """Test params are included in key."""
        key1 = generate_cache_key("GET", "/users", params={"id": 1})
        key2 = generate_cache_key("GET", "/users", params={"id": 2})
        
        assert key1 != key2

    def test_includes_headers(self):
        """Test specified headers are included in key."""
        key1 = generate_cache_key(
            "GET", "/users",
            headers={"Accept-Language": "en"},
            include_headers=["Accept-Language"]
        )
        key2 = generate_cache_key(
            "GET", "/users",
            headers={"Accept-Language": "fr"},
            include_headers=["Accept-Language"]
        )
        
        assert key1 != key2


class TestCachedDecorator:
    """Tests for cached decorator."""

    def test_caches_return_value(self):
        """Test decorator caches return value."""
        call_count = 0
        
        @cached(ttl=60.0)
        def expensive_func(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result1 = expensive_func(5)
        result2 = expensive_func(5)
        
        assert result1 == 10
        assert result2 == 10
        assert call_count == 1

    def test_different_args_not_cached(self):
        """Test different args are not cached together."""
        @cached(ttl=60.0)
        def func(x):
            return x * 2
        
        result1 = func(5)
        result2 = func(10)
        
        assert result1 == 10
        assert result2 == 20


class TestParseCacheControl:
    """Tests for parse_cache_control function."""

    def test_parses_max_age(self):
        """Test parsing max-age directive."""
        result = parse_cache_control("max-age=300")
        
        assert result["max-age"] == 300

    def test_parses_no_cache(self):
        """Test parsing no-cache directive."""
        result = parse_cache_control("no-cache")
        
        assert result["no-cache"] is True

    def test_parses_multiple_directives(self):
        """Test parsing multiple directives."""
        result = parse_cache_control("max-age=300, private, no-store")
        
        assert result["max-age"] == 300
        assert result["private"] is True
        assert result["no-store"] is True

    def test_handles_empty(self):
        """Test handling empty value."""
        result = parse_cache_control("")
        
        assert result == {}

    def test_handles_none(self):
        """Test handling None value."""
        result = parse_cache_control(None)
        
        assert result == {}

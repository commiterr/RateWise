# Caching

RateWise provides pluggable cache backends to reduce API calls.

## Quick Start

```python
from ratewise import RateWiseClient
from ratewise.cache import InMemoryCache

client = RateWiseClient(
    base_url="https://api.example.com",
    cache=InMemoryCache(ttl=300),  # 5 minute TTL
)
```

## In-Memory Cache

Best for single-process applications:

```python
from ratewise.cache import InMemoryCache

cache = InMemoryCache(
    ttl=300,        # Default TTL in seconds
    max_size=1000,  # Maximum entries (LRU eviction)
    namespace="api",  # Key prefix
)
```

### Features

- **TTL-based expiration**: Entries expire after TTL
- **LRU eviction**: Oldest unused entries removed when full
- **Thread-safe**: Safe for multi-threaded applications
- **Namespacing**: Isolate cache keys with prefixes

## Redis Cache

Best for distributed applications:

```python
from ratewise.cache import RedisCache

cache = RedisCache(
    host="localhost",
    port=6379,
    db=0,
    password=None,
    ttl=300,
    namespace="ratewise",
)
```

Install Redis support:
```bash
pip install ratewise[redis]
```

## Cache Statistics

```python
stats = client.cache.get_stats()
print(f"Hits: {stats.hits}")
print(f"Misses: {stats.misses}")
print(f"Hit Rate: {stats.hit_rate:.1%}")
```

## Cache Control

### Disable cache for specific request

```python
response = client.get("/users", use_cache=False)
```

### Manual cache operations

```python
# Check if key exists
exists = cache.exists("key")

# Delete specific key
cache.delete("key")

# Clear all entries
cache.clear()
```

## Cache Key Generation

Keys are generated from:
- HTTP method
- URL
- Query parameters
- Specified headers

```python
from ratewise.cache import generate_cache_key

key = generate_cache_key(
    method="GET",
    url="https://api.example.com/users",
    params={"page": 1},
)
```

## ETag Support

RateWise supports conditional requests with ETags:

```python
# First request stores ETag
response = client.get("/resource")

# Subsequent requests send If-None-Match
# Server returns 304 Not Modified if unchanged
```

## Best Practices

1. **Cache GET requests only** - RateWise only caches GET by default
2. **Set appropriate TTL** - Balance freshness vs. performance
3. **Use namespacing** - Avoid key collisions between apps
4. **Monitor hit rate** - Aim for 70%+ hit rate

# RateWise

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Production-ready API client template with intelligent rate-limit handling, exponential backoff, circuit breaker pattern, and secure logging.**

RateWise is a resilient HTTP client library that handles the complexities of working with rate-limited APIs. It provides automatic retries with configurable backoff strategies, circuit breaker protection against cascading failures, pluggable caching, and security-conscious logging that automatically redacts sensitive credentials.

## Features

- 🔄 **Intelligent Retries** - Automatic retry with exponential backoff and jitter
- 🚦 **Rate Limit Handling** - Respects `Retry-After` headers and 429 responses
- 🔌 **Circuit Breaker** - Prevents cascading failures with configurable thresholds
- 💾 **Pluggable Caching** - In-memory and Redis cache backends with TTL support
- 🔒 **Secure Logging** - Automatic credential redaction in logs
- ⚡ **Async Support** - Full async/await support with `AsyncRateWiseClient`
- 📊 **Metrics & Stats** - Built-in request statistics and retry tracking
- 🔧 **Highly Configurable** - Customize every aspect of client behavior

## Installation

```bash
pip install ratewise
```

Or install from source:

```bash
git clone https://github.com/commiterr/RateWise.git
cd RateWise
pip install -e ".[dev]"
```

## Quick Start

```python
from ratewise import RateWiseClient

# Create a client with automatic retries
client = RateWiseClient(
    base_url="https://api.example.com",
    max_retries=5,
    timeout=30.0,
)

# Make requests - rate limits are handled automatically
try:
    response = client.get("/users/123", headers={
        "Authorization": "Bearer your-token-here"
    })
    user = response.json()
    print(f"User: {user['name']}")
    
except RateLimitExceeded as e:
    print(f"Rate limit exceeded after {e.attempts} attempts")
    
finally:
    client.close()
```

### Context Manager

```python
with RateWiseClient(base_url="https://api.example.com") as client:
    response = client.get("/users")
    users = response.json()
```

### Async Usage

```python
import asyncio
from ratewise import AsyncRateWiseClient

async def main():
    async with AsyncRateWiseClient(
        base_url="https://api.example.com",
        max_retries=3,
    ) as client:
        # Concurrent requests with automatic rate limiting
        tasks = [
            client.get(f"/users/{i}")
            for i in range(100)
        ]
        responses = await asyncio.gather(*tasks)
        print(f"Fetched {len(responses)} users")

asyncio.run(main())
```

## Configuration

### Retry Configuration

```python
from ratewise import RateWiseClient
from ratewise.retry import RetryConfig, ExponentialBackoff

client = RateWiseClient(
    base_url="https://api.example.com",
    
    # Simple configuration
    max_retries=5,
    
    # Or detailed configuration
    retry_config=RetryConfig(
        max_attempts=5,
        retry_on_status={429, 500, 502, 503, 504},
        initial_delay=1.0,
        max_delay=60.0,
        jitter=True,
        jitter_ratio=0.1,
        respect_retry_after=True,
    ),
    
    # Custom backoff strategy
    backoff_strategy=ExponentialBackoff(
        initial_delay=1.0,
        max_delay=60.0,
        multiplier=2.0,
        jitter=True,
    ),
)
```

### Circuit Breaker

```python
from ratewise.circuit_breaker import CircuitBreaker

client = RateWiseClient(
    base_url="https://api.example.com",
    circuit_breaker=CircuitBreaker(
        failure_threshold=5,      # Open after 5 failures
        success_threshold=2,      # Close after 2 successes in half-open
        recovery_timeout=60.0,    # Wait 60s before trying again
    ),
)

# Check circuit breaker state
state = client.circuit_breaker.get_state()
print(f"Circuit: {state['state']} (failures: {state['failure_count']})")
```

### Caching

```python
from ratewise.cache import InMemoryCache, RedisCache

# In-memory cache
client = RateWiseClient(
    base_url="https://api.example.com",
    cache=InMemoryCache(
        ttl=300,        # 5 minute TTL
        max_size=1000,  # Max 1000 entries
    ),
)

# Redis cache
client = RateWiseClient(
    base_url="https://api.example.com",
    cache=RedisCache(
        host="localhost",
        port=6379,
        ttl=300,
        namespace="ratewise",
    ),
)

# Get cache statistics
stats = client.cache.get_stats()
print(f"Cache hit rate: {stats.hit_rate:.1%}")
```

### Secure Logging

RateWise automatically redacts sensitive information from logs:

```python
from ratewise.logging import LogConfig

client = RateWiseClient(
    base_url="https://api.example.com",
    log_config=LogConfig(
        level="INFO",
        redact_headers=[
            "Authorization",
            "X-API-Key",
            "Cookie",
        ],
        redact_patterns=[
            r"password=\w+",
            r"token=[\w-]+",
        ],
        mask_style="partial",  # Show first 4 and last 4 chars
    ),
)
```

**Log output:**
```
2025-09-06 10:15:30 [INFO] ratewise: Request: GET https://api.example.com/users
2025-09-06 10:15:30 [DEBUG] ratewise: Headers: {"Authorization": "Bear...here"}
2025-09-06 10:15:31 [INFO] ratewise: Response: 200 (1.23s)
```

## Statistics & Monitoring

```python
# Get retry statistics
stats = client.get_retry_stats()
print(f"""
Retry Statistics:
- Total Requests: {stats['total_requests']}
- Successful: {stats['successful']}
- Failed: {stats['failed']}
- Total Retries: {stats['total_retries']}
- Average Retries: {stats['avg_retries']:.2f}
- Circuit Breaker Trips: {stats['circuit_breaker_trips']}
""")

# Get delays from last request
delays = client.get_retry_delays()
print(f"Retry delays: {delays}")
```

## Custom Retry Logic

```python
from ratewise.retry import RetryDecision

def custom_retry_logic(response, exception, attempt):
    """Custom logic to decide whether to retry."""
    
    # Always retry on 429 with Retry-After
    if response and response.status_code == 429:
        retry_after = response.headers.get("Retry-After", 60)
        return RetryDecision(should_retry=True, delay=int(retry_after))
    
    # Retry on 5xx with exponential backoff
    if response and 500 <= response.status_code < 600:
        delay = min(2 ** attempt, 60)
        return RetryDecision(should_retry=True, delay=delay)
    
    # Don't retry on 4xx (except 429)
    if response and 400 <= response.status_code < 500:
        return RetryDecision(should_retry=False)
    
    return RetryDecision(should_retry=False)
```

## API Reference

### RateWiseClient

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | str | required | Base URL for API requests |
| `max_retries` | int | 3 | Maximum retry attempts |
| `timeout` | float | 30.0 | Request timeout in seconds |
| `connect_timeout` | float | 5.0 | Connection timeout |
| `backoff_strategy` | ExponentialBackoff | None | Backoff configuration |
| `retry_config` | RetryConfig | None | Full retry configuration |
| `circuit_breaker` | CircuitBreaker | None | Circuit breaker instance |
| `cache` | CacheBackend | None | Cache backend |
| `log_config` | LogConfig | None | Logging configuration |
| `verify_ssl` | bool | True | Verify SSL certificates |
| `default_headers` | dict | None | Default headers for all requests |

### Methods

- `get(endpoint, params=None, headers=None, **kwargs)` - GET request
- `post(endpoint, json=None, data=None, headers=None, **kwargs)` - POST request
- `put(endpoint, json=None, data=None, headers=None, **kwargs)` - PUT request
- `patch(endpoint, json=None, data=None, headers=None, **kwargs)` - PATCH request
- `delete(endpoint, headers=None, **kwargs)` - DELETE request
- `get_retry_stats()` - Get retry statistics
- `get_retry_delays()` - Get delays from last request
- `get_stats()` - Get client statistics
- `close()` - Close the client

## Development

### Setup

```bash
git clone https://github.com/commiterr/RateWise.git
cd RateWise
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/ -v --cov=src/ratewise
```

### Code Style

```bash
black src/ tests/
isort src/ tests/
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [httpx](https://www.python-httpx.org/) - The HTTP client library
- [tenacity](https://tenacity.readthedocs.io/) - Retry library inspiration
- [pydantic](https://pydantic.dev/) - Data validation

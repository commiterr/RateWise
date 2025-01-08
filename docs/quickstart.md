# Quick Start Guide

This guide will help you get started with RateWise in just a few minutes.

## Installation

```bash
pip install ratewise
```

Or from source:

```bash
git clone https://github.com/commiterr/RateWise.git
cd RateWise
pip install -e .
```

## Basic Usage

### Simple Request

```python
from ratewise import RateWiseClient

# Create client
client = RateWiseClient(base_url="https://api.example.com")

# Make request
response = client.get("/users/123")
user = response.json()

# Don't forget to close
client.close()
```

### Using Context Manager

```python
with RateWiseClient(base_url="https://api.example.com") as client:
    response = client.get("/users")
    users = response.json()
```

### POST Request with JSON

```python
with RateWiseClient(base_url="https://api.example.com") as client:
    response = client.post("/users", json={
        "name": "John Doe",
        "email": "john@example.com"
    })
```

### Custom Headers

```python
with RateWiseClient(base_url="https://api.example.com") as client:
    response = client.get("/protected", headers={
        "Authorization": "Bearer your-token"
    })
```

## Error Handling

```python
from ratewise import RateWiseClient
from ratewise.exceptions import RateLimitExceeded, CircuitBreakerOpen

with RateWiseClient(base_url="https://api.example.com") as client:
    try:
        response = client.get("/users")
    except RateLimitExceeded as e:
        print(f"Rate limited after {e.attempts} attempts")
    except CircuitBreakerOpen as e:
        print("Service unavailable, circuit breaker is open")
```

## Configuration

### Retry Settings

```python
client = RateWiseClient(
    base_url="https://api.example.com",
    max_retries=5,      # Retry up to 5 times
    timeout=30.0,       # 30 second timeout
)
```

### With Caching

```python
from ratewise.cache import InMemoryCache

client = RateWiseClient(
    base_url="https://api.example.com",
    cache=InMemoryCache(ttl=300),  # 5 minute cache
)
```

## Next Steps

- [Retry Strategies](retry_strategies.md) - Configure retry behavior
- [Caching](caching.md) - Set up caching
- [Logging](logging.md) - Configure secure logging
- [API Reference](api_reference.md) - Full API documentation

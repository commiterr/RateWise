# Retry Strategies

RateWise provides flexible retry strategies for handling transient failures.

## Default Behavior

By default, RateWise:
- Retries up to 3 times
- Uses exponential backoff with jitter
- Retries on 429 (Rate Limit) and 5xx errors
- Respects `Retry-After` headers

## Configuration

### Simple Configuration

```python
from ratewise import RateWiseClient

client = RateWiseClient(
    base_url="https://api.example.com",
    max_retries=5,
)
```

### Detailed Configuration

```python
from ratewise import RateWiseClient
from ratewise.retry import RetryConfig

client = RateWiseClient(
    base_url="https://api.example.com",
    retry_config=RetryConfig(
        max_attempts=5,
        retry_on_status={429, 500, 502, 503, 504},
        initial_delay=1.0,
        max_delay=60.0,
        jitter=True,
        jitter_ratio=0.1,
        respect_retry_after=True,
    ),
)
```

## Exponential Backoff

Delays increase exponentially with each attempt:

```python
from ratewise.retry import ExponentialBackoff

backoff = ExponentialBackoff(
    initial_delay=1.0,   # First retry after 1 second
    max_delay=60.0,      # Cap at 60 seconds
    multiplier=2.0,      # Double each time
    jitter=True,         # Add randomness
    jitter_ratio=0.1,    # ±10% jitter
)

# Delays: ~1s, ~2s, ~4s, ~8s, ~16s, ...
```

## Jitter

Jitter prevents thundering herd problems by adding randomness:

- Without jitter: 1s, 2s, 4s, 8s, 16s
- With 10% jitter: 0.9-1.1s, 1.8-2.2s, 3.6-4.4s, ...

## Retry-After Header

When APIs return `Retry-After`, RateWise respects it:

```python
retry_config=RetryConfig(
    respect_retry_after=True,
    max_retry_after=300.0,  # Cap at 5 minutes
)
```

## Retry Statistics

Track retry behavior:

```python
stats = client.get_retry_stats()
print(f"Total retries: {stats['total_retries']}")
print(f"Avg retries per request: {stats['avg_retries']:.2f}")

# Get delays from last request
delays = client.get_retry_delays()
print(f"Retry delays: {delays}")
```

## Idempotent Methods

By default, only idempotent methods are retried on 5xx errors:
- GET, HEAD, OPTIONS, PUT, DELETE

POST and PATCH are not retried by default to prevent duplicate operations.

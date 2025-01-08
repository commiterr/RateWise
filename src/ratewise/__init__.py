"""
RateWise - Production-ready API client with rate-limit handling.

A resilient HTTP client library featuring:
- Exponential backoff with jitter
- Circuit breaker pattern
- Pluggable cache backends
- Secure logging with credential redaction
"""

from ratewise.client import RateWiseClient
from ratewise.async_client import AsyncRateWiseClient
from ratewise.retry import (
    RetryConfig,
    ExponentialBackoff,
    RetryDecision,
)
from ratewise.circuit_breaker import CircuitBreaker, CircuitState
from ratewise.cache import CacheBackend, InMemoryCache, RedisCache
from ratewise.exceptions import (
    RateWiseError,
    RateLimitExceeded,
    CircuitBreakerOpen,
    RequestError,
    ResponseError,
)
from ratewise.logging import LogConfig, RequestLogger

__version__ = "1.0.0"
__author__ = "RateWise Contributors"

__all__ = [
    # Clients
    "RateWiseClient",
    "AsyncRateWiseClient",
    # Retry
    "RetryConfig",
    "ExponentialBackoff",
    "RetryDecision",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitState",
    # Cache
    "CacheBackend",
    "InMemoryCache",
    "RedisCache",
    # Exceptions
    "RateWiseError",
    "RateLimitExceeded",
    "CircuitBreakerOpen",
    "RequestError",
    "ResponseError",
    # Logging
    "LogConfig",
    "RequestLogger",
]

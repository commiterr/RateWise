"""Pydantic models for RateWise configuration and responses."""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class HTTPMethod(str, Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ClientConfig(BaseModel):
    """Configuration for RateWise client."""

    base_url: str = Field(..., description="Base URL for API requests")
    timeout: float = Field(default=30.0, gt=0, description="Request timeout in seconds")
    connect_timeout: float = Field(default=5.0, gt=0, description="Connection timeout")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    max_connections: int = Field(default=100, ge=1, description="Max connection pool size")
    max_keepalive: int = Field(default=20, ge=0, description="Max keepalive connections")

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Ensure base_url doesn't end with slash."""
        return v.rstrip("/")


class RequestConfig(BaseModel):
    """Configuration for a single request."""

    method: HTTPMethod
    endpoint: str
    params: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    json_body: Optional[Dict[str, Any]] = None
    data: Optional[Any] = None
    timeout: Optional[float] = None
    allow_redirects: bool = True


class ResponseInfo(BaseModel):
    """Information about an HTTP response."""

    status_code: int
    headers: Dict[str, str] = Field(default_factory=dict)
    content_type: Optional[str] = None
    content_length: Optional[int] = None
    elapsed_seconds: float = 0.0


class RetryInfo(BaseModel):
    """Information about retry attempts."""

    attempt: int = Field(ge=1)
    max_attempts: int
    delay_seconds: float
    reason: str
    will_retry: bool


class CircuitBreakerInfo(BaseModel):
    """Information about circuit breaker state."""

    state: str
    failure_count: int
    success_count: int
    last_failure_time: Optional[float] = None
    recovery_timeout: float


class CacheInfo(BaseModel):
    """Information about cache status."""

    hit: bool
    key: str
    ttl_remaining: Optional[float] = None
    created_at: Optional[float] = None


class RequestMetrics(BaseModel):
    """Metrics for a request."""

    request_id: str
    method: str
    url: str
    status_code: Optional[int] = None
    duration_seconds: float
    retry_count: int = 0
    cache_hit: bool = False
    error: Optional[str] = None


class ClientStats(BaseModel):
    """Statistics for the client."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_retries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    circuit_breaker_trips: int = 0
    average_response_time: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

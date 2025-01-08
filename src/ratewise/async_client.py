"""Asynchronous RateWise API client."""

import asyncio
import time
import uuid
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

import httpx

from ratewise.models import ClientStats
from ratewise.retry import (
    RetryConfig,
    ExponentialBackoff,
    RetryStatistics,
    should_retry_on_status,
    parse_retry_after,
    is_idempotent_method,
)
from ratewise.circuit_breaker import CircuitBreaker
from ratewise.cache import CacheBackend, generate_cache_key
from ratewise.logging import RequestLogger, LogConfig
from ratewise.middleware import (
    MiddlewareChain,
    RequestContext,
    ResponseContext,
    create_default_middleware_chain,
)
from ratewise.exceptions import (
    RateLimitExceeded,
    CircuitBreakerOpen,
    RequestError,
    ServerError,
    TimeoutError,
    ConnectionError,
)

logger = logging.getLogger(__name__)


class AsyncRateWiseClient:
    """Async production-ready API client with rate-limit handling.
    
    Features:
    - Automatic retry with exponential backoff
    - Circuit breaker pattern
    - Pluggable cache backends
    - Secure logging with credential redaction
    - Full async/await support
    """

    def __init__(
        self,
        base_url: str,
        max_retries: int = 3,
        timeout: float = 30.0,
        connect_timeout: float = 5.0,
        backoff_strategy: Optional[ExponentialBackoff] = None,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        cache: Optional[CacheBackend] = None,
        log_config: Optional[LogConfig] = None,
        middleware: Optional[MiddlewareChain] = None,
        verify_ssl: bool = True,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        default_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize async RateWise client."""
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout = timeout
        self.connect_timeout = connect_timeout
        self.verify_ssl = verify_ssl
        
        self.backoff = backoff_strategy or ExponentialBackoff()
        self.retry_config = retry_config or RetryConfig(max_attempts=max_retries)
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.cache = cache
        self.request_logger = RequestLogger(log_config)
        self.middleware = middleware or create_default_middleware_chain()
        self.default_headers = default_headers or {}
        
        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )
        
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout, connect=connect_timeout),
            verify=verify_ssl,
            limits=limits,
        )
        
        self._stats = ClientStats()
        self._retry_stats = RetryStatistics()
        self.retry_count = 0
        self._retry_delays: List[float] = []

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return urljoin(self.base_url + "/", endpoint.lstrip("/"))

    def _merge_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Merge default headers with request headers."""
        merged = self.default_headers.copy()
        if headers:
            merged.update(headers)
        return merged

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        timeout: Optional[float] = None,
        use_cache: bool = True,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make async HTTP request with retry and circuit breaker."""
        url = self._build_url(endpoint)
        merged_headers = self._merge_headers(headers)
        request_id = str(uuid.uuid4())[:8]
        
        if self.cache and use_cache and method.upper() == "GET":
            cache_key = generate_cache_key(method, url, params, merged_headers)
            cached = self.cache.get(cache_key)
            if cached is not None:
                self._stats.cache_hits += 1
                return cached
            self._stats.cache_misses += 1
        
        context = RequestContext(
            method=method,
            url=url,
            headers=merged_headers,
            params=params,
            body=json or data,
            timeout=timeout or self.timeout,
            metadata={"request_id": request_id},
        )
        context = self.middleware.process_request(context)
        
        self.request_logger.log_request(
            method=context.method,
            url=context.url,
            headers=context.headers,
            request_id=request_id,
        )
        
        attempt = 0
        last_exception: Optional[Exception] = None
        self.retry_count = 0
        self._retry_delays.clear()
        
        while attempt < self.retry_config.max_attempts:
            attempt += 1
            self._stats.total_requests += 1
            
            if not self.circuit_breaker.allow_request():
                self._stats.circuit_breaker_trips += 1
                raise CircuitBreakerOpen(
                    message="Circuit breaker is open",
                    failure_count=self.circuit_breaker.failure_count,
                    recovery_timeout=self.circuit_breaker.recovery_timeout,
                )
            
            try:
                start_time = time.time()
                
                response = await self._client.request(
                    method=context.method,
                    url=context.url,
                    params=context.params,
                    headers=context.headers,
                    json=json,
                    data=data,
                    timeout=context.timeout,
                    **kwargs,
                )
                
                duration = time.time() - start_time
                
                if response.status_code == 429:
                    retry_after = parse_retry_after(
                        response.headers.get("Retry-After")
                    )
                    delay = retry_after if retry_after else self.backoff.calculate_delay(attempt)
                    
                    self.retry_count += 1
                    self._retry_delays.append(delay)
                    self._stats.total_retries += 1
                    
                    self.request_logger.log_retry(
                        attempt=attempt,
                        max_attempts=self.retry_config.max_attempts,
                        delay=delay,
                        reason=f"Rate limit (429)",
                        request_id=request_id,
                    )
                    
                    if attempt >= self.retry_config.max_attempts:
                        self.circuit_breaker.record_failure()
                        raise RateLimitExceeded(
                            message="Rate limit exceeded",
                            status_code=429,
                            attempts=attempt,
                            retry_after=int(delay) if retry_after else None,
                            response_body=response.text,
                            headers=dict(response.headers),
                        )
                    
                    await asyncio.sleep(delay)
                    continue
                
                if should_retry_on_status(response.status_code, self.retry_config):
                    if not is_idempotent_method(method, self.retry_config):
                        self.circuit_breaker.record_failure()
                        raise ServerError(
                            message=f"Server error: {response.status_code}",
                            status_code=response.status_code,
                            response_body=response.text,
                        )
                    
                    delay = self.backoff.calculate_delay(attempt)
                    self.retry_count += 1
                    self._retry_delays.append(delay)
                    self._stats.total_retries += 1
                    
                    if attempt >= self.retry_config.max_attempts:
                        self.circuit_breaker.record_failure()
                        raise ServerError(
                            message=f"Server error after {attempt} attempts",
                            status_code=response.status_code,
                            response_body=response.text,
                        )
                    
                    await asyncio.sleep(delay)
                    continue
                
                self.circuit_breaker.record_success()
                self._stats.successful_requests += 1
                
                response_context = ResponseContext(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    body=response.content,
                    elapsed=duration,
                )
                self.middleware.process_response(context, response_context)
                
                self.request_logger.log_response(
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    duration=duration,
                    request_id=request_id,
                )
                
                if self.cache and use_cache and method.upper() == "GET":
                    if 200 <= response.status_code < 300:
                        cache_key = generate_cache_key(method, url, params, merged_headers)
                        self.cache.set(cache_key, response)
                
                return response
                
            except httpx.TimeoutException as e:
                last_exception = e
                self.circuit_breaker.record_failure()
                self._stats.failed_requests += 1
                
                if self.retry_config.retry_on_timeout and attempt < self.retry_config.max_attempts:
                    delay = self.backoff.calculate_delay(attempt)
                    self._retry_delays.append(delay)
                    self._stats.total_retries += 1
                    await asyncio.sleep(delay)
                    continue
                
                raise TimeoutError(
                    message=str(e),
                    timeout=context.timeout,
                    url=url,
                    method=method,
                    cause=e,
                )
                
            except httpx.ConnectError as e:
                last_exception = e
                self.circuit_breaker.record_failure()
                self._stats.failed_requests += 1
                
                if self.retry_config.retry_on_connection_error and attempt < self.retry_config.max_attempts:
                    delay = self.backoff.calculate_delay(attempt)
                    self._retry_delays.append(delay)
                    self._stats.total_retries += 1
                    await asyncio.sleep(delay)
                    continue
                
                raise ConnectionError(
                    message=str(e),
                    url=url,
                    method=method,
                    cause=e,
                )
                
            except Exception as e:
                last_exception = e
                self.circuit_breaker.record_failure()
                self._stats.failed_requests += 1
                self.request_logger.log_error(e, request_id=request_id)
                raise RequestError(
                    message=str(e),
                    url=url,
                    method=method,
                    cause=e,
                )
        
        if last_exception:
            raise last_exception
        
        raise RequestError(message="Request failed", url=url, method=method)

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make async GET request."""
        return await self._make_request("GET", endpoint, params=params, headers=headers, **kwargs)

    async def post(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make async POST request."""
        return await self._make_request("POST", endpoint, json=json, data=data, headers=headers, **kwargs)

    async def put(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make async PUT request."""
        return await self._make_request("PUT", endpoint, json=json, data=data, headers=headers, **kwargs)

    async def patch(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make async PATCH request."""
        return await self._make_request("PATCH", endpoint, json=json, data=data, headers=headers, **kwargs)

    async def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make async DELETE request."""
        return await self._make_request("DELETE", endpoint, headers=headers, **kwargs)

    def get_retry_delays(self) -> List[float]:
        """Get retry delays from last request."""
        return self._retry_delays.copy()

    def get_retry_stats(self) -> Dict[str, Any]:
        """Get retry statistics."""
        return {
            "total_requests": self._stats.total_requests,
            "successful": self._stats.successful_requests,
            "failed": self._stats.failed_requests,
            "total_retries": self._stats.total_retries,
            "avg_retries": (
                self._stats.total_retries / self._stats.total_requests
                if self._stats.total_requests > 0 else 0
            ),
            "circuit_breaker_trips": self._stats.circuit_breaker_trips,
        }

    def get_stats(self) -> ClientStats:
        """Get client statistics."""
        return self._stats

    async def close(self) -> None:
        """Close the async HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncRateWiseClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

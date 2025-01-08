"""Advanced configuration example for RateWise."""

from ratewise import RateWiseClient
from ratewise.retry import RetryConfig, ExponentialBackoff
from ratewise.circuit_breaker import CircuitBreaker, CircuitState
from ratewise.cache import InMemoryCache
from ratewise.logging import LogConfig, MaskStyle


def on_circuit_state_change(old_state: CircuitState, new_state: CircuitState):
    """Callback for circuit breaker state changes."""
    print(f"Circuit breaker: {old_state.value} -> {new_state.value}")


def main():
    """Demonstrate advanced RateWise configuration."""
    
    # Create fully configured client
    client = RateWiseClient(
        base_url="https://httpbin.org",
        
        # Connection settings
        timeout=30.0,
        connect_timeout=5.0,
        verify_ssl=True,
        max_connections=100,
        max_keepalive_connections=20,
        
        # Retry configuration
        retry_config=RetryConfig(
            max_attempts=5,
            retry_on_status={429, 500, 502, 503, 504},
            initial_delay=1.0,
            max_delay=60.0,
            jitter=True,
            jitter_ratio=0.1,
            respect_retry_after=True,
            max_retry_after=300.0,
            retry_on_timeout=True,
            retry_on_connection_error=True,
        ),
        
        # Custom backoff strategy
        backoff_strategy=ExponentialBackoff(
            initial_delay=1.0,
            max_delay=60.0,
            multiplier=2.0,
            jitter=True,
            jitter_ratio=0.1,
        ),
        
        # Circuit breaker
        circuit_breaker=CircuitBreaker(
            failure_threshold=5,
            success_threshold=2,
            recovery_timeout=60.0,
            on_state_change=on_circuit_state_change,
        ),
        
        # Caching
        cache=InMemoryCache(
            ttl=300,        # 5 minute TTL
            max_size=1000,  # Max 1000 entries
            namespace="myapp",
        ),
        
        # Logging with redaction
        log_config=LogConfig(
            level="DEBUG",
            log_request_headers=True,
            log_response_headers=False,
            log_request_body=False,
            log_response_body=False,
            log_timing=True,
            redact_headers=[
                "authorization",
                "x-api-key",
                "cookie",
            ],
            redact_patterns=[
                r"password=\w+",
                r"token=[\w-]+",
                r"secret=\w+",
            ],
            redact_query_params=[
                "password",
                "api_key",
                "token",
            ],
            mask_style=MaskStyle.PARTIAL,
            partial_mask_chars=4,
        ),
        
        # Default headers
        default_headers={
            "User-Agent": "MyApp/1.0 RateWise/1.0",
            "Accept": "application/json",
        },
    )
    
    try:
        # Make request
        print("Making request with full configuration...")
        response = client.get("/get", params={"test": "value"})
        print(f"Status: {response.status_code}")
        
        # Check circuit breaker state
        cb_state = client.circuit_breaker.get_state()
        print(f"\nCircuit Breaker:")
        print(f"  State: {cb_state['state']}")
        print(f"  Failures: {cb_state['failure_count']}")
        
        # Check cache stats
        cache_stats = client.cache.get_stats()
        print(f"\nCache Statistics:")
        print(f"  Hits: {cache_stats.hits}")
        print(f"  Misses: {cache_stats.misses}")
        print(f"  Hit Rate: {cache_stats.hit_rate:.1%}")
        
        # Make same request again (should be cached)
        print("\nMaking same request (should hit cache)...")
        response = client.get("/get", params={"test": "value"})
        
        # Check cache stats again
        cache_stats = client.cache.get_stats()
        print(f"Cache hits after second request: {cache_stats.hits}")
        
        # Get retry statistics
        stats = client.get_retry_stats()
        print(f"\nRetry Statistics:")
        print(f"  Total Requests: {stats['total_requests']}")
        print(f"  Successful: {stats['successful']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Total Retries: {stats['total_retries']}")
        print(f"  Circuit Breaker Trips: {stats['circuit_breaker_trips']}")
        
    finally:
        client.close()


if __name__ == "__main__":
    main()

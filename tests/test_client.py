"""Tests for RateWise client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from ratewise import RateWiseClient, AsyncRateWiseClient
from ratewise.exceptions import RateLimitExceeded, CircuitBreakerOpen, ServerError
from ratewise.retry import RetryConfig


class TestRateWiseClient:
    """Tests for synchronous RateWiseClient."""

    def test_client_initialization(self):
        """Test client initializes with correct defaults."""
        client = RateWiseClient(base_url="https://api.example.com")
        
        assert client.base_url == "https://api.example.com"
        assert client.max_retries == 3
        assert client.timeout == 30.0
        assert client.verify_ssl is True
        
        client.close()

    def test_client_custom_config(self):
        """Test client with custom configuration."""
        client = RateWiseClient(
            base_url="https://api.test.com",
            max_retries=5,
            timeout=60.0,
            verify_ssl=False,
        )
        
        assert client.base_url == "https://api.test.com"
        assert client.max_retries == 5
        assert client.timeout == 60.0
        assert client.verify_ssl is False
        
        client.close()

    def test_context_manager(self):
        """Test client works as context manager."""
        with RateWiseClient(base_url="https://api.example.com") as client:
            assert client is not None

    @patch("httpx.Client.request")
    def test_successful_get_request(self, mock_request, mock_response_200):
        """Test successful GET request."""
        mock_request.return_value = mock_response_200
        
        with RateWiseClient(base_url="https://api.example.com") as client:
            response = client.get("/users/123")
            
            assert response.status_code == 200
            mock_request.assert_called_once()

    @patch("httpx.Client.request")
    def test_successful_post_request(self, mock_request, mock_response_200):
        """Test successful POST request."""
        mock_request.return_value = mock_response_200
        
        with RateWiseClient(base_url="https://api.example.com") as client:
            response = client.post("/users", json={"name": "Test"})
            
            assert response.status_code == 200

    @patch("httpx.Client.request")
    def test_default_headers(self, mock_request, mock_response_200):
        """Test default headers are sent."""
        mock_request.return_value = mock_response_200
        
        with RateWiseClient(
            base_url="https://api.example.com",
            default_headers={"X-Custom": "value"}
        ) as client:
            client.get("/test")
            
            call_kwargs = mock_request.call_args[1]
            assert "X-Custom" in call_kwargs["headers"]

    def test_get_stats(self):
        """Test statistics tracking."""
        with RateWiseClient(base_url="https://api.example.com") as client:
            stats = client.get_stats()
            
            assert stats.total_requests == 0
            assert stats.successful_requests == 0


class TestRetryBehavior:
    """Tests for retry behavior."""

    @patch("httpx.Client.request")
    @patch("time.sleep")
    def test_retries_on_429_with_exponential_backoff(
        self, mock_sleep, mock_request, mock_responses_429_then_200
    ):
        """Test that client retries on 429 with increasing delays.
        
        This is REQUIRED TEST #1.
        """
        mock_request.side_effect = mock_responses_429_then_200
        
        with RateWiseClient(
            base_url="https://api.example.com",
            max_retries=3,
        ) as client:
            response = client.get("/endpoint")
            
            assert response.status_code == 200
            assert client.retry_count == 2
            
            delays = client.get_retry_delays()
            assert len(delays) == 2
            assert delays[0] < delays[1]

    @patch("httpx.Client.request")
    @patch("time.sleep")
    def test_stops_after_max_retries(self, mock_sleep, mock_request, mock_response_429):
        """Test that client stops retrying after max attempts.
        
        This is REQUIRED TEST #2.
        """
        mock_request.return_value = mock_response_429
        
        with RateWiseClient(
            base_url="https://api.example.com",
            max_retries=3,
        ) as client:
            with pytest.raises(RateLimitExceeded) as exc_info:
                client.get("/endpoint")
            
            assert exc_info.value.attempts == 3
            assert "Maximum retry attempts exceeded" in str(exc_info.value)

    @patch("httpx.Client.request")
    @patch("time.sleep")
    def test_respects_retry_after_header(self, mock_sleep, mock_request):
        """Test Retry-After header is respected."""
        response_429 = Mock(spec=httpx.Response)
        response_429.status_code = 429
        response_429.headers = {"Retry-After": "5"}
        response_429.text = ""
        
        response_200 = Mock(spec=httpx.Response)
        response_200.status_code = 200
        response_200.headers = {}
        response_200.text = "{}"
        response_200.content = b"{}"
        
        mock_request.side_effect = [response_429, response_200]
        
        with RateWiseClient(base_url="https://api.example.com") as client:
            client.get("/test")
            
            mock_sleep.assert_called()
            delay = mock_sleep.call_args[0][0]
            assert delay == 5.0

    @patch("httpx.Client.request")
    @patch("time.sleep")
    def test_retries_on_5xx_errors(self, mock_sleep, mock_request):
        """Test retry on 5xx server errors."""
        response_500 = Mock(spec=httpx.Response)
        response_500.status_code = 500
        response_500.headers = {}
        response_500.text = "Server Error"
        
        response_200 = Mock(spec=httpx.Response)
        response_200.status_code = 200
        response_200.headers = {}
        response_200.text = "{}"
        response_200.content = b"{}"
        
        mock_request.side_effect = [response_500, response_200]
        
        with RateWiseClient(base_url="https://api.example.com") as client:
            response = client.get("/test")
            
            assert response.status_code == 200
            assert client.retry_count == 1


class TestCircuitBreaker:
    """Tests for circuit breaker behavior."""

    @patch("httpx.Client.request")
    @patch("time.sleep")
    def test_circuit_breaker_opens_after_failures(self, mock_sleep, mock_request):
        """Test circuit breaker opens after threshold failures."""
        mock_request.side_effect = httpx.ConnectError("Connection failed")
        
        with RateWiseClient(base_url="https://api.example.com") as client:
            client.circuit_breaker.failure_threshold = 2
            
            for _ in range(2):
                try:
                    client.get("/test")
                except Exception:
                    pass
            
            assert client.circuit_breaker.is_open()

    def test_circuit_breaker_rejects_when_open(self):
        """Test requests are rejected when circuit is open."""
        with RateWiseClient(base_url="https://api.example.com") as client:
            client.circuit_breaker._state = client.circuit_breaker._state.__class__("open")
            client.circuit_breaker._failure_count = 5
            
            with pytest.raises(CircuitBreakerOpen):
                client.circuit_breaker.allow_request()
                client.get("/test")


class TestCaching:
    """Tests for caching behavior."""

    @patch("httpx.Client.request")
    def test_cache_hit(self, mock_request, mock_response_200):
        """Test cache hit returns cached response."""
        from ratewise.cache import InMemoryCache
        
        cache = InMemoryCache(ttl=300)
        mock_request.return_value = mock_response_200
        
        with RateWiseClient(
            base_url="https://api.example.com",
            cache=cache,
        ) as client:
            client.get("/users/123")
            client.get("/users/123")
            
            stats = client.get_stats()
            assert stats.cache_hits == 1 or mock_request.call_count == 1

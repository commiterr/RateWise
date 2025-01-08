"""Pytest configuration and fixtures for RateWise tests."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx


@pytest.fixture
def mock_response_200():
    """Create a mock 200 OK response."""
    response = Mock(spec=httpx.Response)
    response.status_code = 200
    response.headers = {"Content-Type": "application/json"}
    response.text = '{"success": true}'
    response.json.return_value = {"success": True}
    response.content = b'{"success": true}'
    response.elapsed = Mock()
    response.elapsed.total_seconds.return_value = 0.1
    return response


@pytest.fixture
def mock_response_429():
    """Create a mock 429 rate limit response."""
    response = Mock(spec=httpx.Response)
    response.status_code = 429
    response.headers = {"Retry-After": "1", "Content-Type": "application/json"}
    response.text = '{"error": "rate_limit_exceeded"}'
    response.json.return_value = {"error": "rate_limit_exceeded"}
    response.content = b'{"error": "rate_limit_exceeded"}'
    return response


@pytest.fixture
def mock_response_500():
    """Create a mock 500 server error response."""
    response = Mock(spec=httpx.Response)
    response.status_code = 500
    response.headers = {"Content-Type": "application/json"}
    response.text = '{"error": "internal_server_error"}'
    response.json.return_value = {"error": "internal_server_error"}
    response.content = b'{"error": "internal_server_error"}'
    return response


@pytest.fixture
def mock_responses_429_then_200(mock_response_429, mock_response_200):
    """Create mock responses: 429, 429, 200."""
    response_429_1 = Mock(spec=httpx.Response)
    response_429_1.status_code = 429
    response_429_1.headers = {"Retry-After": "1"}
    response_429_1.text = '{"error": "rate_limit"}'
    
    response_429_2 = Mock(spec=httpx.Response)
    response_429_2.status_code = 429
    response_429_2.headers = {"Retry-After": "2"}
    response_429_2.text = '{"error": "rate_limit"}'
    
    return [response_429_1, response_429_2, mock_response_200]


@pytest.fixture
def base_url():
    """Base URL for testing."""
    return "https://api.example.com"


@pytest.fixture
def client_config():
    """Default client configuration."""
    return {
        "base_url": "https://api.example.com",
        "max_retries": 3,
        "timeout": 30.0,
    }

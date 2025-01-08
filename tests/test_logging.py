"""Tests for logging and credential redaction."""

import logging
from io import StringIO

import pytest

from ratewise import RateWiseClient
from ratewise.logging import RequestLogger, LogConfig, redact_sensitive_data


class TestCredentialRedaction:
    """Tests for credential redaction in logs."""

    def test_redacts_auth_header_in_logs(self):
        """Test that Authorization headers are redacted in logs.
        
        This is REQUIRED TEST #3.
        """
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.DEBUG)
        
        ratewise_logger = logging.getLogger("ratewise")
        ratewise_logger.addHandler(handler)
        ratewise_logger.setLevel(logging.DEBUG)
        
        logger = RequestLogger()
        
        logger.log_request(
            method="GET",
            url="https://api.example.com/users",
            headers={"Authorization": "Bearer secret-token-12345"},
            request_id="test-123",
        )
        
        log_output = log_stream.getvalue()
        
        assert "secret-token-12345" not in log_output
        
        ratewise_logger.removeHandler(handler)

    def test_redacts_api_key_header(self):
        """Test API key header redaction."""
        logger = RequestLogger()
        
        headers = {
            "X-API-Key": "super-secret-api-key-12345",
            "Content-Type": "application/json",
        }
        
        redacted = logger.redact_headers(headers)
        
        assert "super-secret-api-key-12345" not in redacted["X-API-Key"]
        assert redacted["Content-Type"] == "application/json"

    def test_redacts_bearer_token(self):
        """Test Bearer token redaction."""
        logger = RequestLogger()
        
        headers = {"Authorization": "Bearer my-secret-token"}
        redacted = logger.redact_headers(headers)
        
        assert "my-secret-token" not in redacted["Authorization"]
        assert "..." in redacted["Authorization"] or "****" in redacted["Authorization"]

    def test_redacts_basic_auth(self):
        """Test Basic auth redaction."""
        logger = RequestLogger()
        
        headers = {"Authorization": "Basic dXNlcjpwYXNzd29yZA=="}
        redacted = logger.redact_headers(headers)
        
        assert "dXNlcjpwYXNzd29yZA==" not in redacted["Authorization"]

    def test_redacts_password_in_body(self):
        """Test password redaction in request body."""
        logger = RequestLogger()
        
        body = '{"username": "user", "password": "secret123"}'
        redacted = logger.redact_body(body)
        
        assert "secret123" not in redacted

    def test_redacts_token_in_body(self):
        """Test token redaction in request body."""
        logger = RequestLogger()
        
        body = '{"token": "abc-123-def-456"}'
        redacted = logger.redact_body(body)
        
        assert "abc-123-def-456" not in redacted

    def test_redacts_sensitive_query_params(self):
        """Test sensitive query parameter redaction."""
        logger = RequestLogger()
        
        url = "https://api.example.com/auth?username=john&password=secret&api_key=12345"
        redacted = logger.redact_url(url)
        
        assert "secret" not in redacted
        assert "12345" not in redacted
        assert "username=john" in redacted

    def test_partial_masking(self):
        """Test partial masking shows first/last characters."""
        config = LogConfig(partial_mask_chars=4)
        logger = RequestLogger(config)
        
        headers = {"Authorization": "Bearer very-long-secret-token-here"}
        redacted = logger.redact_headers(headers)
        
        auth_value = redacted["Authorization"]
        assert "..." in auth_value or "****" in auth_value

    def test_redact_sensitive_data_function(self):
        """Test redact_sensitive_data utility function."""
        data = {
            "headers": {
                "Authorization": "Bearer secret",
                "Content-Type": "application/json",
            },
            "body": {"key": "value"},
        }
        
        redacted = redact_sensitive_data(data)
        
        assert "secret" not in str(redacted["headers"]["Authorization"])
        assert redacted["headers"]["Content-Type"] == "application/json"

    def test_custom_redaction_patterns(self):
        """Test custom redaction patterns."""
        config = LogConfig(
            redact_patterns=[
                r"ssn[\"\']?\s*[:=]\s*[\"\']?(\d{3}-\d{2}-\d{4})",
            ]
        )
        logger = RequestLogger(config)
        
        body = '{"ssn": "123-45-6789"}'
        redacted = logger.redact_body(body)
        
        assert "123-45-6789" not in redacted

    def test_cookie_header_redaction(self):
        """Test cookie header is redacted."""
        logger = RequestLogger()
        
        headers = {
            "Cookie": "session=abc123; auth_token=secret456",
        }
        
        redacted = logger.redact_headers(headers)
        
        assert "abc123" not in redacted["Cookie"]
        assert "secret456" not in redacted["Cookie"]


class TestLoggingOutput:
    """Tests for logging output format."""

    def test_log_request_includes_method_and_url(self):
        """Test request log includes method and URL."""
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        
        ratewise_logger = logging.getLogger("ratewise")
        ratewise_logger.addHandler(handler)
        ratewise_logger.setLevel(logging.INFO)
        
        logger = RequestLogger()
        logger.log_request(
            method="GET",
            url="https://api.example.com/test",
            request_id="req-123",
        )
        
        log_output = log_stream.getvalue()
        
        assert "GET" in log_output
        assert "api.example.com" in log_output
        
        ratewise_logger.removeHandler(handler)

    def test_log_response_includes_status(self):
        """Test response log includes status code."""
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        
        ratewise_logger = logging.getLogger("ratewise")
        ratewise_logger.addHandler(handler)
        ratewise_logger.setLevel(logging.INFO)
        
        logger = RequestLogger()
        logger.log_response(
            status_code=200,
            duration=0.5,
            request_id="req-123",
        )
        
        log_output = log_stream.getvalue()
        
        assert "200" in log_output
        
        ratewise_logger.removeHandler(handler)

    def test_log_retry_includes_attempt_info(self):
        """Test retry log includes attempt information."""
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        
        ratewise_logger = logging.getLogger("ratewise")
        ratewise_logger.addHandler(handler)
        ratewise_logger.setLevel(logging.WARNING)
        
        logger = RequestLogger()
        logger.log_retry(
            attempt=2,
            max_attempts=5,
            delay=1.5,
            reason="Rate limit",
            request_id="req-123",
        )
        
        log_output = log_stream.getvalue()
        
        assert "2" in log_output
        assert "5" in log_output
        
        ratewise_logger.removeHandler(handler)

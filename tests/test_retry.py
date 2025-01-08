"""Tests for retry logic."""

import pytest
from unittest.mock import Mock, patch
import time

from ratewise.retry import (
    ExponentialBackoff,
    RetryConfig,
    RetryDecision,
    RetryStatistics,
    should_retry_on_status,
    parse_retry_after,
    is_idempotent_method,
    create_retry_decorator,
)


class TestExponentialBackoff:
    """Tests for ExponentialBackoff."""

    def test_default_values(self):
        """Test default backoff values."""
        backoff = ExponentialBackoff()
        
        assert backoff.initial_delay == 1.0
        assert backoff.max_delay == 60.0
        assert backoff.multiplier == 2.0
        assert backoff.jitter is True

    def test_calculate_delay_increases_exponentially(self):
        """Test delay increases exponentially with attempts."""
        backoff = ExponentialBackoff(
            initial_delay=1.0,
            multiplier=2.0,
            jitter=False,
        )
        
        delay1 = backoff.calculate_delay(1)
        delay2 = backoff.calculate_delay(2)
        delay3 = backoff.calculate_delay(3)
        
        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0

    def test_delay_respects_max(self):
        """Test delay is capped at max_delay."""
        backoff = ExponentialBackoff(
            initial_delay=1.0,
            max_delay=5.0,
            multiplier=2.0,
            jitter=False,
        )
        
        delay = backoff.calculate_delay(10)
        
        assert delay == 5.0

    def test_jitter_adds_randomness(self):
        """Test jitter adds randomness to delay."""
        backoff = ExponentialBackoff(
            initial_delay=10.0,
            jitter=True,
            jitter_ratio=0.5,
        )
        
        delays = [backoff.calculate_delay(1) for _ in range(10)]
        
        assert len(set(delays)) > 1


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = RetryConfig()
        
        assert config.max_attempts == 3
        assert 429 in config.retry_on_status
        assert 500 in config.retry_on_status
        assert config.jitter is True

    def test_custom_retry_statuses(self):
        """Test custom retry status codes."""
        config = RetryConfig(
            retry_on_status={429, 503}
        )
        
        assert 429 in config.retry_on_status
        assert 503 in config.retry_on_status
        assert 500 not in config.retry_on_status


class TestShouldRetryOnStatus:
    """Tests for should_retry_on_status function."""

    def test_retries_on_429(self):
        """Test 429 triggers retry."""
        assert should_retry_on_status(429) is True

    def test_retries_on_500(self):
        """Test 500 triggers retry."""
        assert should_retry_on_status(500) is True

    def test_no_retry_on_400(self):
        """Test 400 does not trigger retry."""
        assert should_retry_on_status(400) is False

    def test_no_retry_on_200(self):
        """Test 200 does not trigger retry."""
        assert should_retry_on_status(200) is False

    def test_uses_custom_config(self):
        """Test uses custom config statuses."""
        config = RetryConfig(retry_on_status={418})
        
        assert should_retry_on_status(418, config) is True
        assert should_retry_on_status(429, config) is False


class TestParseRetryAfter:
    """Tests for parse_retry_after function."""

    def test_parses_integer_seconds(self):
        """Test parsing integer seconds."""
        result = parse_retry_after("120")
        
        assert result == 120.0

    def test_parses_float_seconds(self):
        """Test parsing float seconds."""
        result = parse_retry_after("1.5")
        
        assert result == 1.5

    def test_returns_none_for_none(self):
        """Test returns None for None input."""
        result = parse_retry_after(None)
        
        assert result is None

    def test_returns_none_for_invalid(self):
        """Test returns None for invalid input."""
        result = parse_retry_after("invalid")
        
        assert result is None


class TestIsIdempotentMethod:
    """Tests for is_idempotent_method function."""

    def test_get_is_idempotent(self):
        """Test GET is idempotent."""
        assert is_idempotent_method("GET") is True
        assert is_idempotent_method("get") is True

    def test_put_is_idempotent(self):
        """Test PUT is idempotent."""
        assert is_idempotent_method("PUT") is True

    def test_delete_is_idempotent(self):
        """Test DELETE is idempotent."""
        assert is_idempotent_method("DELETE") is True

    def test_post_is_not_idempotent(self):
        """Test POST is not idempotent."""
        assert is_idempotent_method("POST") is False

    def test_patch_is_not_idempotent(self):
        """Test PATCH is not idempotent by default."""
        assert is_idempotent_method("PATCH") is False


class TestRetryStatistics:
    """Tests for RetryStatistics."""

    def test_record_successful_attempt(self):
        """Test recording successful attempt."""
        stats = RetryStatistics()
        stats.record_attempt(success=True, delay=1.0)
        
        assert stats.total_attempts == 1
        assert stats.successful_attempts == 1
        assert stats.failed_attempts == 0

    def test_record_failed_attempt(self):
        """Test recording failed attempt."""
        stats = RetryStatistics()
        stats.record_attempt(success=False, delay=2.0, status_code=429)
        
        assert stats.total_attempts == 1
        assert stats.failed_attempts == 1
        assert stats.total_delay == 2.0
        assert 429 in stats.status_codes

    def test_average_delay(self):
        """Test average delay calculation."""
        stats = RetryStatistics()
        stats.record_attempt(success=False, delay=1.0)
        stats.record_attempt(success=False, delay=3.0)
        
        assert stats.average_delay == 2.0

    def test_reset(self):
        """Test resetting statistics."""
        stats = RetryStatistics()
        stats.record_attempt(success=True, delay=1.0)
        stats.reset()
        
        assert stats.total_attempts == 0
        assert stats.total_delay == 0.0


class TestRetryDecorator:
    """Tests for retry decorator."""

    def test_retries_on_exception(self):
        """Test decorator retries on exception."""
        call_count = 0
        
        @create_retry_decorator(RetryConfig(max_attempts=3))
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        with patch("time.sleep"):
            result = failing_func()
        
        assert result == "success"
        assert call_count == 3

    def test_gives_up_after_max_attempts(self):
        """Test decorator gives up after max attempts."""
        @create_retry_decorator(RetryConfig(max_attempts=2))
        def always_fails():
            raise ValueError("Always fails")
        
        with patch("time.sleep"):
            with pytest.raises(ValueError):
                always_fails()

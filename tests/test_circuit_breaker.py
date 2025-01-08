"""Tests for circuit breaker."""

import pytest
import time
from unittest.mock import patch

from ratewise.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    circuit_breaker,
)
from ratewise.exceptions import CircuitBreakerOpen


class TestCircuitBreaker:
    """Tests for CircuitBreaker."""

    def test_starts_closed(self):
        """Test circuit breaker starts in closed state."""
        cb = CircuitBreaker()
        
        assert cb.state == CircuitState.CLOSED
        assert cb.is_closed() is True
        assert cb.is_open() is False

    def test_opens_after_failure_threshold(self):
        """Test circuit opens after reaching failure threshold."""
        cb = CircuitBreaker(failure_threshold=3)
        
        for _ in range(3):
            cb.record_failure()
        
        assert cb.state == CircuitState.OPEN
        assert cb.is_open() is True

    def test_rejects_requests_when_open(self):
        """Test requests are rejected when circuit is open."""
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        
        assert cb.allow_request() is False

    def test_allows_requests_when_closed(self):
        """Test requests are allowed when circuit is closed."""
        cb = CircuitBreaker()
        
        assert cb.allow_request() is True

    def test_success_resets_failure_count(self):
        """Test success resets failure count."""
        cb = CircuitBreaker(failure_threshold=3)
        
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        
        assert cb.failure_count == 0
        assert cb.is_closed() is True

    def test_transitions_to_half_open_after_timeout(self):
        """Test circuit transitions to half-open after recovery timeout."""
        cb = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=0.1,
        )
        
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        
        time.sleep(0.15)
        
        cb.is_open()
        assert cb.state == CircuitState.HALF_OPEN

    def test_closes_after_success_in_half_open(self):
        """Test circuit closes after successes in half-open state."""
        cb = CircuitBreaker(
            failure_threshold=1,
            success_threshold=2,
            recovery_timeout=0.01,
        )
        
        cb.record_failure()
        time.sleep(0.02)
        cb.is_open()
        
        cb.record_success()
        cb.record_success()
        
        assert cb.state == CircuitState.CLOSED

    def test_reopens_on_failure_in_half_open(self):
        """Test circuit reopens on failure in half-open state."""
        cb = CircuitBreaker(
            failure_threshold=1,
            recovery_timeout=0.01,
        )
        
        cb.record_failure()
        time.sleep(0.02)
        cb.is_open()
        
        assert cb.state == CircuitState.HALF_OPEN
        
        cb.record_failure()
        
        assert cb.state == CircuitState.OPEN

    def test_call_method_executes_function(self):
        """Test call method executes function."""
        cb = CircuitBreaker()
        
        def my_func():
            return "result"
        
        result = cb.call(my_func)
        
        assert result == "result"

    def test_call_method_raises_when_open(self):
        """Test call method raises when circuit is open."""
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        
        def my_func():
            return "result"
        
        with pytest.raises(CircuitBreakerOpen):
            cb.call(my_func)

    def test_call_method_catches_exceptions(self):
        """Test call method records failure on exception."""
        cb = CircuitBreaker(failure_threshold=2)
        
        def failing_func():
            raise ValueError("error")
        
        with pytest.raises(ValueError):
            cb.call(failing_func)
        
        assert cb.failure_count == 1

    def test_reset(self):
        """Test reset returns to closed state."""
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        
        cb.reset()
        
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_get_state(self):
        """Test get_state returns correct info."""
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        
        state = cb.get_state()
        
        assert state["state"] == "closed"
        assert state["failure_count"] == 1

    def test_metrics_tracking(self):
        """Test metrics are tracked correctly."""
        cb = CircuitBreaker()
        
        cb.record_success()
        cb.record_success()
        cb.record_failure()
        
        assert cb.metrics.total_calls == 3
        assert cb.metrics.successful_calls == 2
        assert cb.metrics.failed_calls == 1

    def test_state_change_callback(self):
        """Test state change callback is called."""
        states = []
        
        def on_change(old, new):
            states.append((old, new))
        
        cb = CircuitBreaker(
            failure_threshold=1,
            on_state_change=on_change,
        )
        
        cb.record_failure()
        
        assert len(states) == 1
        assert states[0] == (CircuitState.CLOSED, CircuitState.OPEN)

    def test_excluded_exceptions(self):
        """Test excluded exceptions don't count as failures."""
        cb = CircuitBreaker(
            failure_threshold=1,
            excluded_exceptions=(ValueError,),
        )
        
        cb.record_failure(ValueError("excluded"))
        
        assert cb.failure_count == 0
        assert cb.is_closed() is True


class TestCircuitBreakerDecorator:
    """Tests for circuit_breaker decorator."""

    def test_decorator_wraps_function(self):
        """Test decorator wraps function correctly."""
        @circuit_breaker(failure_threshold=3)
        def my_func():
            return "result"
        
        result = my_func()
        
        assert result == "result"

    def test_decorator_opens_circuit(self):
        """Test decorated function opens circuit after failures."""
        @circuit_breaker(failure_threshold=2)
        def failing_func():
            raise ValueError("error")
        
        for _ in range(2):
            try:
                failing_func()
            except ValueError:
                pass
        
        with pytest.raises(CircuitBreakerOpen):
            failing_func()

    def test_decorator_exposes_circuit_breaker(self):
        """Test decorator exposes circuit breaker instance."""
        @circuit_breaker()
        def my_func():
            return "result"
        
        assert hasattr(my_func, "circuit_breaker")
        assert isinstance(my_func.circuit_breaker, CircuitBreaker)

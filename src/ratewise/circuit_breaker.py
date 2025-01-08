"""Circuit breaker pattern implementation for RateWise."""

import time
import threading
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Any, List

from ratewise.exceptions import CircuitBreakerOpen

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    success_threshold: int = 2
    recovery_timeout: float = 60.0
    expected_exceptions: tuple = field(default_factory=lambda: (Exception,))
    excluded_exceptions: tuple = field(default_factory=tuple)


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state_transitions: int = 0

    def reset(self) -> None:
        """Reset metrics."""
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.rejected_calls = 0


class CircuitBreaker:
    """Circuit breaker implementation.
    
    The circuit breaker has three states:
    - CLOSED: Normal operation, requests are allowed.
    - OPEN: Requests are blocked after failure threshold is reached.
    - HALF_OPEN: Allows limited requests to test if service has recovered.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        recovery_timeout: float = 60.0,
        expected_exceptions: Optional[tuple] = None,
        excluded_exceptions: Optional[tuple] = None,
        on_state_change: Optional[Callable[[CircuitState, CircuitState], None]] = None,
    ) -> None:
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit.
            success_threshold: Number of successes in half-open before closing.
            recovery_timeout: Seconds to wait before transitioning to half-open.
            expected_exceptions: Exceptions that trigger failure counting.
            excluded_exceptions: Exceptions that don't trigger failure counting.
            on_state_change: Callback for state changes.
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions or (Exception,)
        self.excluded_exceptions = excluded_exceptions or ()
        self.on_state_change = on_state_change

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = threading.RLock()
        self._metrics = CircuitBreakerMetrics()
        self._state_change_listeners: List[Callable] = []

    @property
    def state(self) -> CircuitState:
        """Get current state."""
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count

    @property
    def metrics(self) -> CircuitBreakerMetrics:
        """Get metrics."""
        return self._metrics

    def is_open(self) -> bool:
        """Check if circuit is open."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_recovery():
                    self._transition_to(CircuitState.HALF_OPEN)
                    return False
                return True
            return False

    def is_closed(self) -> bool:
        """Check if circuit is closed."""
        return self._state == CircuitState.CLOSED

    def is_half_open(self) -> bool:
        """Check if circuit is half-open."""
        return self._state == CircuitState.HALF_OPEN

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._last_failure_time is None:
            return True
        return (time.time() - self._last_failure_time) >= self.recovery_timeout

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        old_state = self._state
        if old_state == new_state:
            return

        self._state = new_state
        self._metrics.state_transitions += 1

        logger.info(
            f"Circuit breaker state transition: {old_state.value} -> {new_state.value}"
        )

        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0

        if new_state == CircuitState.HALF_OPEN:
            self._success_count = 0

        if self.on_state_change:
            self.on_state_change(old_state, new_state)

        for listener in self._state_change_listeners:
            try:
                listener(old_state, new_state)
            except Exception as e:
                logger.error(f"Error in state change listener: {e}")

    def record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            self._metrics.total_calls += 1
            self._metrics.successful_calls += 1

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0

    def record_failure(self, exception: Optional[Exception] = None) -> None:
        """Record a failed call."""
        with self._lock:
            if exception is not None:
                if isinstance(exception, self.excluded_exceptions):
                    return
                if not isinstance(exception, self.expected_exceptions):
                    return

            self._metrics.total_calls += 1
            self._metrics.failed_calls += 1
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._transition_to(CircuitState.OPEN)

    def allow_request(self) -> bool:
        """Check if a request is allowed.
        
        Returns:
            True if request is allowed, False if circuit is open.
        """
        with self._lock:
            if self.is_open():
                self._metrics.rejected_calls += 1
                return False
            return True

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute a function through the circuit breaker.
        
        Args:
            func: The function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.
            
        Returns:
            The function result.
            
        Raises:
            CircuitBreakerOpen: If circuit is open.
        """
        if not self.allow_request():
            raise CircuitBreakerOpen(
                message="Circuit breaker is open",
                failure_count=self._failure_count,
                recovery_timeout=self.recovery_timeout,
            )

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(e)
            raise

    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None

    def get_state(self) -> dict:
        """Get current state as dictionary."""
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "recovery_timeout": self.recovery_timeout,
        }

    def add_state_change_listener(
        self,
        listener: Callable[[CircuitState, CircuitState], None]
    ) -> None:
        """Add a listener for state changes."""
        self._state_change_listeners.append(listener)

    def remove_state_change_listener(
        self,
        listener: Callable[[CircuitState, CircuitState], None]
    ) -> None:
        """Remove a state change listener."""
        self._state_change_listeners.remove(listener)


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exceptions: Optional[tuple] = None,
) -> Callable:
    """Decorator to apply circuit breaker to a function.
    
    Args:
        failure_threshold: Number of failures before opening.
        recovery_timeout: Seconds before half-open.
        expected_exceptions: Exceptions to count as failures.
        
    Returns:
        Decorator function.
    """
    cb = CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        expected_exceptions=expected_exceptions,
    )

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return cb.call(func, *args, **kwargs)
        
        wrapper.circuit_breaker = cb
        return wrapper

    return decorator

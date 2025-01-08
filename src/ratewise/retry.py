"""Retry logic with exponential backoff for RateWise."""

import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Any, List, Set
from functools import wraps

from tenacity import (
    retry,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
    wait_random_exponential,
    retry_if_exception_type,
    retry_if_result,
    before_sleep_log,
    after_log,
    RetryCallState,
)
import logging

logger = logging.getLogger(__name__)


class BackoffStrategy(str, Enum):
    """Backoff strategy types."""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    CONSTANT = "constant"
    FIBONACCI = "fibonacci"


@dataclass
class RetryDecision:
    """Decision on whether to retry a request."""
    should_retry: bool
    delay: float = 0.0
    reason: str = ""


@dataclass
class ExponentialBackoff:
    """Exponential backoff configuration with optional jitter."""

    initial_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter: bool = True
    jitter_ratio: float = 0.1

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number.
        
        Args:
            attempt: The attempt number (1-indexed).
            
        Returns:
            Delay in seconds.
        """
        delay = min(
            self.initial_delay * (self.multiplier ** (attempt - 1)),
            self.max_delay
        )
        
        if self.jitter:
            jitter_range = delay * self.jitter_ratio
            delay += random.uniform(-jitter_range, jitter_range)
            delay = max(0, delay)
        
        return delay


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    retry_on_status: Set[int] = field(
        default_factory=lambda: {429, 500, 502, 503, 504}
    )
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    initial_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True
    jitter_ratio: float = 0.1
    respect_retry_after: bool = True
    max_retry_after: float = 300.0
    retry_on_timeout: bool = True
    retry_on_connection_error: bool = True
    idempotent_methods: Set[str] = field(
        default_factory=lambda: {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"}
    )
    
    def get_backoff(self) -> ExponentialBackoff:
        """Get backoff configuration."""
        return ExponentialBackoff(
            initial_delay=self.initial_delay,
            max_delay=self.max_delay,
            jitter=self.jitter,
            jitter_ratio=self.jitter_ratio,
        )


def should_retry_on_status(status_code: int, config: Optional[RetryConfig] = None) -> bool:
    """Check if a status code should trigger a retry.
    
    Args:
        status_code: HTTP status code.
        config: Optional retry configuration.
        
    Returns:
        True if should retry.
    """
    if config is None:
        retry_statuses = {429, 500, 502, 503, 504}
    else:
        retry_statuses = config.retry_on_status
    
    return status_code in retry_statuses


def parse_retry_after(header_value: Optional[str]) -> Optional[float]:
    """Parse Retry-After header value.
    
    Args:
        header_value: The header value (seconds or HTTP date).
        
    Returns:
        Delay in seconds, or None if not parseable.
    """
    if header_value is None:
        return None
    
    try:
        return float(header_value)
    except ValueError:
        pass
    
    try:
        from email.utils import parsedate_to_datetime
        retry_date = parsedate_to_datetime(header_value)
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        delta = (retry_date - now).total_seconds()
        return max(0, delta)
    except (ValueError, TypeError):
        pass
    
    return None


@dataclass
class RetryStatistics:
    """Statistics about retry behavior."""

    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    total_delay: float = 0.0
    delays: List[float] = field(default_factory=list)
    status_codes: List[int] = field(default_factory=list)
    
    def record_attempt(
        self,
        success: bool,
        delay: float = 0.0,
        status_code: Optional[int] = None
    ) -> None:
        """Record a retry attempt."""
        self.total_attempts += 1
        if success:
            self.successful_attempts += 1
        else:
            self.failed_attempts += 1
        
        if delay > 0:
            self.delays.append(delay)
            self.total_delay += delay
        
        if status_code is not None:
            self.status_codes.append(status_code)
    
    @property
    def average_delay(self) -> float:
        """Calculate average delay."""
        if not self.delays:
            return 0.0
        return sum(self.delays) / len(self.delays)
    
    def reset(self) -> None:
        """Reset statistics."""
        self.total_attempts = 0
        self.successful_attempts = 0
        self.failed_attempts = 0
        self.total_delay = 0.0
        self.delays.clear()
        self.status_codes.clear()


class RetryCallback:
    """Callbacks for retry events."""

    def __init__(
        self,
        before_retry: Optional[Callable[[int, float, Any], None]] = None,
        after_retry: Optional[Callable[[int, bool, Any], None]] = None,
        on_give_up: Optional[Callable[[int, Any], None]] = None,
    ) -> None:
        self.before_retry = before_retry
        self.after_retry = after_retry
        self.on_give_up = on_give_up


def create_retry_decorator(
    config: Optional[RetryConfig] = None,
    callbacks: Optional[RetryCallback] = None,
):
    """Create a retry decorator with the given configuration.
    
    Args:
        config: Retry configuration.
        callbacks: Optional callbacks for retry events.
        
    Returns:
        A decorator function.
    """
    if config is None:
        config = RetryConfig()
    
    backoff = config.get_backoff()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            last_exception = None
            stats = RetryStatistics()
            
            while attempt < config.max_attempts:
                attempt += 1
                
                try:
                    result = func(*args, **kwargs)
                    stats.record_attempt(success=True)
                    return result
                    
                except Exception as e:
                    last_exception = e
                    stats.record_attempt(success=False)
                    
                    if attempt >= config.max_attempts:
                        if callbacks and callbacks.on_give_up:
                            callbacks.on_give_up(attempt, e)
                        raise
                    
                    delay = backoff.calculate_delay(attempt)
                    
                    if callbacks and callbacks.before_retry:
                        callbacks.before_retry(attempt, delay, e)
                    
                    logger.warning(
                        f"Retry attempt {attempt}/{config.max_attempts} "
                        f"after {delay:.2f}s delay"
                    )
                    
                    time.sleep(delay)
                    
                    if callbacks and callbacks.after_retry:
                        callbacks.after_retry(attempt, False, e)
            
            raise last_exception
        
        return wrapper
    
    return decorator


def is_idempotent_method(method: str, config: Optional[RetryConfig] = None) -> bool:
    """Check if HTTP method is idempotent.
    
    Args:
        method: HTTP method.
        config: Optional retry configuration.
        
    Returns:
        True if method is idempotent.
    """
    if config is None:
        idempotent = {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"}
    else:
        idempotent = config.idempotent_methods
    
    return method.upper() in idempotent

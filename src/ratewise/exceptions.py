"""Custom exceptions for RateWise."""

from typing import Optional, Any


class RateWiseError(Exception):
    """Base exception for all RateWise errors."""

    def __init__(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.message = message
        super().__init__(message, *args, **kwargs)


class RequestError(RateWiseError):
    """Raised when a request fails to be sent."""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        method: Optional[str] = None,
        cause: Optional[Exception] = None,
    ) -> None:
        self.url = url
        self.method = method
        self.cause = cause
        super().__init__(message)


class ResponseError(RateWiseError):
    """Raised when a response indicates an error."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_body: Optional[str] = None,
        headers: Optional[dict] = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body
        self.headers = headers or {}
        super().__init__(message)


class RateLimitExceeded(ResponseError):
    """Raised when rate limit is exceeded and retries are exhausted."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        status_code: int = 429,
        attempts: int = 0,
        retry_after: Optional[int] = None,
        response_body: Optional[str] = None,
        headers: Optional[dict] = None,
    ) -> None:
        self.attempts = attempts
        self.retry_after = retry_after
        super().__init__(
            message=f"{message}. Maximum retry attempts exceeded after {attempts} attempts",
            status_code=status_code,
            response_body=response_body,
            headers=headers,
        )


class CircuitBreakerOpen(RateWiseError):
    """Raised when circuit breaker is open and requests are blocked."""

    def __init__(
        self,
        message: str = "Circuit breaker is open",
        failure_count: int = 0,
        recovery_timeout: Optional[float] = None,
    ) -> None:
        self.failure_count = failure_count
        self.recovery_timeout = recovery_timeout
        super().__init__(message)


class TimeoutError(RequestError):
    """Raised when a request times out."""

    def __init__(
        self,
        message: str = "Request timed out",
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        self.timeout = timeout
        super().__init__(message, **kwargs)


class ConnectionError(RequestError):
    """Raised when connection to the server fails."""

    pass


class SSLError(RequestError):
    """Raised when SSL/TLS verification fails."""

    pass


class AuthenticationError(ResponseError):
    """Raised when authentication fails (401)."""

    def __init__(
        self,
        message: str = "Authentication failed",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, status_code=401, **kwargs)


class AuthorizationError(ResponseError):
    """Raised when authorization fails (403)."""

    def __init__(
        self,
        message: str = "Authorization failed",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, status_code=403, **kwargs)


class NotFoundError(ResponseError):
    """Raised when resource is not found (404)."""

    def __init__(
        self,
        message: str = "Resource not found",
        **kwargs: Any,
    ) -> None:
        super().__init__(message, status_code=404, **kwargs)


class ServerError(ResponseError):
    """Raised when server returns 5xx error."""

    pass


class RetryExhausted(RateWiseError):
    """Raised when all retry attempts are exhausted."""

    def __init__(
        self,
        message: str = "All retry attempts exhausted",
        attempts: int = 0,
        last_exception: Optional[Exception] = None,
    ) -> None:
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(message)

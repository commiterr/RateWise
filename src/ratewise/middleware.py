"""Middleware/interceptor pattern for RateWise."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class RequestContext:
    """Context for a request being processed."""

    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    params: Optional[Dict[str, Any]] = None
    body: Optional[Any] = None
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: float = 0.0

    def __post_init__(self):
        if self.start_time == 0.0:
            self.start_time = time.time()


@dataclass
class ResponseContext:
    """Context for a response being processed."""

    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None
    elapsed: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Middleware(ABC):
    """Base middleware interface."""

    @abstractmethod
    def process_request(self, context: RequestContext) -> RequestContext:
        """Process request before sending.
        
        Args:
            context: Request context.
            
        Returns:
            Modified request context.
        """
        pass

    @abstractmethod
    def process_response(
        self,
        request: RequestContext,
        response: ResponseContext,
    ) -> ResponseContext:
        """Process response after receiving.
        
        Args:
            request: Original request context.
            response: Response context.
            
        Returns:
            Modified response context.
        """
        pass

    def process_error(
        self,
        request: RequestContext,
        error: Exception,
    ) -> None:
        """Process error.
        
        Args:
            request: Original request context.
            error: The exception.
        """
        pass


class MiddlewareChain:
    """Chain of middleware processors."""

    def __init__(self) -> None:
        self._middleware: List[Middleware] = []

    def add(self, middleware: Middleware) -> "MiddlewareChain":
        """Add middleware to chain."""
        self._middleware.append(middleware)
        return self

    def remove(self, middleware: Middleware) -> bool:
        """Remove middleware from chain."""
        try:
            self._middleware.remove(middleware)
            return True
        except ValueError:
            return False

    def clear(self) -> None:
        """Clear all middleware."""
        self._middleware.clear()

    def process_request(self, context: RequestContext) -> RequestContext:
        """Process request through all middleware."""
        for mw in self._middleware:
            context = mw.process_request(context)
        return context

    def process_response(
        self,
        request: RequestContext,
        response: ResponseContext,
    ) -> ResponseContext:
        """Process response through all middleware (reverse order)."""
        for mw in reversed(self._middleware):
            response = mw.process_response(request, response)
        return response

    def process_error(
        self,
        request: RequestContext,
        error: Exception,
    ) -> None:
        """Process error through all middleware."""
        for mw in reversed(self._middleware):
            mw.process_error(request, error)


class LoggingMiddleware(Middleware):
    """Middleware for request/response logging."""

    def __init__(self, log_level: int = logging.INFO) -> None:
        self.log_level = log_level

    def process_request(self, context: RequestContext) -> RequestContext:
        """Log request."""
        logger.log(
            self.log_level,
            f"Request: {context.method} {context.url}",
        )
        return context

    def process_response(
        self,
        request: RequestContext,
        response: ResponseContext,
    ) -> ResponseContext:
        """Log response."""
        logger.log(
            self.log_level,
            f"Response: {response.status_code} ({response.elapsed:.3f}s)",
        )
        return response

    def process_error(
        self,
        request: RequestContext,
        error: Exception,
    ) -> None:
        """Log error."""
        logger.error(f"Request error: {error}")


class TimingMiddleware(Middleware):
    """Middleware for request timing."""

    def process_request(self, context: RequestContext) -> RequestContext:
        """Record start time."""
        context.metadata["timing_start"] = time.time()
        return context

    def process_response(
        self,
        request: RequestContext,
        response: ResponseContext,
    ) -> ResponseContext:
        """Calculate elapsed time."""
        start = request.metadata.get("timing_start", request.start_time)
        response.elapsed = time.time() - start
        return response


class HeaderMiddleware(Middleware):
    """Middleware for adding default headers."""

    def __init__(self, headers: Optional[Dict[str, str]] = None) -> None:
        self.default_headers = headers or {}

    def process_request(self, context: RequestContext) -> RequestContext:
        """Add default headers."""
        for key, value in self.default_headers.items():
            if key not in context.headers:
                context.headers[key] = value
        return context

    def process_response(
        self,
        request: RequestContext,
        response: ResponseContext,
    ) -> ResponseContext:
        """Pass through response."""
        return response


class UserAgentMiddleware(Middleware):
    """Middleware for setting User-Agent header."""

    def __init__(self, user_agent: str = "RateWise/1.0") -> None:
        self.user_agent = user_agent

    def process_request(self, context: RequestContext) -> RequestContext:
        """Set User-Agent header."""
        if "User-Agent" not in context.headers:
            context.headers["User-Agent"] = self.user_agent
        return context

    def process_response(
        self,
        request: RequestContext,
        response: ResponseContext,
    ) -> ResponseContext:
        """Pass through response."""
        return response


class RetryMetadataMiddleware(Middleware):
    """Middleware for tracking retry metadata."""

    def process_request(self, context: RequestContext) -> RequestContext:
        """Initialize retry metadata."""
        if "retry_count" not in context.metadata:
            context.metadata["retry_count"] = 0
        return context

    def process_response(
        self,
        request: RequestContext,
        response: ResponseContext,
    ) -> ResponseContext:
        """Add retry info to response."""
        response.metadata["retry_count"] = request.metadata.get("retry_count", 0)
        return response


class ContentTypeMiddleware(Middleware):
    """Middleware for content type handling."""

    def __init__(self, default_content_type: str = "application/json") -> None:
        self.default_content_type = default_content_type

    def process_request(self, context: RequestContext) -> RequestContext:
        """Set Content-Type for requests with body."""
        if context.body is not None and "Content-Type" not in context.headers:
            context.headers["Content-Type"] = self.default_content_type
        return context

    def process_response(
        self,
        request: RequestContext,
        response: ResponseContext,
    ) -> ResponseContext:
        """Detect response content type."""
        content_type = response.headers.get("Content-Type", "")
        response.metadata["content_type"] = content_type
        response.metadata["is_json"] = "application/json" in content_type
        return response


def create_default_middleware_chain() -> MiddlewareChain:
    """Create a middleware chain with default middleware."""
    chain = MiddlewareChain()
    chain.add(TimingMiddleware())
    chain.add(UserAgentMiddleware())
    chain.add(ContentTypeMiddleware())
    chain.add(LoggingMiddleware())
    return chain

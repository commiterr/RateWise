"""Secure logging with credential redaction for RateWise."""

import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Pattern
from enum import Enum


class MaskStyle(str, Enum):
    """Masking styles for sensitive data."""
    FULL = "full"
    PARTIAL = "partial"
    HASH = "hash"


@dataclass
class LogConfig:
    """Configuration for logging behavior."""

    level: str = "INFO"
    log_request_headers: bool = True
    log_response_headers: bool = False
    log_request_body: bool = False
    log_response_body: bool = False
    log_timing: bool = True
    redact_headers: List[str] = field(
        default_factory=lambda: [
            "authorization",
            "x-api-key",
            "api-key",
            "apikey",
            "x-auth-token",
            "cookie",
            "set-cookie",
            "x-csrf-token",
        ]
    )
    redact_patterns: List[str] = field(
        default_factory=lambda: [
            r"password[\"\']?\s*[:=]\s*[\"\']?([^\s\"\'&]+)",
            r"token[\"\']?\s*[:=]\s*[\"\']?([^\s\"\'&]+)",
            r"secret[\"\']?\s*[:=]\s*[\"\']?([^\s\"\'&]+)",
            r"api_?key[\"\']?\s*[:=]\s*[\"\']?([^\s\"\'&]+)",
            r"Bearer\s+([^\s]+)",
            r"Basic\s+([^\s]+)",
        ]
    )
    redact_query_params: List[str] = field(
        default_factory=lambda: [
            "password",
            "token",
            "secret",
            "api_key",
            "apikey",
            "access_token",
        ]
    )
    mask_style: MaskStyle = MaskStyle.PARTIAL
    partial_mask_chars: int = 4


class RequestLogger:
    """Secure request/response logger with credential redaction."""

    REDACTION_PLACEHOLDER = "***REDACTED***"

    def __init__(self, config: Optional[LogConfig] = None) -> None:
        """Initialize request logger.
        
        Args:
            config: Logging configuration.
        """
        self.config = config or LogConfig()
        self.logger = logging.getLogger("ratewise")
        
        self._compiled_patterns: List[Pattern] = []
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for redaction."""
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.redact_patterns
        ]

    def _mask_value(self, value: str) -> str:
        """Mask a sensitive value.
        
        Args:
            value: The value to mask.
            
        Returns:
            Masked value.
        """
        if self.config.mask_style == MaskStyle.FULL:
            return self.REDACTION_PLACEHOLDER
        
        elif self.config.mask_style == MaskStyle.PARTIAL:
            chars = self.config.partial_mask_chars
            if len(value) <= chars * 2:
                return "****"
            return f"{value[:chars]}...{value[-chars:]}"
        
        elif self.config.mask_style == MaskStyle.HASH:
            import hashlib
            return f"[HASH:{hashlib.sha256(value.encode()).hexdigest()[:8]}]"
        
        return self.REDACTION_PLACEHOLDER

    def redact_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Redact sensitive headers.
        
        Args:
            headers: Request/response headers.
            
        Returns:
            Headers with sensitive values redacted.
        """
        redacted = {}
        redact_set = {h.lower() for h in self.config.redact_headers}
        
        for key, value in headers.items():
            if key.lower() in redact_set:
                redacted[key] = self._mask_value(value)
            else:
                redacted[key] = self._redact_value(value)
        
        return redacted

    def _redact_value(self, value: str) -> str:
        """Redact sensitive data from a string value.
        
        Args:
            value: The string to redact.
            
        Returns:
            Redacted string.
        """
        result = value
        
        for pattern in self._compiled_patterns:
            def replacer(match):
                full_match = match.group(0)
                sensitive_part = match.group(1) if match.lastindex else full_match
                masked = self._mask_value(sensitive_part)
                return full_match.replace(sensitive_part, masked)
            
            result = pattern.sub(replacer, result)
        
        return result

    def redact_body(self, body: str) -> str:
        """Redact sensitive data from request/response body.
        
        Args:
            body: The body content.
            
        Returns:
            Redacted body.
        """
        return self._redact_value(body)

    def redact_url(self, url: str) -> str:
        """Redact sensitive query parameters from URL.
        
        Args:
            url: The request URL.
            
        Returns:
            URL with sensitive params redacted.
        """
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        parsed = urlparse(url)
        if not parsed.query:
            return url
        
        params = parse_qs(parsed.query, keep_blank_values=True)
        redact_set = {p.lower() for p in self.config.redact_query_params}
        
        redacted_params = {}
        for key, values in params.items():
            if key.lower() in redact_set:
                redacted_params[key] = [self._mask_value(v) for v in values]
            else:
                redacted_params[key] = values
        
        new_query = urlencode(redacted_params, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    def log_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> str:
        """Log an HTTP request.
        
        Args:
            method: HTTP method.
            url: Request URL.
            headers: Request headers.
            body: Request body.
            request_id: Optional request ID.
            
        Returns:
            Request ID for correlation.
        """
        request_id = request_id or str(uuid.uuid4())[:8]
        redacted_url = self.redact_url(url)
        
        self.logger.info(
            f"Request started: {method} {redacted_url}",
            extra={
                "request_id": request_id,
                "method": method,
                "url": redacted_url,
            }
        )
        
        if self.config.log_request_headers and headers:
            redacted_headers = self.redact_headers(headers)
            self.logger.debug(
                f"Request headers: {redacted_headers}",
                extra={"request_id": request_id, "headers": redacted_headers}
            )
        
        if self.config.log_request_body and body:
            redacted_body = self.redact_body(body)
            self.logger.debug(
                f"Request body: {redacted_body}",
                extra={"request_id": request_id}
            )
        
        return request_id

    def log_response(
        self,
        status_code: int,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        duration: Optional[float] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Log an HTTP response.
        
        Args:
            status_code: HTTP status code.
            headers: Response headers.
            body: Response body.
            duration: Request duration in seconds.
            request_id: Request ID for correlation.
        """
        extra = {
            "request_id": request_id,
            "status_code": status_code,
        }
        
        if self.config.log_timing and duration is not None:
            extra["duration_seconds"] = duration
        
        log_level = logging.INFO if status_code < 400 else logging.WARNING
        
        message = f"Response: {status_code}"
        if duration is not None:
            message += f" ({duration:.3f}s)"
        
        self.logger.log(log_level, message, extra=extra)
        
        if self.config.log_response_headers and headers:
            redacted_headers = self.redact_headers(headers)
            self.logger.debug(
                f"Response headers: {redacted_headers}",
                extra={"request_id": request_id}
            )
        
        if self.config.log_response_body and body:
            redacted_body = self.redact_body(body)
            self.logger.debug(
                f"Response body: {redacted_body}",
                extra={"request_id": request_id}
            )

    def log_error(
        self,
        error: Exception,
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an error.
        
        Args:
            error: The exception.
            request_id: Request ID for correlation.
            context: Additional context.
        """
        extra = {
            "request_id": request_id,
            "error_type": type(error).__name__,
        }
        if context:
            extra.update(context)
        
        self.logger.error(
            f"Request error: {error}",
            extra=extra,
            exc_info=True,
        )

    def log_retry(
        self,
        attempt: int,
        max_attempts: int,
        delay: float,
        reason: str,
        request_id: Optional[str] = None,
    ) -> None:
        """Log a retry attempt.
        
        Args:
            attempt: Current attempt number.
            max_attempts: Maximum attempts.
            delay: Delay before retry in seconds.
            reason: Reason for retry.
            request_id: Request ID for correlation.
        """
        self.logger.warning(
            f"Retry {attempt}/{max_attempts} after {delay:.2f}s: {reason}",
            extra={
                "request_id": request_id,
                "attempt": attempt,
                "max_attempts": max_attempts,
                "delay_seconds": delay,
                "reason": reason,
            }
        )

    def log_circuit_breaker_event(
        self,
        event: str,
        state: str,
        failure_count: Optional[int] = None,
    ) -> None:
        """Log a circuit breaker event.
        
        Args:
            event: Event type (opened, closed, half_open).
            state: Current state.
            failure_count: Number of failures.
        """
        self.logger.warning(
            f"Circuit breaker {event}: state={state}",
            extra={
                "event": event,
                "state": state,
                "failure_count": failure_count,
            }
        )


def redact_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Redact sensitive data from a dictionary.
    
    Args:
        data: Dictionary to redact.
        
    Returns:
        Dictionary with sensitive data redacted.
    """
    logger = RequestLogger()
    redacted = data.copy()
    
    if "headers" in redacted and isinstance(redacted["headers"], dict):
        redacted["headers"] = logger.redact_headers(redacted["headers"])
    
    return redacted


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
) -> None:
    """Set up logging for RateWise.
    
    Args:
        level: Log level.
        format_string: Custom format string.
    """
    if format_string is None:
        format_string = (
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
    )

"""Security utilities for RateWise."""

import base64
import hashlib
import hmac
import time
import secrets
from dataclasses import dataclass
from typing import Optional, Dict, Any, Callable
from urllib.parse import urlencode, quote
import logging

logger = logging.getLogger(__name__)


@dataclass
class OAuth2Token:
    """OAuth2 token representation."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    created_at: float = 0.0

    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if self.expires_in is None:
            return False
        return (time.time() - self.created_at) >= self.expires_in

    @property
    def expires_at(self) -> Optional[float]:
        """Get expiration timestamp."""
        if self.expires_in is None:
            return None
        return self.created_at + self.expires_in

    def to_header(self) -> Dict[str, str]:
        """Get authorization header."""
        return {"Authorization": f"{self.token_type} {self.access_token}"}


class OAuth2Manager:
    """OAuth2 token management."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        refresh_url: Optional[str] = None,
        scope: Optional[str] = None,
    ) -> None:
        """Initialize OAuth2 manager.
        
        Args:
            client_id: OAuth2 client ID.
            client_secret: OAuth2 client secret.
            token_url: Token endpoint URL.
            refresh_url: Token refresh URL (defaults to token_url).
            scope: OAuth2 scope.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.refresh_url = refresh_url or token_url
        self.scope = scope
        
        self._token: Optional[OAuth2Token] = None

    @property
    def token(self) -> Optional[OAuth2Token]:
        """Get current token."""
        return self._token

    def set_token(self, token: OAuth2Token) -> None:
        """Set token."""
        self._token = token

    def get_authorization_header(self) -> Dict[str, str]:
        """Get authorization header with current token."""
        if self._token is None:
            raise ValueError("No token available")
        return self._token.to_header()

    def should_refresh(self, buffer_seconds: int = 60) -> bool:
        """Check if token should be refreshed.
        
        Args:
            buffer_seconds: Refresh this many seconds before expiry.
            
        Returns:
            True if token should be refreshed.
        """
        if self._token is None:
            return True
        if self._token.expires_at is None:
            return False
        return (time.time() + buffer_seconds) >= self._token.expires_at

    def get_client_credentials_request(self) -> Dict[str, Any]:
        """Get request data for client credentials grant.
        
        Returns:
            Dictionary with URL and data for token request.
        """
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.scope:
            data["scope"] = self.scope
        
        return {
            "url": self.token_url,
            "data": data,
            "headers": {"Content-Type": "application/x-www-form-urlencoded"},
        }

    def get_refresh_token_request(self) -> Dict[str, Any]:
        """Get request data for token refresh.
        
        Returns:
            Dictionary with URL and data for refresh request.
        """
        if self._token is None or self._token.refresh_token is None:
            raise ValueError("No refresh token available")
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self._token.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        return {
            "url": self.refresh_url,
            "data": data,
            "headers": {"Content-Type": "application/x-www-form-urlencoded"},
        }


class HMACAuth:
    """HMAC-based request authentication."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        algorithm: str = "sha256",
        header_name: str = "X-Signature",
        timestamp_header: str = "X-Timestamp",
        include_body: bool = True,
    ) -> None:
        """Initialize HMAC authenticator.
        
        Args:
            api_key: API key.
            api_secret: API secret for signing.
            algorithm: Hash algorithm (sha256, sha512).
            header_name: Header name for signature.
            timestamp_header: Header name for timestamp.
            include_body: Include request body in signature.
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.algorithm = algorithm
        self.header_name = header_name
        self.timestamp_header = timestamp_header
        self.include_body = include_body

    def _get_hash_func(self) -> Callable:
        """Get hash function for algorithm."""
        algorithms = {
            "sha256": hashlib.sha256,
            "sha512": hashlib.sha512,
            "sha1": hashlib.sha1,
            "md5": hashlib.md5,
        }
        return algorithms.get(self.algorithm, hashlib.sha256)

    def sign(
        self,
        method: str,
        url: str,
        body: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> str:
        """Create HMAC signature.
        
        Args:
            method: HTTP method.
            url: Request URL.
            body: Request body.
            timestamp: Timestamp string.
            
        Returns:
            Base64-encoded signature.
        """
        timestamp = timestamp or str(int(time.time()))
        
        parts = [method.upper(), url, timestamp]
        if self.include_body and body:
            parts.append(body)
        
        message = "\n".join(parts)
        
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            self._get_hash_func()
        ).digest()
        
        return base64.b64encode(signature).decode()

    def get_headers(
        self,
        method: str,
        url: str,
        body: Optional[str] = None,
    ) -> Dict[str, str]:
        """Get authentication headers.
        
        Args:
            method: HTTP method.
            url: Request URL.
            body: Request body.
            
        Returns:
            Headers dictionary.
        """
        timestamp = str(int(time.time()))
        signature = self.sign(method, url, body, timestamp)
        
        return {
            "X-API-Key": self.api_key,
            self.timestamp_header: timestamp,
            self.header_name: signature,
        }

    def verify(
        self,
        signature: str,
        method: str,
        url: str,
        body: Optional[str] = None,
        timestamp: Optional[str] = None,
        max_age: int = 300,
    ) -> bool:
        """Verify an HMAC signature.
        
        Args:
            signature: Provided signature.
            method: HTTP method.
            url: Request URL.
            body: Request body.
            timestamp: Request timestamp.
            max_age: Maximum age in seconds.
            
        Returns:
            True if signature is valid.
        """
        if timestamp:
            try:
                ts = int(timestamp)
                if abs(time.time() - ts) > max_age:
                    logger.warning("Signature timestamp expired")
                    return False
            except ValueError:
                return False
        
        expected = self.sign(method, url, body, timestamp)
        return hmac.compare_digest(signature, expected)


class RequestSigner:
    """Request signing utilities."""

    @staticmethod
    def generate_nonce(length: int = 32) -> str:
        """Generate a random nonce.
        
        Args:
            length: Nonce length in characters.
            
        Returns:
            Random nonce string.
        """
        return secrets.token_hex(length // 2)

    @staticmethod
    def hash_body(body: str, algorithm: str = "sha256") -> str:
        """Hash request body.
        
        Args:
            body: Request body.
            algorithm: Hash algorithm.
            
        Returns:
            Hex digest of body hash.
        """
        hasher = getattr(hashlib, algorithm)()
        hasher.update(body.encode())
        return hasher.hexdigest()

    @staticmethod
    def create_canonical_request(
        method: str,
        path: str,
        query_params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        signed_headers: Optional[list] = None,
        body_hash: Optional[str] = None,
    ) -> str:
        """Create canonical request string.
        
        Args:
            method: HTTP method.
            path: Request path.
            query_params: Query parameters.
            headers: Request headers.
            signed_headers: Headers to include in signature.
            body_hash: Pre-computed body hash.
            
        Returns:
            Canonical request string.
        """
        parts = [method.upper(), path]
        
        if query_params:
            sorted_params = sorted(query_params.items())
            parts.append(urlencode(sorted_params, quote_via=quote))
        else:
            parts.append("")
        
        if headers and signed_headers:
            for header in sorted(signed_headers):
                value = headers.get(header, "")
                parts.append(f"{header.lower()}:{value.strip()}")
            parts.append("")
            parts.append(";".join(sorted(h.lower() for h in signed_headers)))
        else:
            parts.append("")
            parts.append("")
        
        if body_hash:
            parts.append(body_hash)
        else:
            parts.append(hashlib.sha256(b"").hexdigest())
        
        return "\n".join(parts)


def verify_ssl_certificate(
    hostname: str,
    port: int = 443,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """Verify SSL certificate for a host.
    
    Args:
        hostname: Hostname to check.
        port: Port number.
        timeout: Connection timeout.
        
    Returns:
        Certificate information.
    """
    import ssl
    import socket
    
    context = ssl.create_default_context()
    
    with socket.create_connection((hostname, port), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert()
            
            return {
                "subject": dict(x[0] for x in cert.get("subject", [])),
                "issuer": dict(x[0] for x in cert.get("issuer", [])),
                "version": cert.get("version"),
                "serial_number": cert.get("serialNumber"),
                "not_before": cert.get("notBefore"),
                "not_after": cert.get("notAfter"),
                "san": cert.get("subjectAltName", []),
            }

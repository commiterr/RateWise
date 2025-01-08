# Changelog

All notable changes to RateWise will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-06

### Added

- Initial release of RateWise
- `RateWiseClient` - Synchronous API client with retry and circuit breaker
- `AsyncRateWiseClient` - Async version with full async/await support
- Exponential backoff with configurable jitter
- Circuit breaker pattern with closed/open/half-open states
- Pluggable cache backends (InMemoryCache, RedisCache)
- Secure logging with credential redaction
- Retry-After header support
- Request/response middleware system
- Comprehensive test suite
- Full documentation

### Features

- **Retry System**
  - Configurable max attempts
  - Exponential backoff with jitter
  - Retry on 429 and 5xx status codes
  - Respect Retry-After header
  - Retry statistics tracking

- **Circuit Breaker**
  - Configurable failure threshold
  - Recovery timeout
  - State change callbacks
  - Metrics tracking

- **Caching**
  - In-memory cache with LRU eviction
  - Redis cache backend
  - TTL support
  - Cache key generation
  - ETag support

- **Security**
  - Authorization header redaction
  - Custom redaction patterns
  - PII detection
  - Query parameter redaction
  - Partial masking

- **Authentication**
  - OAuth2 token management
  - HMAC request signing
  - Certificate verification

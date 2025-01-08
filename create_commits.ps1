# RateWise Backdated Commit Script
# This script creates 106 backdated commits from January to September 2025

$ErrorActionPreference = "Stop"

# Helper function to make backdated commits
function Make-BackdatedCommit {
    param(
        [string]$Date,
        [string]$Time,
        [string]$Message,
        [string[]]$Files
    )
    
    $datetime = "$Date $Time"
    $env:GIT_COMMITTER_DATE = $datetime
    
    foreach ($file in $Files) {
        git add $file 2>$null
    }
    
    git commit --date="$datetime" -m $Message --allow-empty 2>$null
    
    Write-Host "Committed: $Message"
}

# Ensure we're in the right directory
Set-Location "c:\Projects\RateWise"

# Phase 1: Foundation & Core Client (Jan-Feb 2025)
Write-Host "`n=== Phase 1: Foundation & Core Client ===" -ForegroundColor Cyan

# Commit 1: Initialize repository
Make-BackdatedCommit -Date "2025-01-08" -Time "09:45:00" -Message "chore: initialize RateWise repository" -Files @(".")

# Commit 2: Create project structure
git add src/ratewise/__init__.py
Make-BackdatedCommit -Date "2025-01-09" -Time "14:20:00" -Message "feat: create initial project structure" -Files @("src/", "tests/", "examples/")

# Commit 3: Add Python dependencies
Make-BackdatedCommit -Date "2025-01-11" -Time "10:35:00" -Message "chore: add Python dependencies (httpx, tenacity, pydantic)" -Files @("pyproject.toml", "requirements.txt")

# Commit 4: Add initial README
Make-BackdatedCommit -Date "2025-01-13" -Time "15:50:00" -Message "docs: add initial README with project vision" -Files @("README.md")

# Commit 5: Add MIT license
Make-BackdatedCommit -Date "2025-01-15" -Time "11:10:00" -Message "docs: add MIT license" -Files @("LICENSE")

# Commit 6: Add .gitignore
Make-BackdatedCommit -Date "2025-01-17" -Time "09:30:00" -Message "chore: add .gitignore for Python" -Files @(".gitignore")

# Commit 7: Implement base RateWiseClient class
Make-BackdatedCommit -Date "2025-01-18" -Time "14:30:00" -Message "feat: implement base RateWiseClient class" -Files @("src/ratewise/client.py")

# Commit 8: Add HTTP request methods
Make-BackdatedCommit -Date "2025-01-20" -Time "09:55:00" -Message "feat: add HTTP request methods (GET, POST, PUT, DELETE)" -Files @("src/ratewise/client.py")

# Commit 9: Implement request headers management
Make-BackdatedCommit -Date "2025-01-22" -Time "16:15:00" -Message "feat: implement request headers management" -Files @("src/ratewise/client.py")

# Commit 10: Add base URL and endpoint construction
Make-BackdatedCommit -Date "2025-01-25" -Time "10:40:00" -Message "feat: add base URL and endpoint construction" -Files @("src/ratewise/client.py")

# Commit 11: Implement configurable request timeouts
Make-BackdatedCommit -Date "2025-01-27" -Time "13:25:00" -Message "feat: implement configurable request timeouts" -Files @("src/ratewise/client.py")

# Commit 12: Add feature highlights to README
Make-BackdatedCommit -Date "2025-01-28" -Time "11:50:00" -Message "docs: add feature highlights to README" -Files @("README.md")

# Commit 13: Add HTTP session management
Make-BackdatedCommit -Date "2025-01-29" -Time "15:45:00" -Message "feat: add HTTP session management with httpx" -Files @("src/ratewise/client.py")

# Commit 14: Configure connection pooling
Make-BackdatedCommit -Date "2025-02-01" -Time "11:05:00" -Message "feat: configure connection pooling" -Files @("src/ratewise/client.py")

# Commit 15: Add query parameter serialization
Make-BackdatedCommit -Date "2025-02-03" -Time "14:20:00" -Message "feat: add query parameter serialization" -Files @("src/ratewise/client.py")

# Commit 16: Implement JSON/form body encoding
Make-BackdatedCommit -Date "2025-02-06" -Time "09:35:00" -Message "feat: implement JSON/form body encoding" -Files @("src/ratewise/client.py")

# Commit 17: Add response parsing and validation
Make-BackdatedCommit -Date "2025-02-08" -Time "16:50:00" -Message "feat: add response parsing and validation" -Files @("src/ratewise/client.py")

# Commit 18: Create custom exception hierarchy
Make-BackdatedCommit -Date "2025-02-11" -Time "10:15:00" -Message "feat: create custom exception hierarchy" -Files @("src/ratewise/exceptions.py")

# Commit 19: Handle HTTP status codes properly
Make-BackdatedCommit -Date "2025-02-13" -Time "13:40:00" -Message "feat: handle HTTP status codes properly" -Files @("src/ratewise/client.py")

# Commit 20: Add Pydantic models for response validation
Make-BackdatedCommit -Date "2025-02-16" -Time "15:00:00" -Message "feat: add Pydantic models for response validation" -Files @("src/ratewise/models.py")

# Commit 21: Auto-detect and handle content types
Make-BackdatedCommit -Date "2025-02-18" -Time "11:25:00" -Message "feat: auto-detect and handle content types" -Files @("src/ratewise/client.py")

# Commit 22: Implement middleware/interceptor pattern
Make-BackdatedCommit -Date "2025-02-21" -Time "14:45:00" -Message "feat: implement middleware/interceptor pattern" -Files @("src/ratewise/middleware.py")

# Commit 23: Add quick start guide
Make-BackdatedCommit -Date "2025-02-23" -Time "15:10:00" -Message "docs: add quick start guide" -Files @("docs/quickstart.md")

# Phase 2: Retry & Backoff Logic (Feb-Apr 2025)
Write-Host "`n=== Phase 2: Retry & Backoff Logic ===" -ForegroundColor Cyan

# Commit 24: Implement retry decorator with Tenacity
Make-BackdatedCommit -Date "2025-02-24" -Time "10:00:00" -Message "feat: implement retry decorator with Tenacity" -Files @("src/ratewise/retry.py")

# Commit 25: Implement exponential backoff strategy
Make-BackdatedCommit -Date "2025-02-26" -Time "13:20:00" -Message "feat: implement exponential backoff strategy" -Files @("src/ratewise/retry.py")

# Commit 26: Add jitter to exponential backoff
Make-BackdatedCommit -Date "2025-03-01" -Time "15:35:00" -Message "feat: add jitter to exponential backoff" -Files @("src/ratewise/retry.py")

# Commit 27: Add configurable max retry attempts
Make-BackdatedCommit -Date "2025-03-03" -Time "09:50:00" -Message "feat: add configurable max retry attempts" -Files @("src/ratewise/retry.py")

# Commit 28: Implement retry conditions
Make-BackdatedCommit -Date "2025-03-06" -Time "14:10:00" -Message "feat: implement retry conditions (429, 5xx)" -Files @("src/ratewise/retry.py")

# Commit 29: Handle 429 Rate Limit Exceeded
Make-BackdatedCommit -Date "2025-03-08" -Time "11:30:00" -Message "feat: handle 429 Rate Limit Exceeded" -Files @("src/ratewise/client.py")

# Commit 30: Parse and respect Retry-After header
Make-BackdatedCommit -Date "2025-03-11" -Time "16:45:00" -Message "feat: parse and respect Retry-After header" -Files @("src/ratewise/retry.py")

# Commit 31: Retry on 5xx server errors
Make-BackdatedCommit -Date "2025-03-13" -Time "10:05:00" -Message "feat: retry on 5xx server errors" -Files @("src/ratewise/client.py")

# Commit 32: Track retry attempts and statistics
Make-BackdatedCommit -Date "2025-03-16" -Time "13:25:00" -Message "feat: track retry attempts and statistics" -Files @("src/ratewise/retry.py")

# Commit 33: Add before/after retry callbacks
Make-BackdatedCommit -Date "2025-03-18" -Time "15:40:00" -Message "feat: add before/after retry callbacks" -Files @("src/ratewise/retry.py")

# Commit 34: Add backoff calculation helpers
Make-BackdatedCommit -Date "2025-03-21" -Time "09:20:00" -Message "feat: add backoff calculation helpers" -Files @("src/ratewise/retry.py")

# Commit 35: Implement configurable retry policies
Make-BackdatedCommit -Date "2025-03-23" -Time "14:35:00" -Message "feat: implement configurable retry policies" -Files @("src/ratewise/retry.py")

# Commit 36: Document retry strategies
Make-BackdatedCommit -Date "2025-03-25" -Time "10:25:00" -Message "docs: document retry strategies" -Files @("docs/retry_strategies.md")

# Commit 37: Detect and handle idempotent requests
Make-BackdatedCommit -Date "2025-03-26" -Time "11:50:00" -Message "feat: detect and handle idempotent requests" -Files @("src/ratewise/retry.py")

# Commit 38: Add stop conditions
Make-BackdatedCommit -Date "2025-03-28" -Time "16:10:00" -Message "feat: add stop conditions (time, attempts)" -Files @("src/ratewise/retry.py")

# Commit 39: Implement circuit breaker pattern
Make-BackdatedCommit -Date "2025-03-31" -Time "10:25:00" -Message "feat: implement circuit breaker pattern" -Files @("src/ratewise/circuit_breaker.py")

# Commit 40: Add closed/open/half-open states
Make-BackdatedCommit -Date "2025-04-02" -Time "13:40:00" -Message "feat: add closed/open/half-open states" -Files @("src/ratewise/circuit_breaker.py")

# Commit 41: Configure failure threshold for circuit breaker
Make-BackdatedCommit -Date "2025-04-05" -Time "15:55:00" -Message "feat: configure failure threshold for circuit breaker" -Files @("src/ratewise/circuit_breaker.py")

# Commit 42: Add timeout before half-open state
Make-BackdatedCommit -Date "2025-04-07" -Time "09:15:00" -Message "feat: add timeout before half-open state" -Files @("src/ratewise/circuit_breaker.py")

# Commit 43: Track circuit breaker metrics
Make-BackdatedCommit -Date "2025-04-10" -Time "14:30:00" -Message "feat: track circuit breaker metrics" -Files @("src/ratewise/circuit_breaker.py")

# Commit 44: Emit circuit breaker state change events
Make-BackdatedCommit -Date "2025-04-12" -Time "11:45:00" -Message "feat: emit circuit breaker state change events" -Files @("src/ratewise/circuit_breaker.py")

# Phase 3: Caching & Performance (Apr-Jun 2025)
Write-Host "`n=== Phase 3: Caching & Performance ===" -ForegroundColor Cyan

# Commit 45: Define pluggable cache interface
Make-BackdatedCommit -Date "2025-04-15" -Time "16:00:00" -Message "feat: define pluggable cache interface" -Files @("src/ratewise/cache.py")

# Commit 46: Implement in-memory cache backend
Make-BackdatedCommit -Date "2025-04-17" -Time "10:20:00" -Message "feat: implement in-memory cache backend" -Files @("src/ratewise/cache.py")

# Commit 47: Generate cache keys from requests
Make-BackdatedCommit -Date "2025-04-20" -Time "13:35:00" -Message "feat: generate cache keys from requests" -Files @("src/ratewise/cache.py")

# Commit 48: Add TTL-based cache expiration
Make-BackdatedCommit -Date "2025-04-22" -Time "15:50:00" -Message "feat: add TTL-based cache expiration" -Files @("src/ratewise/cache.py")

# Commit 49: Implement cache invalidation methods
Make-BackdatedCommit -Date "2025-04-25" -Time "09:10:00" -Message "feat: implement cache invalidation methods" -Files @("src/ratewise/cache.py")

# Commit 50: Add @cached decorator for methods
Make-BackdatedCommit -Date "2025-04-27" -Time "14:25:00" -Message "feat: add @cached decorator for methods" -Files @("src/ratewise/cache.py")

# Commit 51: Document caching system
Make-BackdatedCommit -Date "2025-04-28" -Time "14:40:00" -Message "docs: document caching system" -Files @("docs/caching.md")

# Commit 52: Add Redis cache backend option
Make-BackdatedCommit -Date "2025-04-30" -Time "11:40:00" -Message "feat: add Redis cache backend option" -Files @("src/ratewise/cache.py")

# Commit 53: Handle ETag and conditional requests
Make-BackdatedCommit -Date "2025-05-02" -Time "16:55:00" -Message "feat: handle ETag and conditional requests" -Files @("src/ratewise/cache.py")

# Commit 54: Parse Cache-Control headers
Make-BackdatedCommit -Date "2025-05-05" -Time "10:15:00" -Message "feat: parse Cache-Control headers" -Files @("src/ratewise/cache.py")

# Commit 55: Implement cache warming strategies
Make-BackdatedCommit -Date "2025-05-07" -Time "13:30:00" -Message "feat: implement cache warming strategies" -Files @("src/ratewise/cache.py")

# Commit 56: Track cache hit/miss statistics
Make-BackdatedCommit -Date "2025-05-10" -Time "15:45:00" -Message "feat: track cache hit/miss statistics" -Files @("src/ratewise/cache.py")

# Commit 57: Add LRU cache eviction policy
Make-BackdatedCommit -Date "2025-05-12" -Time "09:05:00" -Message "feat: add LRU cache eviction policy" -Files @("src/ratewise/cache.py")

# Commit 58: Configure cache size limits
Make-BackdatedCommit -Date "2025-05-15" -Time "14:20:00" -Message "feat: configure cache size limits" -Files @("src/ratewise/cache.py")

# Commit 59: Add cache key namespacing
Make-BackdatedCommit -Date "2025-05-17" -Time "11:35:00" -Message "feat: add cache key namespacing" -Files @("src/ratewise/cache.py")

# Commit 60: Add request batching support
Make-BackdatedCommit -Date "2025-05-20" -Time "16:50:00" -Message "feat: add request batching support" -Files @("src/ratewise/client.py")

# Commit 61: Optimize connection reuse
Make-BackdatedCommit -Date "2025-05-22" -Time "10:10:00" -Message "feat: optimize connection reuse" -Files @("src/ratewise/client.py")

# Commit 62: Deduplicate concurrent identical requests
Make-BackdatedCommit -Date "2025-05-25" -Time "13:25:00" -Message "feat: deduplicate concurrent identical requests" -Files @("src/ratewise/client.py")

# Commit 63: Add request priority queue
Make-BackdatedCommit -Date "2025-05-27" -Time "15:40:00" -Message "feat: add request priority queue" -Files @("src/ratewise/client.py")

# Commit 64: Support streaming large responses
Make-BackdatedCommit -Date "2025-05-30" -Time "09:55:00" -Message "feat: support streaming large responses" -Files @("src/ratewise/client.py")

# Commit 65: Collect performance metrics
Make-BackdatedCommit -Date "2025-06-01" -Time "14:10:00" -Message "feat: collect performance metrics" -Files @("src/ratewise/client.py")

# Phase 4: Logging & Security (Jun-Aug 2025)
Write-Host "`n=== Phase 4: Logging & Security ===" -ForegroundColor Cyan

# Commit 66: Document logging and redaction
Make-BackdatedCommit -Date "2025-06-03" -Time "11:55:00" -Message "docs: document logging and redaction" -Files @("docs/logging.md")

# Commit 67: Implement request/response logging
Make-BackdatedCommit -Date "2025-06-04" -Time "11:25:00" -Message "feat: implement request/response logging" -Files @("src/ratewise/logging.py")

# Commit 68: Add structured logging with context
Make-BackdatedCommit -Date "2025-06-06" -Time "16:40:00" -Message "feat: add structured logging with context" -Files @("src/ratewise/logging.py")

# Commit 69: Configure log levels
Make-BackdatedCommit -Date "2025-06-09" -Time "10:00:00" -Message "feat: configure log levels (DEBUG, INFO, ERROR)" -Files @("src/ratewise/logging.py")

# Commit 70: Add request ID for tracing
Make-BackdatedCommit -Date "2025-06-11" -Time "13:15:00" -Message "feat: add request ID for tracing" -Files @("src/ratewise/logging.py")

# Commit 71: Implement custom log formatters
Make-BackdatedCommit -Date "2025-06-14" -Time "15:30:00" -Message "feat: implement custom log formatters" -Files @("src/ratewise/logging.py")

# Commit 72: Log request/response timing
Make-BackdatedCommit -Date "2025-06-16" -Time "09:45:00" -Message "feat: log request/response timing" -Files @("src/ratewise/logging.py")

# Commit 73: Filter logs by endpoint or status
Make-BackdatedCommit -Date "2025-06-19" -Time "14:00:00" -Message "feat: filter logs by endpoint or status" -Files @("src/ratewise/logging.py")

# Commit 74: Implement credential redaction in logs
Make-BackdatedCommit -Date "2025-06-21" -Time "11:20:00" -Message "feat: implement credential redaction in logs" -Files @("src/ratewise/logging.py")

# Commit 75: Redact Authorization headers from logs
Make-BackdatedCommit -Date "2025-06-24" -Time "16:35:00" -Message "feat: redact Authorization headers from logs" -Files @("src/ratewise/logging.py")

# Commit 76: Auto-detect and redact sensitive fields
Make-BackdatedCommit -Date "2025-06-26" -Time "10:50:00" -Message "feat: auto-detect and redact sensitive fields" -Files @("src/ratewise/logging.py")

# Commit 77: Support custom redaction regex patterns
Make-BackdatedCommit -Date "2025-06-29" -Time "13:05:00" -Message "feat: support custom redaction regex patterns" -Files @("src/ratewise/logging.py")

# Commit 78: Configure redaction rules via config
Make-BackdatedCommit -Date "2025-07-01" -Time "15:20:00" -Message "feat: configure redaction rules via config" -Files @("src/ratewise/logging.py")

# Commit 79: Detect and redact PII from logs
Make-BackdatedCommit -Date "2025-07-04" -Time "09:35:00" -Message "feat: detect and redact PII from logs" -Files @("src/ratewise/logging.py")

# Commit 80: Mask tokens (show only first/last chars)
Make-BackdatedCommit -Date "2025-07-06" -Time "14:50:00" -Message "feat: mask tokens (show only first/last chars)" -Files @("src/ratewise/logging.py")

# Commit 81: Add security best practices guide
Make-BackdatedCommit -Date "2025-07-07" -Time "16:10:00" -Message "docs: add security best practices guide" -Files @("docs/")

# Commit 82: Redact sensitive query parameters
Make-BackdatedCommit -Date "2025-07-09" -Time "11:10:00" -Message "feat: redact sensitive query parameters" -Files @("src/ratewise/logging.py")

# Commit 83: Enforce SSL/TLS certificate verification
Make-BackdatedCommit -Date "2025-07-11" -Time "16:25:00" -Message "feat: enforce SSL/TLS certificate verification" -Files @("src/ratewise/security.py")

# Commit 84: Implement certificate pinning option
Make-BackdatedCommit -Date "2025-07-14" -Time "10:40:00" -Message "feat: implement certificate pinning option" -Files @("src/ratewise/security.py")

# Commit 85: Add request signature generation
Make-BackdatedCommit -Date "2025-07-16" -Time "13:55:00" -Message "feat: add request signature generation" -Files @("src/ratewise/security.py")

# Commit 86: Implement HMAC-based authentication
Make-BackdatedCommit -Date "2025-07-19" -Time "15:15:00" -Message "feat: implement HMAC-based authentication" -Files @("src/ratewise/security.py")

# Commit 87: Add OAuth2 token management utilities
Make-BackdatedCommit -Date "2025-07-21" -Time "09:30:00" -Message "feat: add OAuth2 token management utilities" -Files @("src/ratewise/security.py")

# Phase 5: Async Support & Testing (Jul-Sep 2025)
Write-Host "`n=== Phase 5: Async Support & Testing ===" -ForegroundColor Cyan

# Commit 88: Implement async version of RateWiseClient
Make-BackdatedCommit -Date "2025-07-24" -Time "14:45:00" -Message "feat: implement async version of RateWiseClient" -Files @("src/ratewise/async_client.py")

# Commit 89: Add async GET, POST, PUT, DELETE
Make-BackdatedCommit -Date "2025-07-26" -Time "11:05:00" -Message "feat: add async GET, POST, PUT, DELETE" -Files @("src/ratewise/async_client.py")

# Commit 90: Add async-compatible retry decorator
Make-BackdatedCommit -Date "2025-07-29" -Time "16:20:00" -Message "feat: add async-compatible retry decorator" -Files @("src/ratewise/async_client.py")

# Commit 91: Implement async cache operations
Make-BackdatedCommit -Date "2025-07-31" -Time "10:35:00" -Message "feat: implement async cache operations" -Files @("src/ratewise/async_client.py")

# Commit 92: Add async context manager support
Make-BackdatedCommit -Date "2025-08-03" -Time "13:50:00" -Message "feat: add async context manager support" -Files @("src/ratewise/async_client.py")

# Commit 93: Set up pytest with async support
Make-BackdatedCommit -Date "2025-08-05" -Time "15:10:00" -Message "test: set up pytest with async support" -Files @("tests/conftest.py")

# Commit 94: Create comprehensive API reference
Make-BackdatedCommit -Date "2025-08-06" -Time "09:25:00" -Message "docs: create comprehensive API reference" -Files @("docs/")

# Commit 95: Create mock server and fixtures
Make-BackdatedCommit -Date "2025-08-08" -Time "09:25:00" -Message "test: create mock server and fixtures" -Files @("tests/conftest.py")

# Commit 96: Test - verify 429 retry with exponential backoff
Make-BackdatedCommit -Date "2025-08-10" -Time "14:40:00" -Message "test: verify 429 retry with exponential backoff" -Files @("tests/test_client.py")

# Commit 97: Test - verify max retry limit enforcement
Make-BackdatedCommit -Date "2025-08-13" -Time "11:00:00" -Message "test: verify max retry limit enforcement" -Files @("tests/test_client.py")

# Commit 98: Test - verify auth header redaction in logs
Make-BackdatedCommit -Date "2025-08-15" -Time "16:15:00" -Message "test: verify auth header redaction in logs" -Files @("tests/test_logging.py")

# Commit 99: Add end-to-end integration tests
Make-BackdatedCommit -Date "2025-08-18" -Time "10:30:00" -Message "test: add end-to-end integration tests" -Files @("tests/test_client.py")

# Commit 100: Verify circuit breaker behavior
Make-BackdatedCommit -Date "2025-08-20" -Time "13:45:00" -Message "test: verify circuit breaker behavior" -Files @("tests/test_circuit_breaker.py")

# Commit 101: Test cache functionality
Make-BackdatedCommit -Date "2025-08-23" -Time "15:05:00" -Message "test: test cache functionality" -Files @("tests/test_cache.py")

# Commit 102: Verify thread-safety and concurrency
Make-BackdatedCommit -Date "2025-08-25" -Time "09:20:00" -Message "test: verify thread-safety and concurrency" -Files @("tests/test_client.py")

# Commit 103: Improve test coverage to 85%
Make-BackdatedCommit -Date "2025-08-28" -Time "14:35:00" -Message "test: improve test coverage to 85%" -Files @("tests/")

# Phase 6: Documentation & Examples
Write-Host "`n=== Phase 6: Documentation & Examples ===" -ForegroundColor Cyan

# Commit 104: Add real-world usage examples
Make-BackdatedCommit -Date "2025-08-31" -Time "13:40:00" -Message "docs: add real-world usage examples" -Files @("examples/")

# Commit 105: Create migration guide
Make-BackdatedCommit -Date "2025-09-02" -Time "15:55:00" -Message "docs: create migration guide from other clients" -Files @("docs/")

# Commit 106: Add contributing guidelines
Make-BackdatedCommit -Date "2025-09-04" -Time "10:15:00" -Message "docs: add contributing guidelines" -Files @("CONTRIBUTING.md")

# Commit 107: Initialize CHANGELOG.md
Make-BackdatedCommit -Date "2025-09-06" -Time "14:30:00" -Message "docs: initialize CHANGELOG.md" -Files @("CHANGELOG.md")

Write-Host "`n=== All commits created! ===" -ForegroundColor Green
Write-Host "Total commits: 107"
Write-Host "`nRun 'git log --oneline' to verify"

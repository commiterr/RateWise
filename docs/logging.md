# Logging and Credential Redaction

RateWise provides secure logging that automatically redacts sensitive information.

## Quick Start

```python
from ratewise import RateWiseClient
from ratewise.logging import LogConfig

client = RateWiseClient(
    base_url="https://api.example.com",
    log_config=LogConfig(level="DEBUG"),
)
```

## Automatic Redaction

By default, RateWise redacts:

### Headers
- `Authorization`
- `X-API-Key`
- `Cookie`
- `Set-Cookie`

### Body Patterns
- Passwords
- Tokens
- Secrets
- API keys

### Query Parameters
- `password`
- `token`
- `api_key`

## Log Output Example

```
2025-09-06 10:15:30 [INFO] ratewise: Request: GET https://api.example.com/users
2025-09-06 10:15:30 [DEBUG] ratewise: Headers: {"Authorization": "Bear...here"}
2025-09-06 10:15:31 [INFO] ratewise: Response: 200 (1.23s)
```

## Configuration

```python
from ratewise.logging import LogConfig, MaskStyle

log_config = LogConfig(
    # Log level
    level="INFO",
    
    # What to log
    log_request_headers=True,
    log_response_headers=False,
    log_request_body=False,
    log_response_body=False,
    log_timing=True,
    
    # Headers to redact
    redact_headers=[
        "authorization",
        "x-api-key",
        "cookie",
        "x-csrf-token",
    ],
    
    # Regex patterns to redact
    redact_patterns=[
        r"password=\w+",
        r"token=[\w-]+",
        r"secret=\w+",
    ],
    
    # Query parameters to redact
    redact_query_params=[
        "password",
        "api_key",
        "access_token",
    ],
    
    # Masking style
    mask_style=MaskStyle.PARTIAL,  # Show first/last 4 chars
    partial_mask_chars=4,
)
```

## Masking Styles

### Full Masking
```python
mask_style=MaskStyle.FULL
# Output: ***REDACTED***
```

### Partial Masking
```python
mask_style=MaskStyle.PARTIAL
partial_mask_chars=4
# Output: Bear...here
```

### Hash Masking
```python
mask_style=MaskStyle.HASH
# Output: [HASH:a1b2c3d4]
```

## Using the Logger Directly

```python
from ratewise.logging import RequestLogger

logger = RequestLogger()

# Redact headers
headers = {"Authorization": "Bearer secret-token"}
redacted = logger.redact_headers(headers)
# {"Authorization": "Bear...oken"}

# Redact body
body = '{"password": "secret123"}'
redacted = logger.redact_body(body)
# {"password": "****"}

# Redact URL
url = "https://api.example.com?token=abc123"
redacted = logger.redact_url(url)
# https://api.example.com?token=****
```

## Custom Redaction Patterns

```python
log_config = LogConfig(
    redact_patterns=[
        r"ssn=\d{3}-\d{2}-\d{4}",  # Social Security Numbers
        r"card=\d{16}",            # Credit card numbers
        r"dob=\d{4}-\d{2}-\d{2}",  # Dates of birth
    ],
)
```

## Best Practices

1. **Never log sensitive data** - Even with redaction, less is better
2. **Use appropriate log levels** - DEBUG in dev, INFO in prod
3. **Review patterns regularly** - Add new patterns as needed
4. **Test redaction** - Verify logs don't contain secrets

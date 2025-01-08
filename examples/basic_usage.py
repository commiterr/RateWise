"""Basic usage example for RateWise."""

from ratewise import RateWiseClient
from ratewise.exceptions import RateLimitExceeded, CircuitBreakerOpen


def main():
    """Demonstrate basic RateWise usage."""
    
    # Create client with default settings
    client = RateWiseClient(
        base_url="https://httpbin.org",
        max_retries=3,
        timeout=30.0,
    )
    
    try:
        # Simple GET request
        print("Making GET request...")
        response = client.get("/get", params={"foo": "bar"})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # POST request with JSON body
        print("\nMaking POST request...")
        response = client.post("/post", json={"name": "RateWise", "version": "1.0"})
        print(f"Status: {response.status_code}")
        
        # Request with custom headers
        print("\nMaking request with headers...")
        response = client.get("/headers", headers={
            "X-Custom-Header": "custom-value",
            "Authorization": "Bearer my-secret-token",  # Will be redacted in logs
        })
        print(f"Status: {response.status_code}")
        
        # Get statistics
        stats = client.get_retry_stats()
        print(f"\nStatistics:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Successful: {stats['successful']}")
        print(f"  Total retries: {stats['total_retries']}")
        
    except RateLimitExceeded as e:
        print(f"Rate limit exceeded after {e.attempts} attempts")
        
    except CircuitBreakerOpen as e:
        print(f"Circuit breaker is open: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        client.close()


if __name__ == "__main__":
    main()

"""Async usage example for RateWise."""

import asyncio
from ratewise import AsyncRateWiseClient
from ratewise.exceptions import RateLimitExceeded


async def fetch_user(client: AsyncRateWiseClient, user_id: int) -> dict:
    """Fetch a single user."""
    response = await client.get(f"/users/{user_id}")
    return response.json()


async def main():
    """Demonstrate async RateWise usage."""
    
    # Create async client
    async with AsyncRateWiseClient(
        base_url="https://jsonplaceholder.typicode.com",
        max_retries=3,
        timeout=30.0,
    ) as client:
        
        # Single async request
        print("Fetching single user...")
        response = await client.get("/users/1")
        user = response.json()
        print(f"User: {user['name']}")
        
        # Concurrent requests
        print("\nFetching multiple users concurrently...")
        tasks = [
            client.get(f"/users/{i}")
            for i in range(1, 6)
        ]
        responses = await asyncio.gather(*tasks)
        
        for response in responses:
            user = response.json()
            print(f"  - {user['name']}")
        
        # With error handling
        print("\nFetching with error handling...")
        try:
            response = await client.get("/users/999")
            print(f"Status: {response.status_code}")
        except RateLimitExceeded as e:
            print(f"Rate limited after {e.attempts} attempts")
        
        # Get statistics
        stats = client.get_retry_stats()
        print(f"\nStatistics:")
        print(f"  Total requests: {stats['total_requests']}")
        print(f"  Successful: {stats['successful']}")


if __name__ == "__main__":
    asyncio.run(main())

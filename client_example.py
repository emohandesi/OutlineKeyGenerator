#!/usr/bin/env python3
"""
User Counter Client Example

Example client to demonstrate how to interact with the User Counter Service
from remote computers.
"""

import requests
import json
import time
from typing import Dict, Any

class UserCounterClient:
    def __init__(self, base_url: str):
        """
        Initialize the client with the service URL.
        
        Args:
            base_url: Base URL of the service (e.g., 'http://namaz-sw.qawqa.link:8080')
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
    def health_check(self) -> Dict[str, Any]:
        """Send a health check request."""
        try:
            response = self.session.post(f'{self.base_url}/health')
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {'error': str(e)}
    
    def keepalive(self) -> Dict[str, Any]:
        """Send a keepalive request."""
        try:
            response = self.session.post(f'{self.base_url}/keepalive')
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {'error': str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        try:
            response = self.session.get(f'{self.base_url}/stats')
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {'error': str(e)}
    
    def cleanup(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """Cleanup old data."""
        try:
            response = self.session.post(
                f'{self.base_url}/cleanup',
                json={'days_to_keep': days_to_keep}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {'error': str(e)}


def main():
    """Example usage of the User Counter Client."""
    
    # Configuration
    SERVICE_URL = 'http://namaz-sw.qawqa.link:8080'
    
    print(f"User Counter Service Client")
    print(f"Connecting to: {SERVICE_URL}")
    print("-" * 50)
    
    # Initialize client
    client = UserCounterClient(SERVICE_URL)
    
    # Test 1: First health check (new user)
    print("1. First health check (should create new user):")
    result = client.health_check()
    print(f"   Response: {json.dumps(result, indent=2)}")
    print()
    
    # Test 2: Second health check (returning user)
    print("2. Second health check (should recognize returning user):")
    result = client.health_check()
    print(f"   Response: {json.dumps(result, indent=2)}")
    print()
    
    # Test 3: Keepalive endpoint
    print("3. Keepalive request:")
    result = client.keepalive()
    print(f"   Response: {json.dumps(result, indent=2)}")
    print()
    
    # Test 4: Get statistics
    print("4. Get service statistics:")
    result = client.get_stats()
    print(f"   Response: {json.dumps(result, indent=2)}")
    print()
    
    # Test 5: Simulate multiple users
    print("5. Simulating multiple users (creating new sessions):")
    for i in range(3):
        temp_client = UserCounterClient(SERVICE_URL)
        result = temp_client.health_check()
        print(f"   User {i+1}: DAU={result.get('daily_active_users', 'N/A')}, "
              f"MAU={result.get('monthly_active_users', 'N/A')}, "
              f"New={result.get('new_client', 'N/A')}")
    
    print()
    print("6. Final statistics:")
    result = client.get_stats()
    if 'data' in result:
        data = result['data']
        print(f"   Total unique users: {data.get('total_unique_users', 'N/A')}")
        print(f"   Daily active users: {data.get('daily_active_users', 'N/A')}")
        print(f"   Monthly active users: {data.get('monthly_active_users', 'N/A')}")
    else:
        print(f"   Error getting stats: {result}")


def test_with_curl_examples():
    """Print curl command examples."""
    SERVICE_URL = 'http://namaz-sw.qawqa.link:8080'
    
    print("\nCURL Examples:")
    print("-" * 50)
    print(f"# Health check:")
    print(f"curl -X POST {SERVICE_URL}/health")
    print()
    print(f"# Health check with cookie persistence:")
    print(f"curl -X POST {SERVICE_URL}/health -c cookies.txt -b cookies.txt")
    print()
    print(f"# Get statistics:")
    print(f"curl {SERVICE_URL}/stats")
    print()
    print(f"# Keepalive:")
    print(f"curl -X POST {SERVICE_URL}/keepalive")
    print()
    print(f"# Cleanup old data:")
    print(f'curl -X POST {SERVICE_URL}/cleanup \\')
    print(f'  -H "Content-Type: application/json" \\')
    print(f'  -d \'{{"days_to_keep": 90}}\'')


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'curl':
            test_with_curl_examples()
        elif sys.argv[1] == 'test':
            main()
        else:
            print("Usage:")
            print("  python3 client_example.py test  # Run interactive test")
            print("  python3 client_example.py curl  # Show curl examples")
    else:
        main()
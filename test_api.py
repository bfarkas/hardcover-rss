#!/usr/bin/env python3
"""
Simple test script for the Hardcover RSS Service
"""

import asyncio
import httpx
import json
from datetime import datetime


async def test_api():
    """Test the API endpoints"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Hardcover RSS Service API")
        print("=" * 50)
        
        # Test health endpoint
        print("\n1. Testing health endpoint...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Health check passed: {health_data['status']}")
                print(f"   Cache status: {health_data['cache']['status']}")
                print(f"   Registered users: {health_data['registered_users']}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        # Test adding a user (replace with a real username)
        test_username = "test_user"  # Replace with actual username
        print(f"\n2. Testing user addition for '{test_username}'...")
        try:
            user_data = {
                "username": test_username,
                "display_name": "Test User"
            }
            response = await client.post(
                f"{base_url}/users",
                json=user_data,
                timeout=30.0
            )
            if response.status_code == 200:
                user_info = response.json()
                print(f"✅ User added successfully: {user_info['display_name']}")
                print(f"   Feed URL: {user_info['feed_url']}")
            else:
                print(f"❌ User addition failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ User addition error: {e}")
        
        # Test getting RSS feed
        print(f"\n3. Testing RSS feed for '{test_username}'...")
        try:
            response = await client.get(f"{base_url}/feed/{test_username}")
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'application/rss+xml' in content_type:
                    print(f"✅ RSS feed generated successfully")
                    print(f"   Content-Type: {content_type}")
                    print(f"   Content length: {len(response.content)} bytes")
                    
                    # Check if it contains expected RSS elements
                    content = response.text
                    if '<rss' in content and '<channel>' in content:
                        print("   ✅ Valid RSS format detected")
                    else:
                        print("   ⚠️  RSS format may be invalid")
                else:
                    print(f"❌ Unexpected content type: {content_type}")
            else:
                print(f"❌ RSS feed failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ RSS feed error: {e}")
        
        # Test listing users
        print("\n4. Testing user listing...")
        try:
            response = await client.get(f"{base_url}/users")
            if response.status_code == 200:
                users = response.json()
                print(f"✅ Found {len(users)} registered users:")
                for user in users:
                    print(f"   - {user['username']} ({user['display_name']})")
            else:
                print(f"❌ User listing failed: {response.status_code}")
        except Exception as e:
            print(f"❌ User listing error: {e}")
        
        # Test feeds listing
        print("\n5. Testing feeds listing...")
        try:
            response = await client.get(f"{base_url}/feeds")
            if response.status_code == 200:
                feeds_data = response.json()
                print(f"✅ Found {len(feeds_data['feeds'])} available feeds:")
                for feed in feeds_data['feeds']:
                    print(f"   - {feed['username']}: {feed['feed_url']}")
            else:
                print(f"❌ Feeds listing failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Feeds listing error: {e}")
        
        print("\n" + "=" * 50)
        print("🏁 API testing completed!")


if __name__ == "__main__":
    print("Starting API tests...")
    print("Make sure the service is running on http://localhost:8000")
    print("You can start it with: docker-compose up -d")
    print()
    
    asyncio.run(test_api()) 
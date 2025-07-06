import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class Cache:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
        
    async def connect(self):
        """Connect to Redis"""
        if not self.client:
            self.client = redis.from_url(self.redis_url)
            await self.client.ping()
            logger.info("Connected to Redis")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            await self.client.close()
            self.client = None
            logger.info("Disconnected from Redis")
    
    async def _ensure_connected(self):
        """Ensure Redis connection is established"""
        if not self.client:
            await self.connect()
    
    async def get_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Get cached user data"""
        await self._ensure_connected()
        try:
            data = await self.client.get(f"user:{username}")
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Error getting user data for {username}: {e}")
        return None
    
    async def set_user_data(self, username: str, data: Dict[str, Any], ttl: int = 3600):
        """Cache user data with TTL"""
        await self._ensure_connected()
        try:
            await self.client.setex(f"user:{username}", ttl, json.dumps(data))
            logger.debug(f"Cached user data for {username}")
        except Exception as e:
            logger.error(f"Error caching user data for {username}: {e}")
    
    async def get_book_list(self, username: str) -> Optional[Dict[str, Any]]:
        """Get cached book list for a user"""
        await self._ensure_connected()
        try:
            data = await self.client.get(f"books:{username}")
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Error getting book list for {username}: {e}")
        return None
    
    async def set_book_list(self, username: str, data: Dict[str, Any], ttl: int = 1800):
        """Cache book list with TTL (30 minutes)"""
        await self._ensure_connected()
        try:
            await self.client.setex(f"books:{username}", ttl, json.dumps(data))
            logger.debug(f"Cached book list for {username}")
        except Exception as e:
            logger.error(f"Error caching book list for {username}: {e}")
    
    async def get_all_users(self) -> List[str]:
        """Get all registered usernames from persistent storage"""
        await self._ensure_connected()
        try:
            # Get all keys that match the pattern "user:*"
            keys = await self.client.keys("user:*")
            # Extract usernames from keys (remove "user:" prefix)
            usernames = [key.decode('utf-8').replace("user:", "") for key in keys]
            logger.info(f"Retrieved {len(usernames)} users from persistent storage")
            return usernames
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    async def store_user_persistent(self, username: str, user_data: Dict[str, Any]):
        """Store user data persistently (no TTL)"""
        await self._ensure_connected()
        try:
            # Store user data without expiration for persistence
            await self.client.set(f"user:{username}", json.dumps(user_data))
            logger.info(f"Stored user {username} persistently")
        except Exception as e:
            logger.error(f"Error storing user {username} persistently: {e}")
    
    async def remove_user(self, username: str):
        """Remove user data from cache and persistent storage"""
        await self._ensure_connected()
        try:
            # Remove both cached and persistent user data
            await self.client.delete(f"user:{username}")
            await self.client.delete(f"books:{username}")
            logger.info(f"Removed user {username} from storage")
        except Exception as e:
            logger.error(f"Error removing user {username}: {e}")
    
    async def clear_cache(self):
        """Clear all cached data (but keep persistent user data)"""
        await self._ensure_connected()
        try:
            # Only clear book lists, keep user registrations
            keys = await self.client.keys("books:*")
            if keys:
                await self.client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cached book lists")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}") 
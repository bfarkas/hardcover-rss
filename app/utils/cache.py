import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import redis.asyncio as redis
from ..scraper.models import UserBookList
from ..config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis-based cache manager for user book lists"""
    
    def __init__(self):
        self.redis_client = None
        self.ttl = settings.cache_ttl
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(settings.redis_url)
            await self.redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Fallback to in-memory cache
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
    
    def _get_cache_key(self, username: str) -> str:
        """Generate cache key for user"""
        return f"hardcover:user:{username}:want_to_read"
    
    async def get_user_book_list(self, username: str) -> Optional[UserBookList]:
        """Get user book list from cache"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._get_cache_key(username)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                
                # Convert ISO strings back to datetime objects
                if data.get('last_updated'):
                    dt = datetime.fromisoformat(data['last_updated'])
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    data['last_updated'] = dt
                
                for book in data.get('books', []):
                    if book.get('date_added'):
                        dt = datetime.fromisoformat(book['date_added'])
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        book['date_added'] = dt
                
                return UserBookList(**data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached data for {username}: {e}")
            return None
    
    def _serialize_datetimes(self, obj):
        if isinstance(obj, dict):
            return {k: self._serialize_datetimes(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_datetimes(i) for i in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

    async def set_user_book_list(self, username: str, user_book_list: UserBookList):
        """Cache user book list"""
        if not self.redis_client:
            return
        
        try:
            cache_key = self._get_cache_key(username)
            data = user_book_list.model_dump()
            data = self._serialize_datetimes(data)
            
            await self.redis_client.setex(
                cache_key,
                self.ttl,
                json.dumps(data)
            )
            logger.info(f"Cached book list for {username}")
            
        except Exception as e:
            logger.error(f"Error caching data for {username}: {e}")
    
    async def invalidate_user_cache(self, username: str):
        """Invalidate cache for a specific user"""
        if not self.redis_client:
            return
        
        try:
            cache_key = self._get_cache_key(username)
            await self.redis_client.delete(cache_key)
            logger.info(f"Invalidated cache for {username}")
            
        except Exception as e:
            logger.error(f"Error invalidating cache for {username}: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {"status": "not_connected"}
        
        try:
            info = await self.redis_client.info()
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed")
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "error": str(e)} 
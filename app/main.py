import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
import os

from .config.settings import settings
from .scraper.hardcover import HardcoverAPI
from .feeds.generator import RSSFeedGenerator
from .utils.cache import Cache
from .utils.scheduler import Scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
cache = Cache(settings.redis_url)
hardcover_api = HardcoverAPI()
feed_generator = RSSFeedGenerator()
scheduler = Scheduler()

# In-memory user storage (will be replaced by persistent storage)
users: dict = {}

class UserCreate(BaseModel):
    username: str
    display_name: Optional[str] = None

class UserResponse(BaseModel):
    username: str
    display_name: str
    enabled: bool
    feed_url: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Hardcover RSS service...")
    
    # Connect to Redis
    await cache.connect()
    
    # Load users from persistent storage
    await load_users_from_storage()
    
    # Start background scheduler
    scheduler.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Hardcover RSS service...")
    scheduler.stop()
    await cache.disconnect()

async def load_users_from_storage():
    """Load all registered users from persistent storage"""
    try:
        usernames = await cache.get_all_users()
        for username in usernames:
            user_data = await cache.get_user_data(username)
            if user_data:
                users[username] = user_data
                logger.info(f"Loaded user {username} from persistent storage")
        
        logger.info(f"Loaded {len(users)} users from persistent storage")
    except Exception as e:
        logger.error(f"Error loading users from storage: {e}")

app = FastAPI(
    title="Hardcover RSS Service",
    description="RSS feeds for Hardcover.app want-to-read lists",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Hardcover RSS",
        "version": "1.0.0",
        "users": len(users),
        "docs": "/docs"
    }

@app.get("/users", response_model=List[UserResponse])
async def list_users():
    """List all registered users"""
    return [
        UserResponse(
            username=username,
            display_name=user_data.get("display_name", username),
            enabled=user_data.get("enabled", True),
            feed_url=f"/feed/{username}"
        )
        for username, user_data in users.items()
    ]

@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    """Register a new user"""
    username = user.username.lower()
    
    if username in users:
        raise HTTPException(status_code=400, detail="User already registered")
    
    # Test if user exists on Hardcover
    try:
        book_list = await hardcover_api.get_user_want_to_read(username)
        if not book_list:
            raise HTTPException(status_code=404, detail="User not found on Hardcover")
        
        # Store user data
        user_data = {
            "username": username,
            "display_name": user.display_name or username,
            "enabled": True,
            "created_at": asyncio.get_event_loop().time()
        }
        
        users[username] = user_data
        
        # Store user persistently
        await cache.store_user_persistent(username, user_data)
        
        logger.info(f"Registered user: {username}")
        
        return UserResponse(
            username=username,
            display_name=user_data["display_name"],
            enabled=user_data["enabled"],
            feed_url=f"/feed/{username}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user {username}: {e}")
        raise HTTPException(status_code=500, detail="Failed to register user")

@app.delete("/users/{username}")
async def delete_user(username: str):
    """Remove a user"""
    username = username.lower()
    
    if username not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Remove from memory and persistent storage
    del users[username]
    await cache.remove_user(username)
    
    logger.info(f"Removed user: {username}")
    return {"message": "User removed"}

@app.get("/feed/{username}")
async def get_user_feed(username: str):
    """Get RSS feed for a user's want-to-read list"""
    username = username.lower()
    
    if username not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = users[username]
    if not user_data.get("enabled", True):
        raise HTTPException(status_code=400, detail="User is disabled")
    
    try:
        # Try to get from cache first
        cached_data = await cache.get_book_list(username)
        if cached_data:
            logger.info(f"Serving cached feed for {username}")
            return Response(
                content=cached_data["feed_content"],
                media_type="application/rss+xml"
            )
        
        # Fetch fresh data
        book_list = await hardcover_api.get_user_want_to_read(username)
        if not book_list:
            raise HTTPException(status_code=404, detail="No books found")
        
        # Generate RSS feed
        feed_content = feed_generator.generate_feed(book_list)
        
        # Cache the feed
        await cache.set_book_list(username, {"feed_content": feed_content})
        
        logger.info(f"Generated fresh feed for {username} ({len(book_list.books)} books)")
        
        return Response(
            content=feed_content,
            media_type="application/rss+xml"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating feed for {username}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate feed")

@app.get("/list_rss/{username}")
async def get_user_feed_goodreads(username: str):
    """Goodreads-compatible RSS endpoint alias"""
    return await get_user_feed(username)

@app.post("/refresh/{username}")
async def refresh_user_feed(username: str, background_tasks: BackgroundTasks):
    """Refresh a user's feed (clear cache and regenerate)"""
    username = username.lower()
    
    if username not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Clear cache for this user
    await cache.client.delete(f"books:{username}")
    
    # Trigger background refresh
    background_tasks.add_task(refresh_user_background, username)
    
    return {"message": "Refresh initiated"}

async def refresh_user_background(username: str):
    """Background task to refresh user feed"""
    try:
        logger.info(f"Refreshing feed for {username}")
        book_list = await hardcover_api.get_user_want_to_read(username)
        if book_list:
            feed_content = feed_generator.generate_feed(book_list)
            await cache.set_book_list(username, {"feed_content": feed_content})
            logger.info(f"Refreshed feed for {username}")
    except Exception as e:
        logger.error(f"Error refreshing feed for {username}: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        await cache._ensure_connected()
        return {
            "status": "healthy",
            "users": len(users),
            "redis": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        } 
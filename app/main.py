import logging
import asyncio
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import Response, PlainTextResponse
from pydantic import BaseModel
import uvicorn

from .config import settings
from .scraper import HardcoverAPI, User, UserBookList
from .feeds import RSSFeedGenerator
from .utils import CacheManager, Scheduler

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Hardcover RSS Service",
    description="RSS feeds for Hardcover.app want-to-read lists",
    version="1.0.0"
)

# Global instances
hardcover_api = HardcoverAPI()
cache_manager = CacheManager()
scheduler = Scheduler()
rss_generator = RSSFeedGenerator()

# In-memory user storage (in production, use a database)
users: Dict[str, User] = {}


class UserCreate(BaseModel):
    username: str
    display_name: str = None


class UserResponse(BaseModel):
    username: str
    display_name: str
    enabled: bool
    feed_url: str


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Hardcover RSS Service")
    
    # Connect to cache
    await cache_manager.connect()
    
    # Start scheduler
    scheduler.start()
    
    # Add refresh job
    scheduler.add_refresh_job("refresh_all_users", refresh_all_users)
    
    logger.info("Service started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Hardcover RSS Service")
    
    # Stop scheduler
    scheduler.stop()
    
    # Disconnect from cache
    await cache_manager.disconnect()
    
    logger.info("Service shutdown complete")


async def refresh_user_data(username: str) -> UserBookList:
    """Refresh data for a specific user"""
    try:
        # Get user info if not in memory
        if username not in users:
            user_info = await hardcover_api.get_user_info(username)
            if not user_info:
                raise HTTPException(status_code=404, detail=f"User {username} not found")
            users[username] = user_info
        
        # Fetch latest data from Hardcover API
        user_book_list = await hardcover_api.get_user_want_to_read(username)
        if not user_book_list:
            raise HTTPException(status_code=404, detail=f"No data found for user {username}")
        
        # Cache the data
        await cache_manager.set_user_book_list(username, user_book_list)
        
        logger.info(f"Refreshed data for user {username}")
        return user_book_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing data for {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Error refreshing data for {username}")


async def refresh_all_users():
    """Refresh data for all registered users"""
    logger.info("Starting refresh for all users")
    
    for username in list(users.keys()):
        try:
            await refresh_user_data(username)
            # Small delay to avoid overwhelming the API
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Failed to refresh user {username}: {e}")
    
    logger.info("Completed refresh for all users")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    cache_stats = await cache_manager.get_cache_stats()
    jobs = scheduler.get_jobs()
    
    return {
        "status": "healthy",
        "cache": cache_stats,
        "scheduler_jobs": len(jobs),
        "registered_users": len(users)
    }


@app.post("/users", response_model=UserResponse)
async def add_user(user_data: UserCreate):
    """Add a new user to track"""
    try:
        # Verify user exists on Hardcover
        user_info = await hardcover_api.get_user_info(user_data.username)
        if not user_info:
            raise HTTPException(status_code=404, detail=f"User {user_data.username} not found on Hardcover")
        
        # Update display name if provided
        if user_data.display_name:
            user_info.display_name = user_data.display_name
        
        # Store user
        users[user_data.username] = user_info
        
        # Fetch initial data
        await refresh_user_data(user_data.username)
        
        logger.info(f"Added user {user_data.username}")
        
        return UserResponse(
            username=user_info.username,
            display_name=user_info.display_name,
            enabled=user_info.enabled,
            feed_url=f"/feed/{user_info.username}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding user {user_data.username}: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding user {user_data.username}")


@app.get("/users", response_model=List[UserResponse])
async def list_users():
    """List all registered users"""
    return [
        UserResponse(
            username=user.username,
            display_name=user.display_name,
            enabled=user.enabled,
            feed_url=f"/feed/{user.username}"
        )
        for user in users.values()
    ]


@app.delete("/users/{username}")
async def remove_user(username: str):
    """Remove a user from tracking"""
    if username not in users:
        raise HTTPException(status_code=404, detail=f"User {username} not found")
    
    # Remove from memory
    del users[username]
    
    # Invalidate cache
    await cache_manager.invalidate_user_cache(username)
    
    logger.info(f"Removed user {username}")
    
    return {"message": f"User {username} removed successfully"}


@app.get("/feed/{username}")
async def get_user_feed(username: str):
    """Get RSS feed for a specific user"""
    try:
        # Check if user is registered
        if username not in users:
            raise HTTPException(status_code=404, detail=f"User {username} not found")
        
        # Try to get from cache first
        user_book_list = await cache_manager.get_user_book_list(username)
        
        # If not in cache, fetch fresh data
        if not user_book_list:
            user_book_list = await refresh_user_data(username)
        
        # Generate RSS feed
        rss_content = rss_generator.generate_feed(user_book_list)
        
        if not rss_content:
            raise HTTPException(status_code=500, detail="Error generating RSS feed")
        
        return Response(
            content=rss_content,
            media_type="application/rss+xml",
            headers={
                "Cache-Control": f"public, max-age={settings.cache_ttl}",
                "Content-Type": "application/rss+xml; charset=utf-8"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating feed for {username}: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating feed for {username}")


@app.post("/refresh/{username}")
async def refresh_user_feed(username: str, background_tasks: BackgroundTasks):
    """Manually refresh a user's feed"""
    if username not in users:
        raise HTTPException(status_code=404, detail=f"User {username} not found")
    
    # Add refresh task to background
    background_tasks.add_task(refresh_user_data, username)
    
    return {"message": f"Refresh started for user {username}"}


@app.post("/refresh")
async def refresh_all_feeds(background_tasks: BackgroundTasks):
    """Manually refresh all user feeds"""
    if not users:
        raise HTTPException(status_code=400, detail="No users registered")
    
    # Add refresh task to background
    background_tasks.add_task(refresh_all_users)
    
    return {"message": "Refresh started for all users"}


@app.get("/feeds")
async def list_feeds():
    """List all available feeds"""
    feeds = []
    for username, user in users.items():
        feeds.append({
            "username": username,
            "display_name": user.display_name,
            "feed_url": f"/feed/{username}",
            "enabled": user.enabled
        })
    
    return {"feeds": feeds}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    ) 
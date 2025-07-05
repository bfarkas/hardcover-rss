from pydantic_settings import BaseSettings
from typing import List, Optional
import os


def get_default_redis_url() -> str:
    """Get the default Redis URL based on the environment."""
    # Check if we're running in Docker (common Docker environment variables)
    if os.getenv("DOCKER_CONTAINER") or os.getenv("KUBERNETES_SERVICE_HOST"):
        return "redis://redis:6379"
    
    # Check if we're running in a Docker Compose environment
    if os.getenv("REDIS_URL"):
        return os.getenv("REDIS_URL")
    
    # Default to localhost for local development
    return "redis://localhost:6379"


class Settings(BaseSettings):
    # Hardcover API settings
    hardcover_api_token: str
    hardcover_api_url: str = "https://api.hardcover.app/v1/graphql"
    
    # Application settings
    refresh_interval: int = 3600  # seconds
    cache_ttl: int = 1800  # seconds
    log_level: str = "INFO"
    
    # Redis settings
    redis_url: str = get_default_redis_url()
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 
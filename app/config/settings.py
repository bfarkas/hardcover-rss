from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Hardcover API settings
    hardcover_api_token: str
    hardcover_api_url: str = "https://api.hardcover.app/v1/graphql"
    
    # Application settings
    refresh_interval: int = 3600  # seconds
    cache_ttl: int = 1800  # seconds
    log_level: str = "INFO"
    
    # Redis settings
    redis_url: str = "redis://localhost:6379"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Book(BaseModel):
    """Book model representing a book from Hardcover API"""
    id: str
    title: str
    author: str
    cover_image_url: Optional[str] = None
    description: Optional[str] = None
    isbn: Optional[str] = None
    published_year: Optional[int] = None
    page_count: Optional[int] = None
    average_rating: Optional[float] = None
    date_added: Optional[datetime] = None
    user_rating: Optional[int] = None
    user_review: Optional[str] = None


class User(BaseModel):
    """User model for managing user configurations"""
    id: str
    username: str
    display_name: str
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)


class UserBookList(BaseModel):
    """Model for a user's book list"""
    user: User
    books: List[Book]
    last_updated: datetime = Field(default_factory=datetime.now)


class HardcoverAPIResponse(BaseModel):
    """Generic response wrapper for Hardcover API"""
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[Dict[str, Any]]] = None 
import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from .models import Book, User, UserBookList
from ..config import settings

logger = logging.getLogger(__name__)


class HardcoverAPI:
    """Client for interacting with Hardcover GraphQL API"""
    
    def __init__(self):
        self.api_url = settings.hardcover_api_url
        self.api_token = settings.hardcover_api_token
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
    
    async def get_user_want_to_read(self, username: str) -> Optional[UserBookList]:
        """Fetch a user's 'want to read' list from the correct bookshelf"""
        try:
            # GraphQL query to get user's want to read bookshelf and its books
            query = """
            query GetUserWantToRead($username: citext!) {
                users(where: {username: {_eq: $username}}, limit: 1) {
                    id
                    username
                    bookshelves(where: {slug: {_eq: "want-to-read"}}, limit: 1) {
                        id
                        slug
                        name
                        bookshelf_books(order_by: {created_at: desc}) {
                            id
                            created_at
                            book {
                                id
                                title
                                description
                                authors {
                                    name
                                }
                                # Add more fields as needed
                            }
                        }
                    }
                }
            }
            """
            
            variables = {"username": username}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json={"query": query, "variables": variables},
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"API request failed: {response.status_code}")
                    return None
                
                data = response.json()
                
                if "errors" in data:
                    logger.error(f"GraphQL errors: {data['errors']}")
                    return None
                
                users_data = data.get("data", {}).get("users", [])
                if not users_data:
                    logger.warning(f"User not found: {username}")
                    return None
                
                user_data = users_data[0]  # Get the first user
                
                # Create User object
                user = User(
                    id=str(user_data["id"]),
                    username=user_data["username"],
                    display_name=user_data.get("username", username)
                )
                
                # Find the want-to-read bookshelf
                books = []
                bookshelves = user_data.get("bookshelves", [])
                if bookshelves:
                    bookshelf = bookshelves[0]
                    for shelf_book in bookshelf.get("bookshelf_books", []):
                        book_info = shelf_book.get("book", {})
                        book = Book(
                            id=str(book_info.get("id", shelf_book["id"])),
                            title=book_info.get("title"),
                            author=", ".join(a["name"] for a in book_info.get("authors", [])),
                            cover_image_url=None,
                            description=book_info.get("description"),
                            isbn=None,
                            published_year=None,
                            page_count=None,
                            average_rating=None,
                            date_added=datetime.fromisoformat(shelf_book["created_at"].replace("Z", "+00:00")) if shelf_book.get("created_at") else None,
                            user_rating=None,
                            user_review=None
                        )
                        books.append(book)
                
                return UserBookList(user=user, books=books)
                
        except Exception as e:
            logger.error(f"Error fetching want to read list for {username}: {e}")
            return None
    
    async def get_user_info(self, username: str) -> Optional[User]:
        """Get basic user information"""
        try:
            query = """
            query GetUserInfo($username: citext!) {
                users(where: {username: {_eq: $username}}, limit: 1) {
                    id
                    username
                }
            }
            """
            
            variables = {"username": username}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json={"query": query, "variables": variables},
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"API request failed: {response.status_code}")
                    return None
                
                data = response.json()
                logger.info(f"GraphQL response for user {username}: {data}")
                
                if "errors" in data:
                    logger.error(f"GraphQL errors: {data['errors']}")
                    return None
                
                users_data = data.get("data", {}).get("users", [])
                
                if not users_data:
                    logger.warning(f"User not found: {username}")
                    return None
                
                user_data = users_data[0]  # Get the first user
                
                return User(
                    id=str(user_data["id"]),
                    username=user_data["username"],
                    display_name=user_data.get("username", username)  # Use username as display name for now
                )
                
        except Exception as e:
            logger.error(f"Error fetching user info for {username}: {e}")
            return None 
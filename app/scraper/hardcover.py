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
        # Try XHR approach first (more reliable for want-to-read shelf)
        result = await self.fetch_user_want_to_read_xhr(username)
        if result:
            logger.info(f"Successfully fetched want-to-read list for {username} via XHR ({len(result.books)} books)")
            return result
        
        # Fallback to GraphQL approach if XHR fails
        logger.warning(f"XHR approach failed for {username}, trying GraphQL fallback")
        try:
            # GraphQL query to get user_books with only valid fields
            query = """
            query GetUserAllFields($username: citext!) {
                users(where: {username: {_eq: $username}}, limit: 1) {
                    id
                    username
                    user_books(order_by: {created_at: desc}) {
                        id
                        created_at
                        book {
                            id
                            title
                            description
                        }
                    }
                }
            }
            """
            
            variables = {"username": username}
            response = await self.client.post(
                self.graphql_url,
                json={"query": query, "variables": variables},
                headers=self.headers,
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error(f"GraphQL request failed: {response.status_code}")
                return None
                
            data = response.json()
            
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return None
                
            users = data.get("data", {}).get("users", [])
            if not users:
                logger.error(f"User {username} not found")
                return None
                
            user_data = users[0]
            user_books = user_data.get("user_books", [])
            
            # Build User and Book objects
            user = User(
                id=username,
                username=username,
                display_name=username
            )
            
            books = []
            for user_book in user_books:
                book_data = user_book.get("book", {})
                book = Book(
                    id=str(book_data.get("id")),
                    title=book_data.get("title", ""),
                    author="",  # Not available in this query
                    cover_image_url=None,
                    description=book_data.get("description"),
                    isbn=None,
                    published_year=None,
                    page_count=None,
                    average_rating=None,
                    date_added=None,
                    user_rating=None,
                    user_review=None
                )
                books.append(book)
            
            logger.info(f"Successfully fetched user books for {username} via GraphQL ({len(books)} books)")
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

    async def fetch_user_want_to_read_xhr(self, username: str) -> Optional[UserBookList]:
        """Fetch a user's 'want to read' list from the Hardcover web XHR endpoint."""
        import re, html
        try:
            url = f"https://hardcover.app/@{username}/books/want-to-read"
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; HardcoverRSS/1.0)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": f"https://hardcover.app/@{username}",
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30.0)
                if response.status_code != 200:
                    logger.error(f"XHR request failed: {response.status_code}")
                    return None
                # Extract data-page attribute from <div id="app" data-page="...">
                m = re.search(r'<div id="app"[^>]*data-page="([^"]+)"', response.text)
                if not m:
                    logger.error("Could not find data-page attribute in XHR response")
                    return None
                data_page_raw = m.group(1)
                data_page_json = html.unescape(data_page_raw)
                import json
                data = json.loads(data_page_json)
                # Try to extract books from letterbooks or rootState.books.books
                books_list = None
                if "props" in data and "letterbooks" in data["props"]:
                    letterbooks_obj = data["props"]["letterbooks"]
                    if isinstance(letterbooks_obj, dict) and "letterbooks" in letterbooks_obj:
                        books_list = letterbooks_obj["letterbooks"]
                    elif isinstance(letterbooks_obj, list):
                        books_list = letterbooks_obj
                elif "letterbooks" in data:
                    letterbooks_obj = data["letterbooks"]
                    if isinstance(letterbooks_obj, dict) and "letterbooks" in letterbooks_obj:
                        books_list = letterbooks_obj["letterbooks"]
                    elif isinstance(letterbooks_obj, list):
                        books_list = letterbooks_obj
                if not books_list:
                    logger.error("No books found in XHR response (letterbooks missing)")
                    return None
                # Build User and Book objects
                user = User(
                    id=username,
                    username=username,
                    display_name=username
                )
                books = []
                for entry in books_list:
                    book_info = entry["book"] if isinstance(entry, dict) and "book" in entry else entry
                    book = Book(
                        id=str(book_info.get("id")),
                        title=book_info.get("title", ""),
                        author=book_info.get("author", ""),
                        cover_image_url=book_info.get("cover", {}).get("url") if book_info.get("cover") else None,
                        description=book_info.get("description"),
                        isbn=book_info.get("isbn"),
                        published_year=book_info.get("release_year"),
                        page_count=book_info.get("pages"),
                        average_rating=float(book_info["rating"]) if book_info.get("rating") else None,
                        date_added=None,
                        user_rating=None,
                        user_review=None
                    )
                    books.append(book)
                return UserBookList(user=user, books=books)
        except Exception as e:
            logger.error(f"Error fetching want to read list via XHR for {username}: {e}")
            return None 
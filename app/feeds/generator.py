from feedgen.feed import FeedGenerator
from typing import List
from datetime import datetime, timezone
import logging
from ..scraper.models import UserBookList, Book

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RSSFeedGenerator:
    """Generate RSS feeds in Goodreads format"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or "http://localhost:8000"
    
    def generate_feed(self, user_book_list: UserBookList) -> str:
        """Generate RSS feed for a user's want to read list"""
        try:
            fg = FeedGenerator()
            fg.load_extension('dc')
            
            # Set feed metadata
            fg.title(f"{user_book_list.user.display_name}'s bookshelf: to-read")
            fg.description(f"{user_book_list.user.display_name}'s bookshelf: to-read")
            fg.link(href=f"{self.base_url}/feed/{user_book_list.user.username}")
            fg.language('en-US')
            print(f"fg.lastBuildDate: {datetime.now()} (type: {type(datetime.now())}, tzinfo: {datetime.now().tzinfo})")
            fg.lastBuildDate(datetime.now(timezone.utc))
            fg.ttl(60)  # 1 hour cache
            
            # Add feed image (similar to Goodreads)
            fg.image(
                title=f"{user_book_list.user.display_name}'s bookshelf: to-read",
                url="https://hardcover.app/favicon.ico",
                link=f"{self.base_url}/feed/{user_book_list.user.username}"
            )
            
            # Add entries for each book
            for book in user_book_list.books:
                fe = fg.add_entry()
                
                # Entry title
                fe.title(book.title)
                
                # Entry link (to Hardcover book page)
                fe.link(href=f"https://hardcover.app/book/{book.id}")
                
                # Entry description (similar to Goodreads format)
                description = self._generate_book_description(book, user_book_list.user)
                fe.description(description)
                
                # Entry ID
                fe.id(book.id)
                
                # Entry published date
                if book.date_added:
                    dt = book.date_added
                else:
                    dt = datetime.now()
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                print(f"fe.published: {dt} (type: {type(dt)}, tzinfo: {dt.tzinfo})")
                fe.published(dt)
                
                # Entry updated date
                now_dt = datetime.now(timezone.utc)
                print(f"fg.updated: {datetime.now()} (type: {type(datetime.now())}, tzinfo: {datetime.now().tzinfo})")
                fe.updated(datetime.now(timezone.utc))
                
                # Add custom fields similar to Goodreads
                fe.dc.dc_creator(book.author)
                fe.dc.dc_subject("to-read")
                
                # Add custom tags for additional metadata
                if book.isbn:
                    fe.dc.dc_identifier(book.isbn)
                if book.published_year:
                    fe.dc.dc_date(f"{book.published_year}-01-01")
            
            return fg.rss_str(pretty=True).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error generating RSS feed for {user_book_list.user.username}: {e}")
            return ""
    
    def _generate_book_description(self, book: Book, user) -> str:
        """Generate book description in Goodreads format"""
        description_parts = []
        
        # Book title and author
        description_parts.append(f"<![CDATA[{book.title}]]>")
        
        # Book ID (similar to Goodreads)
        description_parts.append(f"{book.id}")
        
        # Book description
        if book.description:
            description_parts.append(f"<![CDATA[{book.description}]]>")
        
        # Book metadata
        if book.page_count:
            description_parts.append(f"{book.page_count}")
        
        # Author
        description_parts.append(f"{book.author}")
        
        # ISBN
        if book.isbn:
            description_parts.append(f"{book.isbn}")
        
        # User info
        description_parts.append(f"{user.display_name}")
        
        # User rating (0 for want to read)
        description_parts.append("0")
        
        # Shelf
        description_parts.append("to-read")
        
        # Average rating
        if book.average_rating:
            description_parts.append(f"{book.average_rating:.2f}")
        else:
            description_parts.append("0.00")
        
        # Published year
        if book.published_year:
            description_parts.append(f"{book.published_year}")
        else:
            description_parts.append("")
        
        # Book title again (Goodreads format)
        description_parts.append(f"{book.title}")
        
        # Author again
        description_parts.append(f"author: {book.author}")
        
        # User name
        description_parts.append(f"name: {user.display_name}")
        
        # Average rating
        if book.average_rating:
            description_parts.append(f"average rating: {book.average_rating:.2f}")
        else:
            description_parts.append("average rating: 0.00")
        
        # Published year
        if book.published_year:
            description_parts.append(f"book published: {book.published_year}")
        else:
            description_parts.append("book published: ")
        
        # User rating
        description_parts.append("rating: 0")
        
        # Read at (empty for want to read)
        description_parts.append("read at: ")
        
        # Date added
        if book.date_added:
            description_parts.append(f"date added: {book.date_added.strftime('%Y/%m/%d')}")
        else:
            description_parts.append("date added: ")
        
        # Shelves
        description_parts.append("shelves: to-read")
        
        # Review (empty for want to read)
        description_parts.append("review: ")
        
        return " ".join(description_parts) 

    def _format_date(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat() 
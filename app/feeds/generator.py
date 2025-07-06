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
                fe.dc.dc_creator(book.author_name or book.author)
                fe.dc.dc_subject("to-read")
                
                # Add custom tags for additional metadata
                if book.published_year:
                    fe.dc.dc_date(f"{book.published_year}-01-01")
                
                # Add custom elements to match Goodreads structure
                # We'll need to post-process the XML to add these custom tags
                # For now, we'll store them in the feed entry for later processing
                fe._custom_data = {
                    'book_id': book.book_id,
                    'book_image_url': book.cover_image_url,
                    'book_small_image_url': book.cover_image_url,
                    'book_medium_image_url': book.cover_image_url,
                    'book_large_image_url': book.cover_image_url,
                    'book_description': book.book_description,
                    'author_name': book.author_name,
                    'isbn': book.isbn,
                    'user_name': user_book_list.user.display_name,
                    'user_rating': '0',
                    'user_read_at': '',
                    'user_date_added': book.date_added.strftime('%a, %d %b %Y %H:%M:%S %z') if book.date_added else datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z'),
                    'user_date_created': book.date_added.strftime('%a, %d %b %Y %H:%M:%S %z') if book.date_added else datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z'),
                    'user_shelves': 'to-read',
                    'user_review': '',
                    'average_rating': f"{book.average_rating:.2f}" if book.average_rating else "0.00",
                    'book_published': str(book.published_year) if book.published_year else '',
                    'num_pages': str(book.page_count) if book.page_count else ''
                }
            
            # Generate the RSS XML
            rss_xml = fg.rss_str(pretty=True).decode('utf-8')
            
            # Post-process to add custom elements
            rss_xml = self._add_custom_elements(rss_xml, fg.entry())
            
            return rss_xml
            
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
        
        # Book description (use book_description if available, fallback to description)
        book_desc = book.book_description or book.description
        if book_desc:
            description_parts.append(f"<![CDATA[{book_desc}]]>")
        
        # Book metadata
        if book.page_count:
            description_parts.append(f"{book.page_count}")
        
        # Author (use author_name if available, fallback to author)
        author_name = book.author_name or book.author
        description_parts.append(f"{author_name}")
        
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
        
        # Author again (use author_name if available)
        description_parts.append(f"author: {author_name}")
        
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

    def _add_custom_elements(self, rss_xml: str, entries) -> str:
        """Add custom elements to the RSS XML to match Goodreads structure"""
        import re
        
        # Split the XML into parts
        parts = rss_xml.split('</item>')
        
        if len(parts) <= 1:
            return rss_xml
        
        # Process each item
        for i, entry in enumerate(entries):
            if hasattr(entry, '_custom_data') and entry._custom_data:
                custom_data = entry._custom_data
                
                # Create custom elements XML with proper indentation (2 spaces to match RSS structure)
                custom_elements = []
                
                if custom_data.get('book_id'):
                    custom_elements.append(f'  <book_id>{custom_data["book_id"]}</book_id>')
                
                if custom_data.get('book_image_url'):
                    custom_elements.append(f'  <book_image_url><![CDATA[{custom_data["book_image_url"]}]]></book_image_url>')
                    custom_elements.append(f'  <book_small_image_url><![CDATA[{custom_data["book_small_image_url"]}]]></book_small_image_url>')
                    custom_elements.append(f'  <book_medium_image_url><![CDATA[{custom_data["book_medium_image_url"]}]]></book_medium_image_url>')
                    custom_elements.append(f'  <book_large_image_url><![CDATA[{custom_data["book_large_image_url"]}]]></book_large_image_url>')
                
                if custom_data.get('book_description'):
                    custom_elements.append(f'  <book_description><![CDATA[{custom_data["book_description"]}]]></book_description>')
                
                if custom_data.get('book_id'):
                    custom_elements.append(f'  <book id="{custom_data["book_id"]}">')
                    if custom_data.get('num_pages'):
                        custom_elements.append(f'    <num_pages>{custom_data["num_pages"]}</num_pages>')
                    custom_elements.append('  </book>')
                
                if custom_data.get('author_name'):
                    custom_elements.append(f'  <author_name>{custom_data["author_name"]}</author_name>')
                
                if custom_data.get('isbn'):
                    custom_elements.append(f'  <isbn>{custom_data["isbn"]}</isbn>')
                
                if custom_data.get('user_name'):
                    custom_elements.append(f'  <user_name>{custom_data["user_name"]}</user_name>')
                
                custom_elements.append(f'  <user_rating>{custom_data.get("user_rating", "0")}</user_rating>')
                custom_elements.append(f'  <user_read_at>{custom_data.get("user_read_at", "")}</user_read_at>')
                
                if custom_data.get('user_date_added'):
                    custom_elements.append(f'  <user_date_added><![CDATA[{custom_data["user_date_added"]}]]></user_date_added>')
                
                if custom_data.get('user_date_created'):
                    custom_elements.append(f'  <user_date_created><![CDATA[{custom_data["user_date_created"]}]]></user_date_created>')
                
                custom_elements.append(f'  <user_shelves>{custom_data.get("user_shelves", "to-read")}</user_shelves>')
                custom_elements.append(f'  <user_review>{custom_data.get("user_review", "")}</user_review>')
                
                if custom_data.get('average_rating'):
                    custom_elements.append(f'  <average_rating>{custom_data["average_rating"]}</average_rating>')
                
                if custom_data.get('book_published'):
                    custom_elements.append(f'  <book_published>{custom_data["book_published"]}</book_published>')
                
                # Insert custom elements before </item> with proper spacing
                if i < len(parts) - 1:  # Not the last part
                    # Add custom elements with proper spacing and indentation
                    parts[i] = parts[i] + '\n' + '\n'.join(custom_elements)
        
        # Rejoin the XML
        return '</item>'.join(parts) 
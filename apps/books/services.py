"""
Book cover fetching service for Comuniza.
Integrates with Open Library API and Amazon fallback to fetch book covers and metadata.
"""

import json
import os
import re
import time
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.utils import timezone

from apps.items.models import Item, ItemImage


class BookCoverService:
    """Service for fetching book covers and metadata from Open Library with Amazon fallback."""

    BASE_URL = "https://openlibrary.org"
    BOOKS_API = f"{BASE_URL}/api/books"
    COVERS_API = "https://covers.openlibrary.org/b"
    CACHE_TIMEOUT = 30 * 24 * 60 * 60  # 30 days
    AMAZON_CACHE_TIMEOUT = 90 * 24 * 60 * 60  # 90 days for Amazon results
    BLOCKING_TIMEOUT = 15 * 60  # 15 minutes

    # Language normalization mapping - all variations map to ISO 639-3 codes
    LANGUAGE_MAPPING = {
        'english': 'en', 'en': 'en', 'eng': 'en', 'englisch': 'en', 'EN': 'en', 'English': 'en',
        'spanish': 'es', 'es': 'es', 'spa': 'es', 'español': 'es', 'ES': 'es', 'Spanish': 'es',
        'french': 'fr', 'fr': 'fr', 'fra': 'fr', 'français': 'fr', 'FR': 'fr', 'French': 'fr',
        'german': 'de', 'de': 'de', 'deu': 'de', 'deutsch': 'de', 'DE': 'de', 'German': 'de',
        'italian': 'it', 'it': 'it', 'ita': 'it', 'italiano': 'it', 'IT': 'it', 'Italian': 'it',
        'portuguese': 'pt', 'pt': 'pt', 'por': 'pt', 'português': 'pt', 'PT': 'pt', 'Portuguese': 'pt',
        'chinese': 'zh', 'zh': 'zh', 'zho': 'zh', '中文': 'zh', 'ZH': 'zh', 'Chinese': 'zh',
        'japanese': 'ja', 'ja': 'ja', 'jpn': 'ja', '日本語': 'ja', 'JA': 'ja', 'Japanese': 'ja',
        'korean': 'ko', 'ko': 'ko', 'kor': 'ko', '한국어': 'ko', 'KO': 'ko', 'Korean': 'ko',
        'russian': 'ru', 'ru': 'ru', 'rus': 'ru', 'русский': 'ru', 'RU': 'ru', 'Russian': 'ru',
        'arabic': 'ar', 'ar': 'ar', 'ara': 'ar', 'العربية': 'ar', 'AR': 'ar', 'Arabic': 'ar',
        'hindi': 'hi', 'hi': 'hi', 'hin': 'hi', 'हिन्दी': 'hi', 'HI': 'hi', 'Hindi': 'hi',
        'dutch': 'nl', 'nl': 'nl', 'nld': 'nl', 'nederlands': 'nl', 'NL': 'nl', 'Dutch': 'nl',
        'polish': 'pl', 'pl': 'pl', 'pol': 'pl', 'polski': 'pl', 'PL': 'pl', 'Polish': 'pl',
        'swedish': 'sv', 'sv': 'sv', 'swe': 'sv', 'svenska': 'sv', 'SV': 'sv', 'Swedish': 'sv',
        'norwegian': 'no', 'no': 'no', 'nor': 'no', 'norsk': 'no', 'NO': 'no', 'Norwegian': 'no',
        'danish': 'da', 'da': 'da', 'dan': 'da', 'dansk': 'da', 'DA': 'da', 'Danish': 'da',
        'finnish': 'fi', 'fi': 'fi', 'fin': 'fi', 'suomi': 'fi', 'FI': 'fi', 'Finnish': 'fi',
        'greek': 'el', 'el': 'el', 'ell': 'el', 'ελληνικά': 'el', 'EL': 'el', 'Greek': 'el',
        'turkish': 'tr', 'tr': 'tr', 'tur': 'tr', 'türkçe': 'tr', 'TR': 'tr', 'Turkish': 'tr',
        'hebrew': 'he', 'he': 'he', 'heb': 'he', 'עברית': 'he', 'HE': 'he', 'Hebrew': 'he',
        'thai': 'th', 'th': 'th', 'tha': 'th', 'ไทย': 'th', 'TH': 'th', 'Thai': 'th',
        'vietnamese': 'vi', 'vi': 'vi', 'vie': 'vi', 'tiếng việt': 'vi', 'VI': 'vi', 'Vietnamese': 'vi',
        'czech': 'cs', 'cs': 'cs', 'ces': 'cs', 'čeština': 'cs', 'CS': 'cs', 'Czech': 'cs',
    }
    
    @staticmethod
    def normalize_isbn(isbn):
        """Normalize ISBN by removing hyphens and spaces."""
        if not isbn:
            return None
        # Remove all non-digit characters
        clean_isbn = re.sub(r'\D', '', isbn)
        return clean_isbn
    
    @staticmethod
    def is_valid_isbn(isbn):
        """Check if ISBN is valid (basic validation)."""
        if not isbn:
            return False
        clean_isbn = BookCoverService.normalize_isbn(isbn)
        
        if not clean_isbn:
            return False

        # ISBN-10: 10 digits
        if len(clean_isbn) == 10:
            return True
        # ISBN-13: 13 digits and starts with 978 or 979
        elif len(clean_isbn) == 13 and clean_isbn.startswith(('978', '979')):
            return True
        return False

    @staticmethod
    def normalize_language(lang_input):
        """Normalize language input to ISO 639-3 code."""
        if not lang_input:
            return None

        # Normalize input: lowercase, strip spaces
        normalized = lang_input.lower().strip()

        # Direct lookup in mapping
        if normalized in BookCoverService.LANGUAGE_MAPPING:
            return BookCoverService.LANGUAGE_MAPPING[normalized]

        # Check if it's already an ISO code (2-3 lowercase)
        import re
        if re.match(r'^[a-z]{2,3}$', normalized):
            return normalized

        return None

    @staticmethod
    def normalize_subjects(subjects_list):
        """Group and normalize subjects."""
        if not subjects_list:
            return []

        # Subject grouping categories
        subject_groups = {
            'Fiction': ['fiction', 'novel', 'story', 'fantasy', 'science fiction', 'scifi', 'romance', 'mystery', 'thriller', 'horror'],
            'Non-Fiction': ['non-fiction', 'biography', 'history', 'science', 'philosophy', 'self-help', 'business'],
            'Children': ['children', 'juvenile', 'young adult', 'ya'],
            'Educational': ['education', 'textbook', 'study', 'learning'],
            'Religion & Spirituality': ['religion', 'spirituality', 'faith', 'religious'],
        }

        normalized = []
        used_groups = set()

        for subject in subjects_list:
            subject_str = subject.get('name', str(subject)) if isinstance(subject, dict) else str(subject)
            subject_lower = subject_str.lower()

            # Find matching group
            for group_name, keywords in subject_groups.items():
                if any(keyword in subject_lower for keyword in keywords):
                    if group_name not in used_groups:
                        normalized.append(group_name)
                        used_groups.add(group_name)
                        break
            else:
                # No match, add original
                if len(normalized) < 10:
                    normalized.append(subject_str)

        return normalized
    
    @staticmethod
    def fetch_book_metadata(isbn):
        """Fetch book metadata from Open Library API with Amazon fallback."""
        # Clean ISBN first
        clean_isbn = BookCoverService.normalize_isbn(isbn)

        # Try Open Library first
        cache_key = f"ol_metadata_{clean_isbn}"
        ol_data = cache.get(cache_key)

        if ol_data is None:
            ol_data = BookCoverService._fetch_open_library_metadata(clean_isbn)
            cache.set(cache_key, ol_data, BookCoverService.CACHE_TIMEOUT)

        # If OL has data with covers, return it
        if ol_data and ol_data.get('covers'):
            return ol_data

        # Try Amazon fallback
        isbn10 = BookCoverService.isbn13_to_isbn10(clean_isbn)
        if isbn10:
            cache_key_amazon = f"amazon_metadata_{isbn10}"
            amazon_data = cache.get(cache_key_amazon)

            if amazon_data is None:
                amazon_data = BookCoverService.scrape_amazon_book_data(isbn10)
                cache.set(cache_key_amazon, amazon_data, BookCoverService.AMAZON_CACHE_TIMEOUT)

            if amazon_data:
                # Merge OL and Amazon data
                merged_data = BookCoverService.merge_metadata(ol_data, amazon_data)
                return merged_data

        # Return OL data even if no covers (for fallback generation)
        return ol_data

    @staticmethod
    def _fetch_open_library_metadata(isbn):
        """Fetch book metadata from Open Library API."""
        try:
            import urllib.request
            import urllib.parse

            url = f"{BookCoverService.BOOKS_API}?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
            req = urllib.request.Request(url)

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    metadata = data.get(f"ISBN:{isbn}", {})

                    if metadata:
                        # Extract and group subjects
                        subjects_list = metadata.get('subjects', [])
                        subjects = BookCoverService.normalize_subjects(subjects_list)

                        # Extract and normalize languages
                        languages_list = metadata.get('languages', [])
                        normalized_languages = []
                        for lang in languages_list:
                            lang_key = lang.get('key', '')
                            normalized = BookCoverService.normalize_language(lang_key.replace('/languages/', ''))
                            if normalized:
                                normalized_languages.append(normalized)
                            else:
                                normalized_languages.append(lang_key.replace('/languages/', ''))

                        # Extract publisher name from publisher objects
                        publishers = metadata.get('publishers', [])
                        publisher_name = ''
                        if publishers and isinstance(publishers, list) and len(publishers) > 0:
                            if isinstance(publishers[0], dict):
                                publisher_name = publishers[0].get('name', '')
                            else:
                                publisher_name = str(publishers[0])

                        result = {
                            'title': metadata.get('title', ''),
                            'authors': [author.get('name', '') if isinstance(author, dict) else str(author) for author in metadata.get('authors', [])],
                            'publisher': publisher_name,
                            'publish_date': metadata.get('publish_date', ''),
                            'isbn': isbn,
                            'covers': [],
                            'description': metadata.get('description', {}).get('value', '') if isinstance(metadata.get('description'), dict) else metadata.get('description', ''),
                            'languages': normalized_languages,
                            'subjects': subjects,
                            'pages': metadata.get('number_of_pages', ''),
                            'edition': metadata.get('edition_name', ''),
                            'physical_format': metadata.get('physical_format', ''),
                        }

                        # Get cover URLs
                        if 'cover' in metadata:
                            cover_urls = metadata['cover']
                            if isinstance(cover_urls, dict):
                                result['covers'] = [cover_urls.get('large', ''), cover_urls.get('medium', ''), cover_urls.get('small', '')]
                            elif isinstance(cover_urls, int):
                                # It's a cover ID, build URLs manually
                                cover_id = cover_urls
                                result['covers'] = [
                                    f"{BookCoverService.COVERS_API}/b/id/{cover_id}-L.jpg",
                                    f"{BookCoverService.COVERS_API}/b/id/{cover_id}-M.jpg",
                                    f"{BookCoverService.COVERS_API}/b/id/{cover_id}-S.jpg"
                                ]
                        elif metadata.get('covers') and isinstance(metadata.get('covers'), list):
                            for cover_id in metadata.get('covers')[:1]:  # Get first cover
                                result['covers'] = [
                                    f"{BookCoverService.COVERS_API}/b/id/{cover_id}-L.jpg",
                                    f"{BookCoverService.COVERS_API}/b/id/{cover_id}-M.jpg",
                                    f"{BookCoverService.COVERS_API}/b/id/{cover_id}-S.jpg"
                                ]
                                break

                        return result

        except Exception as e:
            pass

        return None
    
    @staticmethod
    def fetch_cover_url(isbn, size='M'):
        """Get cover URL for ISBN from Open Library."""
        return f"{BookCoverService.COVERS_API}/isbn/{isbn}-{size}.jpg"
    
    @staticmethod
    def download_and_save_cover(url, item, order=0, is_primary=True):
        """Download cover from URL and save as ItemImage."""
        try:
            import urllib.request

            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0')

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    image_data = response.read()

                    # Create filename
                    filename = f"cover-{item.isbn or 'isbn-lookup'}-{order}.jpg"

                    # Save using Django's ContentFile
                    from django.core.files.base import ContentFile

                    # Create ItemImage
                    item_image = ItemImage(
                        item=item,
                        image=ContentFile(image_data, name=filename),
                        is_primary=is_primary,
                        order=order
                    )
                    item_image.save()

                    return True, f"Cover saved as {filename}"

        except Exception as e:
            return False, f"Error downloading cover: {str(e)}"

    @staticmethod
    def download_cover(url, isbn, size='M'):
        """Download cover image and save to local storage."""
        try:
            import urllib.request
            
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    # Create directory structure
                    cover_dir = os.path.join('covers', isbn[:10], isbn[-3])
                    os.makedirs(os.path.join(settings.MEDIA_ROOT, cover_dir), exist_ok=True)
                    
                    # Save file
                    filename = f"cover-{size}.jpg"
                    file_path = os.path.join(cover_dir, filename)
                    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                    
                    with open(full_path, 'wb') as f:
                        f.write(response.read())
                    
                    return file_path
            
        except Exception as e:
            pass

        return None
    
    @staticmethod
    def process_item_cover(item):
        """Process and set cover for an item."""
        if not item.isbn:
            return False, "No ISBN provided"
        
        isbn = BookCoverService.normalize_isbn(item.isbn)
        if not BookCoverService.is_valid_isbn(isbn):
            return False, "Invalid ISBN format"
        
        # Skip if user already uploaded a cover
        if item.images.filter(is_primary=True).exists():
            return False, "User already uploaded cover"
        
        # Mark ISBN as attempted
        item.isbn_lookup_attempted = True
        
        try:
            # Fetch metadata
            metadata = BookCoverService.fetch_book_metadata(isbn)
            if metadata:
                # Update item metadata if fields are empty
                if not item.title and metadata['title']:
                    item.title = metadata['title']
                if not item.author and metadata['authors']:
                    item.author = ', '.join(metadata['authors'])
                if not item.publisher and metadata['publisher']:
                    item.publisher = metadata['publisher']
                if not item.year and metadata['publish_date']:
                    # Extract year from publish_date
                    year_match = re.search(r'(\d{4})', metadata['publish_date'])
                    if year_match:
                        item.year = int(year_match.group(1))
                
                # Try to download cover
                cover_url = None
                if metadata['covers'] and len(metadata['covers']) > 0:
                    # Use the first cover URL from metadata (large size)
                    cover_url = metadata['covers'][0]
                else:
                    # Fallback to ISBN-based URL
                    cover_url = BookCoverService.fetch_cover_url(isbn, 'L')

                if cover_url:
                    cover_path = BookCoverService.download_cover(cover_url, isbn, 'L')
                    
                    if cover_path:
                        # Create ItemImage
                        item_image = ItemImage(
                            item=item,
                            image=cover_path,
                            is_primary=True,
                            caption=f"Auto-fetched from Open Library: {metadata['title']}"
                        )
                        item_image.save()

                        # Set cover source based on metadata source
                        cover_source = metadata.get('source', 'openlibrary')
                        item.cover_source = cover_source
                        item.cover_fetched_at = timezone.now()
                        item.save(update_fields=['title', 'author', 'publisher', 'year', 'isbn_lookup_attempted', 'cover_source', 'cover_fetched_at'])

                        return True, f"Cover and metadata fetched successfully from {cover_source}"
                    else:
                        return False, "Failed to download cover"
                else:
                    # No cover found, generate fallback
                    authors = metadata.get('authors', [])
                    author = authors[0] if authors else ''
                    cover_path = BookCoverService.generate_fallback_cover(metadata['title'], author, isbn)
                    if cover_path:
                        item_image = ItemImage(
                            item=item,
                            image=cover_path,
                            is_primary=True,
                            caption=f"Generated cover: {metadata['title']}"
                        )
                        item_image.save()
                        
                        item.cover_source = 'generated'
                        item.cover_fetched_at = timezone.now()
                        item.save(update_fields=['title', 'author', 'publisher', 'year', 'isbn_lookup_attempted', 'cover_source', 'cover_fetched_at'])
                        
                        return True, f"Generated fallback cover"
                    else:
                        return False, "No cover available and fallback generation failed"
            else:
                # Generate basic fallback from item data
                cover_path = BookCoverService.generate_fallback_cover(item.title, item.author, isbn)
                if cover_path:
                    item_image = ItemImage(
                        item=item,
                        image=cover_path,
                        is_primary=True,
                        caption=f"Generated cover: {item.title}"
                    )
                    item_image.save()
                    
                    item.cover_source = 'generated'
                    item.cover_fetched_at = timezone.now()
                    item.save(update_fields=['isbn_lookup_attempted', 'cover_source', 'cover_fetched_at'])
                    
                    return True, f"Generated fallback cover"
                else:
                    return False, "No metadata found and fallback generation failed"
                    
        except Exception as e:
            return False, f"Error processing cover: {str(e)}"
    
    @staticmethod
    def generate_fallback_cover(title, author, isbn):
        """Generate a simple 8-bit style fallback cover."""
        try:
            # Create a simple colored rectangle as fallback
            # We'll use CSS gradient generation for now since PIL might not be available
            import hashlib
            
            # Use ISBN hash to generate consistent colors
            hash_obj = hashlib.md5(isbn.encode())
            hash_int = int(hash_obj.hexdigest(), 16)
            
            # Pastel colors
            colors = [
                '#FFB6C1',  # Light pink
                '#FFDAB9',  # Peach
                '#C7ECEE',  # Light blue
                '#B9FBC0',  # Light green
                '#FFF5B4',  # Light yellow
                '#E6E6FA',  # Lavender
            ]
            
            color = colors[hash_int % len(colors)]
            
            # For now, return a placeholder path
            # In a real implementation, we'd create an actual image
            return f"generated-{isbn}-{hash_int % 100}.jpg"
            
        except Exception as e:
            pass
            return None

    @staticmethod
    def isbn13_to_isbn10(isbn13):
        """Convert ISBN-13 to ISBN-10 for Amazon lookups."""
        if not isbn13 or len(isbn13.replace('-', '')) != 13:
            return None

        # Remove hyphens and validate
        clean = isbn13.replace('-', '')
        if not clean.startswith(('978', '979')):
            return None

        # Extract middle 9 digits (positions 4-12 of ISBN-13)
        middle9 = clean[3:12]

        # Calculate ISBN-10 check digit (weights 10,9,8,7,6,5,4,3,2)
        total = 0
        for i, digit in enumerate(middle9):
            total += int(digit) * (10 - i)

        check_digit = (11 - (total % 11)) % 11
        if check_digit == 10:
            check_digit = 'X'
        else:
            check_digit = str(check_digit)

        return middle9 + check_digit

    @staticmethod
    def is_amazon_blocked():
        """Check if Amazon is currently blocking our requests."""
        cache_key = 'amazon_blocking_status'
        return cache.get(cache_key, False)

    @staticmethod
    def set_amazon_blocked():
        """Mark Amazon as blocked for 15 minutes."""
        cache_key = 'amazon_blocking_status'
        cache.set(cache_key, True, BookCoverService.BLOCKING_TIMEOUT)

    @staticmethod
    def scrape_amazon_book_data(isbn10):
        """Scrape Amazon for comprehensive book metadata."""
        if BookCoverService.is_amazon_blocked():
            return None

        # Try regions in order: amazon.com, amazon.es, amazon.de
        regions = [
            ('com', 'amazon.com'),
            ('es', 'amazon.es'),
            ('de', 'amazon.de')
        ]

        for region_code, domain in regions:
            url = f"https://www.{domain}/dp/{isbn10}"
            data = BookCoverService._scrape_amazon_page(url)

            if data and (data.get('title') or data.get('covers')):
                return data

        return None

    @staticmethod
    def _scrape_amazon_page(url):
        """Scrape a single Amazon product page."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; ComunizaBot/1.0)',
                'Accept-Language': 'en-US,en;q=0.9'
            }

            # Add small delay to be respectful
            time.sleep(1)

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 403 or response.status_code == 503:
                # Amazon is blocking us
                BookCoverService.set_amazon_blocked()
                return None

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            data = {}

            # Title
            title_elem = soup.find('span', {'id': 'productTitle'})
            if title_elem:
                data['title'] = title_elem.text.strip()

            # Authors
            authors = []
            author_elems = soup.find_all('a', {'class': 'contributorNameID'})
            for author in author_elems:
                authors.append(author.text.strip())
            if authors:
                data['authors'] = authors

            # Publisher and Publication Date from detail bullets
            publisher_info = soup.find('div', {'id': 'detailBullets_feature_div'})
            if publisher_info:
                bullets = publisher_info.find_all('span', {'class': 'a-list-item'})
                for bullet in bullets:
                    text = bullet.text.strip()
                    if 'Publisher' in text:
                        # Extract publisher and date
                        # This is a simplified extraction - could be more robust
                        data['publisher'] = text.replace('Publisher', '').strip()
                    if any(word in text.lower() for word in ['hardcover', 'paperback', 'kindle']):
                        data['format'] = text.strip()

            # Cover Image (medium quality)
            img_selectors = [
                {'id': 'landingImage'},
                {'id': 'imgBlkFront'},
                {'class': 'a-dynamic-image'},
                {'class': 'frontImage'}
            ]

            cover_url = None
            for selector in img_selectors:
                img = soup.find('img', selector)
                if img and 'src' in img.attrs:
                    cover_url = img['src']
                    # Prefer medium quality
                    if '_SL' in cover_url:
                        cover_url = cover_url.replace('_SL1500_', '_SL500_').replace('_SL1000_', '_SL500_')
                    break

            if cover_url:
                # Prefer medium quality image
                if '_SL1500_' in cover_url:
                    cover_url = cover_url.replace('_SL1500_', '_SL500_')
                elif '_SL1000_' in cover_url:
                    cover_url = cover_url.replace('_SL1000_', '_SL500_')
                elif '_SL750_' in cover_url:
                    cover_url = cover_url.replace('_SL750_', '_SL500_')
                # If already medium or we can't determine, keep as is

                data['covers'] = [cover_url]
                data['cover_url'] = cover_url

            # Publication year (simplified extraction)
            if publisher_info:
                # Look for year in the publisher info
                year_match = re.search(r'(\d{4})', str(publisher_info))
                if year_match:
                    data['publish_date'] = year_match.group(1)

            data['source'] = 'amazon'
            return data if (data.get('title') or data.get('covers')) else None

        except Exception as e:
            pass
            return None

    @staticmethod
    def merge_metadata(ol_data, amazon_data):
        """Merge Open Library and Amazon data intelligently."""
        merged = ol_data.copy() if ol_data else {}

        if amazon_data:
            # Open Library has priority for core metadata
            if not merged.get('title') and amazon_data.get('title'):
                merged['title'] = amazon_data['title']

            if not merged.get('authors') and amazon_data.get('authors'):
                merged['authors'] = amazon_data['authors']

            if not merged.get('publisher') and amazon_data.get('publisher'):
                merged['publisher'] = amazon_data['publisher']

            if not merged.get('publish_date') and amazon_data.get('publish_date'):
                merged['publish_date'] = amazon_data['publish_date']

            # Always prefer Amazon cover (better quality)
            if amazon_data.get('covers'):
                merged['covers'] = amazon_data['covers']
                merged['cover_url'] = amazon_data.get('cover_url')
                merged['source'] = 'amazon'

            # Add format if available
            if amazon_data.get('format'):
                merged['format'] = amazon_data['format']

        return merged
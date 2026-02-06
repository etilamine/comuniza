"""
Custom validators for Comuniza.

This module contains custom Django validators for input sanitization and validation
to ensure data integrity and security, including comprehensive image upload validation.
"""

import os
import re
import phonenumbers
import magic
import html
from PIL import Image
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, EmailValidator
from django.utils.html import strip_tags
from django.utils.text import slugify


class SanitizedTextValidator:
    """Validator that sanitizes text input to prevent XSS and ensure clean data."""

    def __init__(self, max_length=None, allowed_tags=None, strip_html=True):
        self.max_length = max_length
        self.allowed_tags = allowed_tags or []
        self.strip_html = strip_html

    def __call__(self, value):
        if not value:
            return value

        # Strip HTML tags if requested
        if self.strip_html:
            value = strip_tags(value)
        elif self.allowed_tags:
            # If specific tags are allowed, we'd need a more sophisticated HTML cleaner
            # For now, just strip all tags for security
            value = strip_tags(value)

        # Trim whitespace
        value = value.strip()

        # Check length
        if self.max_length and len(value) > self.max_length:
            raise ValidationError(
                _("Text exceeds maximum length of %(max_length)s characters."),
                params={'max_length': self.max_length},
            )

        # Check for potentially dangerous patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'on\w+\s*=',  # Event handlers
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE | re.DOTALL):
                raise ValidationError(_("Invalid content detected."))

        return value


class ISBNValidator:
    """Validator for ISBN-10 and ISBN-13 numbers."""

    def __call__(self, value):
        if not value:
            return value

        # Remove spaces, hyphens, etc.
        clean_isbn = re.sub(r'[^\dX]', '', str(value).upper())

        # Check if it's a valid length
        if len(clean_isbn) not in [10, 13]:
            raise ValidationError(_("ISBN must be 10 or 13 digits long."))

        # Validate ISBN-10
        if len(clean_isbn) == 10:
            if not self._validate_isbn10(clean_isbn):
                raise ValidationError(_("Invalid ISBN-10 number."))
        # Validate ISBN-13
        elif len(clean_isbn) == 13:
            if not self._validate_isbn13(clean_isbn):
                raise ValidationError(_("Invalid ISBN-13 number."))

        return clean_isbn

    def _validate_isbn10(self, isbn):
        """Validate ISBN-10 checksum."""
        if len(isbn) != 10:
            return False

        total = 0
        for i, char in enumerate(isbn):
            if char == 'X':
                if i != 9:  # X only allowed at the end
                    return False
                digit = 10
            else:
                try:
                    digit = int(char)
                except ValueError:
                    return False
            total += digit * (10 - i)

        return total % 11 == 0

    def _validate_isbn13(self, isbn):
        """Validate ISBN-13 checksum."""
        if len(isbn) != 13:
            return False

        total = 0
        for i, char in enumerate(isbn):
            try:
                digit = int(char)
            except ValueError:
                return False
            total += digit * (1 if i % 2 == 0 else 3)

        return total % 10 == 0


class PhoneNumberValidator:
    """Validator for international phone numbers."""

    def __init__(self, default_region=None):
        self.default_region = default_region or 'DE'  # Default to Germany

    def __call__(self, value):
        if not value:
            return value

        # Remove all non-digit characters except + and spaces
        cleaned = re.sub(r'[^\d+\s]', '', str(value))

        try:
            # Parse the phone number
            parsed = phonenumbers.parse(cleaned, self.default_region)

            # Validate the number
            if not phonenumbers.is_valid_number(parsed):
                raise ValidationError(_("Invalid phone number."))

            # Format the number in international format
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)

        except phonenumbers.NumberParseException:
            raise ValidationError(_("Invalid phone number format."))


class YearValidator:
    """Validator for year values."""

    def __init__(self, min_year=1000, max_year=None):
        self.min_year = min_year
        self.max_year = max_year or 2100  # Default to reasonable future year

    def __call__(self, value):
        if value is None:
            return value

        try:
            year = int(value)
        except (ValueError, TypeError):
            raise ValidationError(_("Year must be a valid number."))

        if year < self.min_year:
            raise ValidationError(
                _("Year must be %(min_year)s or later."),
                params={'min_year': self.min_year},
            )

        if year > self.max_year:
            raise ValidationError(
                _("Year cannot be later than %(max_year)s."),
                params={'max_year': self.max_year},
            )

        return year


class PriceValidator:
    """Validator for price/currency values."""

    def __init__(self, max_digits=10, decimal_places=2, min_value=0):
        self.max_digits = max_digits
        self.decimal_places = decimal_places
        self.min_value = min_value

    def __call__(self, value):
        if value is None:
            return value

        try:
            # Convert to Decimal for precise validation
            from decimal import Decimal, InvalidOperation
            price = Decimal(str(value))
        except (InvalidOperation, TypeError):
            raise ValidationError(_("Invalid price format."))

        if price < self.min_value:
            raise ValidationError(
                _("Price cannot be less than %(min_value)s."),
                params={'min_value': self.min_value},
            )

        # Check decimal places
        if '.' in str(value):
            decimal_part = str(value).split('.')[-1]
            if len(decimal_part) > self.decimal_places:
                raise ValidationError(
                    _("Price can have at most %(decimal_places)s decimal places."),
                    params={'decimal_places': self.decimal_places},
                )

        return price


class CoordinateValidator:
    """Validator for latitude/longitude coordinates."""

    def __call__(self, value):
        if value is None:
            return value

        try:
            coord = float(value)
        except (ValueError, TypeError):
            raise ValidationError(_("Coordinate must be a valid number."))

        # For latitude: -90 to 90
        # For longitude: -180 to 180
        # Since we don't know which coordinate this is for, we'll allow the wider range
        if coord < -180 or coord > 180:
            raise ValidationError(_("Coordinate must be between -180 and 180."))

        return coord


class SafeSlugValidator:
    """Validator for slug fields that ensures safe URL characters."""

    def __call__(self, value):
        if not value:
            return value

        # Generate slug and check if it matches the input
        safe_slug = slugify(value)

        if safe_slug != value:
            raise ValidationError(_("Slug contains invalid characters. Use only letters, numbers, and hyphens."))

        return value


class NoProfanityValidator:
    """Validator that checks for common profanity."""

    # Basic profanity list (expand as needed)
    PROFANITY_WORDS = {
        'damn', 'hell', 'crap', 'shit', 'fuck', 'ass', 'bitch', 'bastard',
        'cunt', 'dick', 'pussy', 'cock', 'tits', 'boobs', 'asshole',
        # Add more as needed, or load from a file
    }

    def __call__(self, value):
        if not value:
            return value

        text_lower = str(value).lower()

        # Check for profanity
        for word in self.PROFANITY_WORDS:
            if word in text_lower:
                raise ValidationError(_("Content contains inappropriate language."))

        return value


class UsernameValidator:
    """Validator for username fields."""

    def __call__(self, value):
        if not value:
            return value

        # Check length
        if len(value) < 3:
            raise ValidationError(_("Username must be at least 3 characters long."))

        if len(value) > 50:
            raise ValidationError(_("Username cannot exceed 50 characters."))

        # Check for valid characters (letters, numbers, underscores, hyphens)
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValidationError(_("Username can only contain letters, numbers, underscores, and hyphens."))

        # Check for reserved words
        reserved_words = {'admin', 'root', 'system', 'moderator', 'staff', 'support'}
        if value.lower() in reserved_words:
            raise ValidationError(_("This username is reserved."))

        return value


class StrongPasswordValidator:
    """Validator for strong passwords."""

    def __call__(self, value):
        if not value:
            return value

        errors = []

        if len(value) < 8:
            errors.append(_("Password must be at least 8 characters long."))

        if not re.search(r'[A-Z]', value):
            errors.append(_("Password must contain at least one uppercase letter."))

        if not re.search(r'[a-z]', value):
            errors.append(_("Password must contain at least one lowercase letter."))

        if not re.search(r'\d', value):
            errors.append(_("Password must contain at least one number."))

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            errors.append(_("Password must contain at least one special character."))

        if errors:
            raise ValidationError(errors)

        return value


class ImageUploadValidator:
    """Comprehensive image upload validation with security restrictions."""

    # Allowed MIME types for images
    ALLOWED_MIME_TYPES = {
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/webp',
        'image/gif'
    }

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.webp', '.gif'
    }

    # Maximum file sizes (in bytes)
    MAX_SIZES = {
        'avatar': 5 * 1024 * 1024,      # 5MB
        'item_image': 5 * 1024 * 1024,   # 5MB
        'group_image': 5 * 1024 * 1024,  # 5MB
        'default': 5 * 1024 * 1024       # 5MB default
    }

    # Maximum dimensions (width, height)
    MAX_DIMENSIONS = {
        'avatar': (2000, 2000),          # 2000x2000px
        'item_image': (4000, 4000),      # 4000x4000px
        'group_image': (3000, 3000),     # 3000x3000px
        'default': (2000, 2000)          # 2000x2000px default
    }

    @classmethod
    def validate_image(cls, uploaded_file, image_type='default'):
        """
        Comprehensive image validation.

        Args:
            uploaded_file: UploadedFile instance
            image_type: Type of image ('avatar', 'item_image', 'group_image', 'default')

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(uploaded_file, UploadedFile):
            raise ValidationError(_("Invalid file upload."))

        # 1. Check file size
        cls._validate_file_size(uploaded_file, image_type)

        # 2. Check file extension
        cls._validate_file_extension(uploaded_file)

        # 3. Check MIME type
        cls._validate_mime_type(uploaded_file)

        # 4. Validate actual image content
        cls._validate_image_content(uploaded_file, image_type)

        # 5. Sanitize filename
        cls._sanitize_filename(uploaded_file)

    @classmethod
    def _validate_file_size(cls, uploaded_file, image_type):
        """Validate file size."""
        max_size = cls.MAX_SIZES.get(image_type, cls.MAX_SIZES['default'])

        if uploaded_file.size > max_size:
            max_mb = max_size / (1024 * 1024)
            raise ValidationError(
                _("File size too large. Maximum size is %(max_size).1f MB.") %
                {'max_size': max_mb}
            )

    @classmethod
    def _validate_file_extension(cls, uploaded_file):
        """Validate file extension."""
        filename = uploaded_file.name.lower()
        _, ext = os.path.splitext(filename)

        if ext not in cls.ALLOWED_EXTENSIONS:
            allowed_exts = ', '.join(cls.ALLOWED_EXTENSIONS)
            raise ValidationError(
                _("Invalid file extension. Allowed extensions: %(allowed)s.") %
                {'allowed': allowed_exts}
            )

    @classmethod
    def _validate_mime_type(cls, uploaded_file):
        """Validate MIME type using python-magic."""
        try:
            # Read first few bytes to determine MIME type
            file_content = uploaded_file.read(2048)
            uploaded_file.seek(0)  # Reset file pointer

            mime_type = magic.from_buffer(file_content, mime=True)

            if mime_type not in cls.ALLOWED_MIME_TYPES:
                raise ValidationError(
                    _("Invalid file type. Only images are allowed.")
                )

        except Exception:
            # Fallback to basic validation if magic fails
            if not uploaded_file.content_type or not uploaded_file.content_type.startswith('image/'):
                raise ValidationError(_("Invalid file type. Only images are allowed."))

    @classmethod
    def _validate_image_content(cls, uploaded_file, image_type):
        """Validate actual image content and dimensions."""
        try:
            with Image.open(uploaded_file) as img:
                # Verify image can be processed
                img.verify()

                # Reset file pointer and reopen for dimension check
                uploaded_file.seek(0)
                with Image.open(uploaded_file) as img:
                    max_width, max_height = cls.MAX_DIMENSIONS.get(
                        image_type, cls.MAX_DIMENSIONS['default']
                    )

                    if img.width > max_width or img.height > max_height:
                        raise ValidationError(
                            _("Image dimensions too large. Maximum size is %(max_w)d×%(max_h)d pixels.") %
                            {'max_w': max_width, 'max_h': max_height}
                        )

                    # Check for potentially malicious images
                    cls._validate_image_safety(img)

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(_("Invalid or corrupted image file."))

    @classmethod
    def _validate_image_safety(cls, image):
        """Validate image for potential security issues."""
        # Check for animated GIFs (can be used for DoS)
        if image.format == 'GIF' and getattr(image, 'is_animated', False):
            if image.n_frames > 50:  # Reasonable limit
                raise ValidationError(_("Animated GIFs with too many frames are not allowed."))

        # Check image mode
        if image.mode not in ['RGB', 'RGBA', 'L', 'P']:
            raise ValidationError(_("Unsupported image format."))

    @classmethod
    def _sanitize_filename(cls, uploaded_file):
        """Sanitize filename to prevent path traversal."""
        filename = uploaded_file.name

        # Remove directory separators
        filename = os.path.basename(filename)

        # Remove dangerous characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)

        # Ensure filename is not empty
        if not filename or filename.startswith('.'):
            filename = 'image_' + filename.lstrip('.')

        # Limit filename length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext

        uploaded_file.name = filename


class EnhancedInputSanitizer:
    """Enhanced input sanitization with comprehensive security measures."""

    # Extended XSS patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
        r'onfocus\s*=',
        r'onblur\s*=',
        r'onchange\s*=',
        r'onsubmit\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<link[^>]*>.*?</link>',
        r'<meta[^>]*>.*?</meta>',
        r'expression\s*\(',
        r'@import',
        r'<style[^>]*>.*?</style>',
    ]

    # Extended SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(\bUNION\b.*\bSELECT\b)',
        r'(\bDROP\b.*\bTABLE\b)',
        r'(\bINSERT\b.*\bINTO\b)',
        r'(\bUPDATE\b.*\bSET\b)',
        r'(\bDELETE\b.*\bFROM\b)',
        r'(\bSELECT\b.*\bFROM\b)',
        r'(--)',
        r'(/\*.*\*/)',
        r'(\'\s*OR\s*\'.*\')',
        r'(\"\s*OR\s*\".*\")',
        r'(\bEXEC\b)',
        r'(\bEXECUTE\b)',
        r'(\bXP_CMDSHELL\b)',
        r'(\bSP_EXECUTESQL\b)',
    ]

    @classmethod
    def sanitize_text_input(cls, text, allow_html=False, max_length=None):
        """
        Enhanced text sanitization with comprehensive security checks.

        Args:
            text: Input text to sanitize
            allow_html: Whether to allow certain HTML tags
            max_length: Maximum allowed length

        Returns:
            Sanitized text
        """
        if not text:
            return text

        # Convert to string if needed
        if not isinstance(text, str):
            text = str(text)

        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

        # Apply length limit
        if max_length and len(text) > max_length:
            text = text[:max_length]

        # Strip whitespace
        text = text.strip()

        if not allow_html:
            # Escape HTML entities
            text = html.escape(text, quote=True)

            # Remove dangerous patterns
            for pattern in cls.XSS_PATTERNS:
                text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        else:
            # Allow only safe HTML tags (basic implementation)
            # For production, consider using bleach library
            allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
            # For now, we'll escape everything for security
            text = html.escape(text, quote=True)

        # Remove SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

        # Additional security checks
        text = cls._remove_control_characters(text)
        text = cls._normalize_unicode(text)

        return text

    @classmethod
    def _remove_control_characters(cls, text):
        """Remove potentially dangerous control characters."""
        # Keep only safe control characters (tab, newline, carriage return)
        return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

    @classmethod
    def _normalize_unicode(cls, text):
        """Normalize Unicode to prevent homograph attacks."""
        import unicodedata
        # Normalize to NFKC which decomposes and recomposes characters
        return unicodedata.normalize('NFKC', text)

    @classmethod
    def sanitize_email(cls, email):
        """Enhanced email sanitization and validation."""
        if not email:
            return email

        email = cls.sanitize_text_input(email.strip().lower())

        # Enhanced email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError(_("Invalid email address."))

        # Check for dangerous patterns in email
        dangerous_patterns = [
            r'[\x00-\x1F\x7F]',  # Control characters
            r'[<>]',  # HTML brackets
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, email):
                raise ValidationError(_("Invalid email address."))

        return email

    @classmethod
    def sanitize_url(cls, url):
        """Enhanced URL sanitization and validation."""
        if not url:
            return url

        url = cls.sanitize_text_input(url.strip())

        # Remove dangerous protocols
        dangerous_protocols = [
            'javascript:', 'vbscript:', 'data:', 'file:', 'ftp:',
            'mailto:', 'tel:', 'sms:', 'callto:'
        ]

        url_lower = url.lower()
        for protocol in dangerous_protocols:
            if url_lower.startswith(protocol):
                raise ValidationError(_("Invalid URL protocol."))

        # Basic URL validation
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url):
            raise ValidationError(_("Invalid URL format. Only HTTP/HTTPS URLs are allowed."))

        return url


# Custom form field validators for images
def validate_avatar_image(value):
    """Validator for avatar images."""
    ImageUploadValidator.validate_image(value, 'avatar')


def validate_item_image(value):
    """Validator for item images."""
    ImageUploadValidator.validate_image(value, 'item_image')


def validate_group_image(value):
    """Validator for group images."""
    ImageUploadValidator.validate_image(value, 'group_image')


# Enhanced text validators
def validate_enhanced_safe_text(value):
    """Enhanced validator for safe text input."""
    sanitized = EnhancedInputSanitizer.sanitize_text_input(value)
    if sanitized != html.escape(value):
        raise ValidationError(_("Input contains unsafe characters."))
    return sanitized


def validate_enhanced_safe_html(value):
    """Enhanced validator for safe HTML input."""
    sanitized = EnhancedInputSanitizer.sanitize_text_input(value, allow_html=True)
    if sanitized != html.escape(value):
        raise ValidationError(_("HTML contains unsafe content."))
    return sanitized


def validate_enhanced_email(value):
    """Enhanced validator for safe email input."""
    return EnhancedInputSanitizer.sanitize_email(value)


def validate_enhanced_url(value):
    """Enhanced validator for safe URL input."""
    return EnhancedInputSanitizer.sanitize_url(value)


# Pre-configured validator instances for common use
sanitized_text = SanitizedTextValidator()
enhanced_sanitized_text = EnhancedInputSanitizer()
isbn_validator = ISBNValidator()
phone_validator = PhoneNumberValidator()
year_validator = YearValidator()
price_validator = PriceValidator()
coordinate_validator = CoordinateValidator()
safe_slug = SafeSlugValidator()
no_profanity = NoProfanityValidator()
username_validator = UsernameValidator()
strong_password = StrongPasswordValidator()

# Image validators
avatar_image_validator = ImageUploadValidator()
item_image_validator = ImageUploadValidator()
group_image_validator = ImageUploadValidator()

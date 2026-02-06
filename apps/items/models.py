"""
Items models for Comuniza.
Items that can be shared and borrowed within groups.
"""

from django.conf import settings
from django.db import models, transaction
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.fields import ThumbnailerImageField
from apps.core.validators import (
    sanitized_text, isbn_validator, year_validator, price_validator,
    coordinate_validator, username_validator, no_profanity
)


class ItemCategory(models.Model):
    """
    Categories for organizing items (books, tools, electronics, etc.)
    """

    name = models.CharField(
        _("name"),
        max_length=100,
        validators=[sanitized_text, no_profanity]
    )
    slug = models.SlugField(_("slug"), max_length=120, unique=True)
    description = models.TextField(
        _("description"),
        blank=True,
        validators=[sanitized_text]
    )
    icon = models.CharField(
        _("icon"),
        max_length=50,
        blank=True,
        validators=[sanitized_text],
        help_text=_("Font Awesome icon class")
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
        verbose_name=_("parent category"),
    )

    # Form configuration for category-specific fields
    form_required_fields = models.JSONField(
        _("required fields"),
        default=list,
        blank=True,
        help_text=_("JSON list of field names that should be required for this category")
    )
    form_optional_fields = models.JSONField(
        _("optional fields"),
        default=list,
        blank=True,
        help_text=_("JSON list of field names that should be optional for this category")
    )
    form_hidden_fields = models.JSONField(
        _("hidden fields"),
        default=list,
        blank=True,
        help_text=_("JSON list of field names that should be hidden for this category")
    )
    form_field_labels = models.JSONField(
        _("field labels"),
        default=dict,
        blank=True,
        help_text=_("JSON object mapping field names to custom labels for this category")
    )
    form_field_help = models.JSONField(
        _("field help text"),
        default=dict,
        blank=True,
        help_text=_("JSON object mapping field names to custom help text for this category")
    )
    form_field_order = models.JSONField(
        _("field order"),
        default=list,
        blank=True,
        help_text=_("JSON array of field names in display order. Fields not listed will appear after ordered fields. Example: ['title', 'category', 'author', 'description']")
    )

    # Metadata
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        db_table = "item_categories"
        verbose_name = _("item category")
        verbose_name_plural = _("item categories")
        ordering = ["name"]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Item(models.Model):
    """
    An item that can be shared/borrowed (book, tool, equipment, etc.)
    """

    CONDITION_CHOICES = [
        ("new", _("New")),
        ("excellent", _("Excellent")),
        ("good", _("Good")),
        ("fair", _("Fair")),
        ("poor", _("Poor")),
    ]

    STATUS_CHOICES = [
        ("available", _("Available")),
        ("borrowed", _("Borrowed")),
        ("not_right_now", _("Not Right Now")),
        ("special_conditions", _("Special Conditions")),
    ]

    # Basic Information
    title = models.CharField(
        _("title"),
        max_length=200,
        validators=[sanitized_text, no_profanity]
    )
    slug = models.SlugField(_("slug"), max_length=220, unique=True)
    description = models.TextField(
        _("description"),
        blank=True,
        validators=[sanitized_text]
    )
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="items",
        verbose_name=_("category"),
    )

    # Details
    author = models.CharField(
        _("author/brand"),
        max_length=200,
        blank=True,
        validators=[sanitized_text],
        help_text=_("Author for books, brand for tools/equipment"),
    )
    publisher = models.CharField(
        _("publisher"),
        max_length=200,
        blank=True,
        validators=[sanitized_text],
        help_text=_("Publisher for books"),
    )
    languages = models.CharField(
        _("languages"),
        max_length=200,
        blank=True,
        validators=[sanitized_text],
        help_text=_("Languages (comma-separated for books)"),
    )
    book_format = models.CharField(
        _("book format"),
        max_length=20,
        choices=[
            ("paperback", _("Paperback")),
            ("hardcover", _("Hardcover")),
            ("ebook", _("E-book")),
            ("audiobook", _("Audiobook")),
            ("other", _("Other")),
        ],
        blank=True,
        help_text=_("Format for books"),
    )
    subjects = models.CharField(
        _("subjects"),
        max_length=500,
        blank=True,
        validators=[sanitized_text],
        help_text=_("Subjects/topics for books (comma-separated)"),
    )
    isbn = models.CharField(
        _("ISBN/Serial Number"),
        max_length=50,
        blank=True,
        validators=[isbn_validator],
        help_text=_("ISBN for books, serial number for equipment"),
    )
    year = models.PositiveIntegerField(
        _("year"),
        null=True,
        blank=True,
        validators=[year_validator]
    )
    condition = models.CharField(
        _("condition"), max_length=10, choices=CONDITION_CHOICES, default="good"
    )
    estimated_value = models.DecimalField(
        _("estimated value"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[price_validator],
        help_text=_("Estimated replacement value in local currency"),
    )

    # Lending Information
    status = models.CharField(
        _("status"), max_length=20, choices=STATUS_CHOICES, default="available"
    )
    LOAN_PERIOD_CHOICES = [
        (1, _("1 day")),
        (3, _("3 days")),
        (7, _("1 week")),
        (14, _("2 weeks")),
        (21, _("3 weeks")),
        (30, _("1 month")),
        (60, _("2 months")),
        (90, _("3 months")),
    ]

    max_loan_days = models.PositiveIntegerField(
        _("maximum loan days"),
        choices=LOAN_PERIOD_CHOICES,
        default=14,
        help_text=_("Maximum number of days this item can be borrowed"),
    )
    requires_deposit = models.BooleanField(
        _("requires deposit"),
        default=False,
        help_text=_("Whether borrowers need to provide a deposit"),
    )
    deposit_amount = models.DecimalField(
        _("deposit amount"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[price_validator],
    )

    # Relationships
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_items",
        verbose_name=_("owner"),
    )
    groups = models.ManyToManyField(
        "groups.Group",
        related_name="items",
        verbose_name=_("groups"),
        help_text=_("Groups where this item is available"),
        blank=True,
    )
    VISIBILITY_CHOICES = [
        ("public", _("Public")),
        ("private", _("Private")),
        ("restricted", _("Restricted")),
    ]

    visibility = models.CharField(
        _("visibility"),
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default="public",
        help_text=_("Public: visible to everyone, Private: hidden, Restricted: only group members"),
    )
    current_borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="currently_borrowed_items",
        verbose_name=_("current borrower"),
    )

    # Settings
    allow_reservations = models.BooleanField(
        _("allow reservations"),
        default=True,
        help_text=_("Allow users to reserve this item when it's borrowed"),
    )
    is_active = models.BooleanField(_("active"), default=True)

    # Book Cover Metadata
    cover_url = models.URLField(_("cover URL"), blank=True, help_text=_("External cover URL from API"))
    cover_source = models.CharField(
        _("cover source"),
        max_length=20,
        choices=[
            ("uploaded", "User Uploaded"),
            ("openlibrary", "Open Library"),
            ("generated", "Generated"),
        ],
        blank=True,
        help_text=_("Source of the cover image"),
    )
    cover_fetched_at = models.DateTimeField(
        _("cover fetched at"),
        null=True,
        blank=True,
        help_text=_("When the cover was fetched from external API"),
    )
    isbn_lookup_attempted = models.BooleanField(
        _("ISBN lookup attempted"),
        default=False,
        help_text=_("Whether we've tried to look up this ISBN"),
    )

    # Metadata
    identifier = models.CharField(
        _("unique identifier"),
        max_length=12,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Unique item identifier (e.g., ITEM-XXXX)")
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    views_count = models.PositiveIntegerField(_("views count"), default=0)
    borrow_count = models.PositiveIntegerField(_("times borrowed"), default=0)

    class Meta:
        db_table = "items"
        verbose_name = _("item")
        verbose_name_plural = _("items")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["owner", "is_active"]),
            models.Index(fields=["status", "is_active"]),
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # Auto-set author to "Anonymous" if not provided
        if not self.author:
            self.author = "Anonymous"

        # Generate unique identifier for new items
        if is_new and not self.identifier:
            import random
            import string
            # Generate 10-character alphanumeric identifier
            chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            self.identifier = chars

        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure uniqueness with retry logic for race conditions
            original_slug = self.slug
            counter = 1
            max_retries = 3
            retry_count = 0
            saved = False

            while retry_count < max_retries and not saved:
                try:
                    with transaction.atomic():
                        super().save(*args, **kwargs)
                        saved = True
                except Exception:
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise
                    # Try next slug variation
                    self.slug = f"{original_slug}-{counter}"
                    counter += 1
        else:
            super().save(*args, **kwargs)
        
        # Emit ItemCreated event for new items (handled asynchronously)
        if is_new:
            from apps.core.events import event_bus, ItemCreatedEvent
            event = ItemCreatedEvent(
                item_id=self.pk,
                owner_id=self.owner_id,
                item_name=self.title,
                category=self.category.name if self.category else 'uncategorized'
            )
            event_bus.publish(event)
        
        # Auto-fetch book cover if ISBN is provided and no user cover exists
        if self.isbn and not self.isbn_lookup_attempted:
            from apps.books.services import BookCoverService
            success, message = BookCoverService.process_item_cover(self)
            if success:
                pass
            else:
                pass

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("item_detail", kwargs={"identifier": self.identifier})

    @property
    def is_available(self):
        """Check if item is available for borrowing."""
        return self.status == "available" and self.is_active

    @property
    def is_borrowed(self):
        """Check if item is currently borrowed."""
        return self.status == "borrowed"

    def can_borrow(self, user):
        """Check if a user can borrow this item."""
        if not self.is_available:
            return False
        if user == self.owner:
            return False
        # Public items can be borrowed by anyone
        if self.visibility == "public":
            return True
        # Restricted items can be borrowed by group members
        elif self.visibility == "restricted":
            return self.groups.filter(members=user).exists()
        # Private items cannot be borrowed
        else:  # private
            return False

    def can_edit(self, user):
        """Check if a user can edit this item."""
        return user == self.owner


class ItemImage(models.Model):
    """
    Images for items.
    """

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("item"),
    )
    image = ThumbnailerImageField(_("image"), upload_to="items/", resize_source=dict(size=(2000, 2000), quality=90))
    caption = models.CharField(_("caption"), max_length=200, blank=True)
    is_primary = models.BooleanField(_("primary image"), default=False)
    order = models.PositiveIntegerField(_("order"), default=0)

    # Metadata
    uploaded_at = models.DateTimeField(_("uploaded at"), auto_now_add=True)

    class Meta:
        db_table = "item_images"
        verbose_name = _("item image")
        verbose_name_plural = _("item images")
        ordering = ["order", "-is_primary", "-uploaded_at"]
        indexes = [
            models.Index(fields=["item", "is_primary"]),
        ]

    def __str__(self):
        return f"Image for {self.item.title}"

    def save(self, *args, **kwargs):
        # If this is set as primary, unset other primary images for this item
        if self.is_primary:
            ItemImage.objects.filter(item=self.item, is_primary=True).update(
                is_primary=False
            )
        super().save(*args, **kwargs)
    
    def get_thumbnail_url(self, alias='item_detail'):
        """
        Get thumbnail URL using easy-thumbnails.
        
        Args:
            alias: Thumbnail alias from settings ('item_list', 'item_detail', 'item_large', etc.)
            
        Returns:
            Thumbnail URL or None if no image
        """
        if not self.image:
            return None
        
        try:
            from easy_thumbnails.files import get_thumbnailer
            thumbnailer = get_thumbnailer(self.image)
            thumbnail = thumbnailer.get_thumbnail(alias)
            return thumbnail.url if thumbnail else self.image.url
        except Exception:
            # Fallback to original image if thumbnail generation fails
            return self.image.url if self.image else None


class TempItemImage(models.Model):
    """
    Temporary images uploaded before item is saved.
    Automatically cleaned up after 24 hours.
    """
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_("user")
    )
    image = ThumbnailerImageField(
        _("image"), 
        upload_to="temp_items/", 
        resize_source=dict(size=(2000, 2000), quality=90)
    )
    session_key = models.CharField(
        _("session key"), 
        max_length=40, 
        db_index=True,
        blank=True,
        default=""
    )
    uploaded_at = models.DateTimeField(
        _("uploaded at"), 
        auto_now_add=True
    )
    order = models.PositiveIntegerField(_("order"), default=0)
    
    class Meta:
        db_table = "temp_item_images"
        verbose_name = _("temporary item image")
        verbose_name_plural = _("temporary item images")
        ordering = ["order", "uploaded_at"]
        indexes = [
            models.Index(fields=["user", "session_key"]),
            models.Index(fields=["uploaded_at"]),
        ]
    
    def __str__(self):
        return f"Temp image for {self.user.username}"
    
    @classmethod
    def cleanup_old_images(cls):
        """Delete images older than 24 hours."""
        from django.utils import timezone
        cutoff = timezone.now() - timezone.timedelta(hours=24)
        return cls.objects.filter(uploaded_at__lt=cutoff).delete()


class ItemReview(models.Model):
    """
    Reviews/ratings for items after being borrowed.
    """

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("item"),
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="item_reviews_written",
        verbose_name=_("reviewer"),
    )
    loan = models.OneToOneField(
        "loans.Loan",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="item_review",
        verbose_name=_("loan"),
    )

    # Review content
    rating = models.PositiveSmallIntegerField(
        _("rating"),
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text=_("Rating from 1 to 5"),
    )
    comment = models.TextField(
        _("comment"),
        blank=True,
        validators=[sanitized_text, no_profanity]
    )

    # Metadata
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        db_table = "item_reviews"
        verbose_name = _("item review")
        verbose_name_plural = _("item reviews")
        ordering = ["-created_at"]
        unique_together = [["item", "reviewer", "loan"]]
        indexes = [
            models.Index(fields=["item", "rating"]),
            models.Index(fields=["reviewer"]),
        ]

    def __str__(self):
        return f"Review by {self.reviewer.email} for {self.item.title}"


class ItemWishlist(models.Model):
    """
    Users can add items to their wishlist to track items they want to borrow.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
        verbose_name=_("user"),
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="wishlisted_by",
        verbose_name=_("item"),
    )
    notes = models.TextField(
        _("notes"),
        blank=True,
        validators=[sanitized_text]
    )
    notify_when_available = models.BooleanField(
        _("notify when available"),
        default=True,
        help_text=_("Send notification when this item becomes available"),
    )

    # Metadata
    added_at = models.DateTimeField(_("added at"), auto_now_add=True)

    class Meta:
        db_table = "item_wishlists"
        verbose_name = _("wishlist item")
        verbose_name_plural = _("wishlist items")
        unique_together = [["user", "item"]]
        ordering = ["-added_at"]
        indexes = [
            models.Index(fields=["user", "notify_when_available"]),
        ]

    def __str__(self):
        return f"{self.user.email} wishlisted {self.item.title}"

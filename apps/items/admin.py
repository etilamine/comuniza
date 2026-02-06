"""
Admin configuration for Items app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Item, ItemCategory, ItemImage, ItemReview, ItemWishlist


class ItemImageInline(admin.TabularInline):
    """Inline admin for item images."""

    model = ItemImage
    extra = 1
    fields = ["image", "caption", "is_primary", "order"]
    readonly_fields = []


class ItemReviewInline(admin.TabularInline):
    """Inline admin for item reviews."""

    model = ItemReview
    extra = 0
    fields = ["reviewer", "rating", "comment", "created_at"]
    readonly_fields = ["created_at"]
    autocomplete_fields = ["reviewer"]


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for ItemCategory model."""

    list_display = ["name", "parent", "is_active", "has_form_config", "created_at"]
    list_filter = ["is_active", "created_at", "parent"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at"]
    autocomplete_fields = ["parent"]

    def has_form_config(self, obj):
        """Check if category has form configuration."""
        return bool(obj.form_required_fields or obj.form_optional_fields or obj.form_hidden_fields)
    has_form_config.short_description = _("Has Form Config")
    has_form_config.boolean = True

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "description",
                    "icon",
                    "parent",
                )
            },
        ),
        (
            _("Form Configuration"),
            {
                "fields": (
                    "form_field_order",
                    "form_required_fields",
                    "form_optional_fields",
                    "form_hidden_fields",
                    "form_field_labels",
                    "form_field_help",
                ),
                "description": _(
                    "Configure form field ordering and visibility for this category. "
                    "Use JSON format. Example: ['title', 'category', 'author'] for field order."
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Status"),
            {"fields": ("is_active",)},
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )

    def get_form(self, request, obj=None, **kwargs):
        """Customize form to add help text for JSON fields."""
        form = super().get_form(request, obj, **kwargs)

        # Add help text for JSON fields
        form.base_fields['form_field_order'].help_text = _(
            "JSON array of field names in display order. Fields not listed will appear after ordered fields. "
            "Example: ['title', 'category', 'author', 'description']"
        )
        form.base_fields['form_required_fields'].help_text = _(
            "JSON array of field names that should be required for this category. "
            "Example: ['author', 'publisher', 'isbn']"
        )
        form.base_fields['form_optional_fields'].help_text = _(
            "JSON array of field names that should be optional for this category. "
            "Example: ['year', 'estimated_value']"
        )
        form.base_fields['form_hidden_fields'].help_text = _(
            "JSON array of field names that should be hidden for this category. "
            "Example: ['book_format', 'subjects']"
        )
        form.base_fields['form_field_labels'].help_text = _(
            "JSON object mapping field names to custom labels. "
            "Example: {'author': 'Brand', 'publisher': 'Retailer'}"
        )
        form.base_fields['form_field_help'].help_text = _(
            "JSON object mapping field names to custom help text. "
            "Example: {'isbn': 'Serial number for warranty purposes'}"
        )

        return form


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """Admin configuration for Item model."""

    list_display = [
        "title",
        "owner",
        "category",
        "condition",
        "status",
        "borrow_count",
        "is_active",
        "created_at",
    ]
    list_filter = [
        "status",
        "condition",
        "is_active",
        "category",
        "created_at",
        "requires_deposit",
    ]
    search_fields = [
        "title",
        "description",
        "author",
        "publisher",
        "isbn",
        "owner__email",
    ]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = [
        "created_at",
        "updated_at",
        "views_count",
        "borrow_count",
        "is_available",
        "is_borrowed",
    ]
    autocomplete_fields = ["owner", "category", "current_borrower"]
    filter_horizontal = ["groups"]
    inlines = [ItemImageInline, ItemReviewInline]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "description",
                    "category",
                    "owner",
                )
            },
        ),
        (
            _("Details"),
            {
                "fields": (
                    "author",
                    "publisher",
                    "isbn",
                    "year",
                    "condition",
                    "estimated_value",
                )
            },
        ),
        (
            _("Lending Information"),
            {
                "fields": (
                    "status",
                    "max_loan_days",
                    "requires_deposit",
                    "deposit_amount",
                    "current_borrower",
                )
            },
        ),
        (
            _("Availability"),
            {
                "fields": (
                    "groups",
                    "allow_reservations",
                    "is_active",
                )
            },
        ),
        (
            _("Statistics"),
            {
                "fields": (
                    "views_count",
                    "borrow_count",
                    "is_available",
                    "is_borrowed",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ItemImage)
class ItemImageAdmin(admin.ModelAdmin):
    """Admin configuration for ItemImage model."""

    list_display = ["item", "caption", "is_primary", "order", "uploaded_at"]
    list_filter = ["is_primary", "uploaded_at"]
    search_fields = ["item__title", "caption"]
    readonly_fields = ["uploaded_at"]
    autocomplete_fields = ["item"]

    fieldsets = (
        (
            None,
            {"fields": ("item", "image", "caption", "is_primary", "order")},
        ),
        (
            _("Metadata"),
            {
                "fields": ("uploaded_at",),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ItemReview)
class ItemReviewAdmin(admin.ModelAdmin):
    """Admin configuration for ItemReview model."""

    list_display = ["item", "reviewer", "rating", "created_at"]
    list_filter = ["rating", "created_at"]
    search_fields = ["item__title", "reviewer__email", "comment"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["item", "reviewer", "loan"]

    fieldsets = (
        (
            None,
            {"fields": ("item", "reviewer", "loan", "rating", "comment")},
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ItemWishlist)
class ItemWishlistAdmin(admin.ModelAdmin):
    """Admin configuration for ItemWishlist model."""

    list_display = ["user", "item", "notify_when_available", "added_at"]
    list_filter = ["notify_when_available", "added_at"]
    search_fields = ["user__email", "item__title", "notes"]
    readonly_fields = ["added_at"]
    autocomplete_fields = ["user", "item"]

    fieldsets = (
        (
            None,
            {"fields": ("user", "item", "notes", "notify_when_available")},
        ),
        (
            _("Metadata"),
            {
                "fields": ("added_at",),
                "classes": ("collapse",),
            },
        ),
    )

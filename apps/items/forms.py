"""
Forms for Items app with category-specific field handling and enhanced validation.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Item, ItemCategory
from apps.core.validators import (
    EnhancedInputSanitizer,
    validate_enhanced_safe_text,
    validate_enhanced_safe_html,
    validate_item_image
)


class ItemForm(forms.ModelForm):
    """
    Dynamic form for Item creation/editing with category-specific fields.
    """

    select_all_groups = forms.BooleanField(
        label=_("Share with all my groups"),
        required=False,
        help_text=_("When 'Restricted' visibility is selected, automatically include all groups you belong to")
    )

    class Meta:
        model = Item
        fields = [
            "title",
            "description",
            "category",
            "author",
            "publisher",
            "languages",
            "book_format",
            "subjects",
            "isbn",
            "year",
            "condition",
            "status",
            "estimated_value",
            "max_loan_days",
            "groups",
            "visibility",
            "allow_reservations",
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Get user from kwargs
        super().__init__(*args, **kwargs)

        # Set default visibility for new items
        if not self.instance.pk and self.user:
            self.fields['visibility'].initial = self.user.default_item_visibility

        # Get category for dynamic configuration
        category_name = None
        if self.instance and self.instance.category:
            category_name = self.instance.category.name
        elif 'category' in self.data and self.data['category']:
            try:
                from .models import ItemCategory
                category = ItemCategory.objects.get(pk=self.data['category'])
                category_name = category.name
            except (ItemCategory.DoesNotExist, ValueError):
                pass

        # Apply field ordering if category has custom order
        if category_name:
            try:
                from .models import ItemCategory
                category = ItemCategory.objects.get(name=category_name, is_active=True)
                if category.form_field_order:
                    self.reorder_item_details_fields(category.form_field_order)
            except ItemCategory.DoesNotExist:
                pass

        # Add placeholders and help text
        self.fields['title'].widget.attrs['placeholder'] = _('e.g., The Lean Startup, Dewalt Power Drill, Canon EOS Camera')
        self.fields['author'].widget.attrs['placeholder'] = _('e.g., Eric Ries, DeWalt, Canon')
        self.fields['description'].widget.attrs['placeholder'] = _('Describe your item, its condition, and any special features...')
        self.fields['description'].widget.attrs['rows'] = 4
        self.fields['publisher'].widget.attrs['placeholder'] = _('e.g., Penguin Books, Amazon')
        self.fields['languages'].widget.attrs['placeholder'] = _('e.g., English, Spanish, French')
        self.fields['book_format'].widget.attrs['placeholder'] = _('Select format')
        self.fields['subjects'].widget.attrs['placeholder'] = _('e.g., Fiction, Fantasy, Adventure')
        self.fields['isbn'].widget.attrs['placeholder'] = _('Enter ISBN to auto-fetch book data...')
        self.fields['year'].widget.attrs['placeholder'] = _('e.g., 2020')
        self.fields['estimated_value'].widget.attrs['placeholder'] = _('Optional')

        # Set up category choices with empty option
        self.fields['category'].empty_label = _('Select a category (optional)')

        # Set up book format choices with empty option
        self.fields['book_format'].empty_label = _('Select format (for books)')

        # Handle select_all_groups logic
        if self.user and 'select_all_groups' in self.data and self.data.get('select_all_groups') == 'on':
            # If select_all_groups is checked, pre-select all user's groups
            if not self.instance.pk:  # Only for new items
                self.fields['groups'].initial = list(self.user.groups.values_list('id', flat=True))

    def reorder_item_details_fields(self, field_order):
        """Reorder only Item Details fields, keeping Basic Info fields in their original positions."""
        if not field_order:
            return

        # Define which fields are Basic Info (should not be reordered)
        basic_info_fields = ['title', 'category', 'description']

        # Separate fields into Basic Info and Item Details
        basic_info_ordered = {}
        item_details_ordered = {}
        remaining_fields = {}

        # First, collect Basic Info fields in their original order
        for field_name in self.fields.keys():
            if field_name in basic_info_fields:
                basic_info_ordered[field_name] = self.fields[field_name]

        # Then, add Item Details fields in the specified order
        for field_name in field_order:
            if field_name in self.fields and field_name not in basic_info_fields:
                item_details_ordered[field_name] = self.fields[field_name]

        # Add any remaining Item Details fields not in the order list
        for field_name, field in self.fields.items():
            if field_name not in basic_info_ordered and field_name not in item_details_ordered:
                remaining_fields[field_name] = field

        # Reconstruct the fields dict: Basic Info first, then ordered Item Details, then remaining
        self.fields.clear()
        self.fields.update(basic_info_ordered)
        self.fields.update(item_details_ordered)
        self.fields.update(remaining_fields)

    def get_category_fields(self, category_name):
        """
        Return field configuration for specific categories from database.
        """
        if not category_name:
            return self._get_default_category_config()

        try:
            category = ItemCategory.objects.get(name=category_name, is_active=True)
            return {
                'required_fields': category.form_required_fields or [],
                'optional_fields': category.form_optional_fields or [],
                'hidden_fields': category.form_hidden_fields or [],
                'show_sections': self._determine_show_sections(category),
                'hide_sections': self._determine_hide_sections(category),
            }
        except ItemCategory.DoesNotExist:
            return self._get_default_category_config()

    def _get_default_category_config(self):
        """Return default configuration for unknown categories."""
        return {
            'required_fields': [],
            'optional_fields': ['author', 'year', 'estimated_value'],
            'hidden_fields': [],
            'show_sections': ['general_details'],
            'hide_sections': []
        }

    def _determine_show_sections(self, category):
        """Determine which sections to show based on category configuration."""
        sections = []

        # Check if category has book-related fields
        book_fields = ['author', 'publisher', 'languages', 'book_format', 'subjects', 'isbn']
        has_book_fields = any(field in (category.form_required_fields + category.form_optional_fields)
                            for field in book_fields)

        if has_book_fields:
            sections.append('book_details')

        # Add other section logic based on category
        if category.name.lower() in ['tools', 'electronics', 'sports & outdoors', 'home & garden', 'games & hobbies']:
            sections.append(f"{category.name.lower().replace(' & ', '_').replace(' ', '_')}_details")

        if not sections:
            sections.append('general_details')

        return sections

    def _determine_hide_sections(self, category):
        """Determine which sections to hide based on category configuration."""
        hide_sections = []

        # Hide book details if no book-related fields are configured
        book_fields = ['author', 'publisher', 'languages', 'book_format', 'subjects', 'isbn']
        has_book_fields = any(field in (category.form_required_fields + category.form_optional_fields)
                            for field in book_fields)

        if not has_book_fields:
            hide_sections.append('book_details')

        return hide_sections

    def get_field_labels(self, category_name):
        """
        Return category-specific field labels from database.
        """
        if not category_name:
            return {}

        try:
            category = ItemCategory.objects.get(name=category_name, is_active=True)
            return category.form_field_labels or {}
        except ItemCategory.DoesNotExist:
            return {}

    def get_field_help_text(self, category_name):
        """
        Return category-specific help text for fields from database.
        """
        if not category_name:
            return {}

        try:
            category = ItemCategory.objects.get(name=category_name, is_active=True)
            return category.form_field_help or {}
        except ItemCategory.DoesNotExist:
            return {}


class ItemSearchForm(forms.Form):
    """
    Search form for items with filtering options.
    """

    q = forms.CharField(
        label=_('Search'),
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('Search items, authors, descriptions...'),
            'class': 'form-control'
        })
    )

    category = forms.ModelChoiceField(
        queryset=ItemCategory.objects.filter(is_active=True),
        empty_label=_('All Categories'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    status = forms.ChoiceField(
        choices=[('', _('All Status'))] + Item.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    group = forms.CharField(
        label=_('Group'),
        required=False,
        widget=forms.HiddenInput()
    )

    def clean_title(self):
        """Enhanced title validation and sanitization."""
        title = self.cleaned_data.get('title')
        if title:
            title = EnhancedInputSanitizer.sanitize_text_input(title, max_length=200)
            if not title.strip():
                raise forms.ValidationError(_("Title cannot be empty."))
        return title

    def clean_description(self):
        """Enhanced description validation and sanitization."""
        description = self.cleaned_data.get('description')
        if description:
            # Allow basic HTML formatting in description
            description = EnhancedInputSanitizer.sanitize_text_input(
                description,
                allow_html=True,
                max_length=2000
            )
        return description

    def clean_author(self):
        """Enhanced author validation and sanitization."""
        author = self.cleaned_data.get('author')
        if author:
            author = EnhancedInputSanitizer.sanitize_text_input(author, max_length=100)
        return author

    def clean_publisher(self):
        """Enhanced publisher validation and sanitization."""
        publisher = self.cleaned_data.get('publisher')
        if publisher:
            publisher = EnhancedInputSanitizer.sanitize_text_input(publisher, max_length=100)
        return publisher

    def clean_isbn(self):
        """Enhanced ISBN validation."""
        isbn = self.cleaned_data.get('isbn')
        if isbn:
            # Remove spaces, hyphens, etc.
            isbn = ''.join(c for c in isbn if c.isalnum() or c == 'X').upper()
            # Basic ISBN validation (length check)
            if len(isbn) not in [10, 13]:
                raise forms.ValidationError(_("ISBN must be 10 or 13 characters long."))
        return isbn

    def clean_year(self):
        """Enhanced year validation."""
        year = self.cleaned_data.get('year')
        if year:
            try:
                year = int(year)
                current_year = 2026  # Update this dynamically if needed
                if year < 1800 or year > current_year + 2:
                    raise forms.ValidationError(_("Please enter a valid year."))
            except ValueError:
                raise forms.ValidationError(_("Year must be a valid number."))
        return year

    def clean_subjects(self):
        """Enhanced subjects validation and sanitization."""
        subjects = self.cleaned_data.get('subjects')
        if subjects:
            # Sanitize each subject
            sanitized_subjects = []
            for subject in subjects:
                sanitized = EnhancedInputSanitizer.sanitize_text_input(subject, max_length=50)
                if sanitized.strip():
                    sanitized_subjects.append(sanitized)
            return sanitized_subjects
        return subjects

"""
Template tags and filters for the items app.
"""

from django import template

register = template.Library()


@register.filter
def get_field(form, field_name):
    """
    Get a form field by name.
    Usage: {{ form|get_field:'title' }}
    """
    return form[field_name]


@register.simple_tag
def get_item_details_field_order(category):
    """
    Get the ordered list of Item Details fields for a category.
    Returns the field order from database, or default ordering.
    """
    if not category:
        return get_default_item_details_order()

    try:
        from apps.items.models import ItemCategory
        cat_obj = ItemCategory.objects.get(name=category, is_active=True)
        if cat_obj.form_field_order:
            # Filter to only include Item Details fields
            item_details_fields = get_item_details_fields()
            return [field for field in cat_obj.form_field_order if field in item_details_fields]
    except ItemCategory.DoesNotExist:
        pass

    return get_default_item_details_order()


def get_item_details_fields():
    """
    Get the list of fields that belong to the Item Details section.
    """
    return [
        'author', 'publisher', 'languages', 'book_format', 'subjects',
        'isbn', 'year', 'condition', 'status', 'estimated_value',
        'max_loan_days', 'groups', 'is_public', 'allow_reservations'
    ]


def get_default_item_details_order():
    """
    Get the default ordering for Item Details fields.
    """
    return [
        'author', 'publisher', 'isbn', 'year', 'condition',
        'status', 'estimated_value', 'max_loan_days', 'groups',
        'is_public', 'allow_reservations', 'languages', 'book_format', 'subjects'
    ]
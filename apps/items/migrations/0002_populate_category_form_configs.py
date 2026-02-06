# Generated manually for populating category form configurations

from django.db import migrations


def populate_category_form_configs(apps, schema_editor):
    """Populate existing categories with form configurations."""
    ItemCategory = apps.get_model('items', 'ItemCategory')

    # Form configurations for each category
    category_configs = {
        'Books': {
            'form_required_fields': ['author', 'publisher', 'languages', 'book_format', 'subjects', 'isbn'],
            'form_optional_fields': ['year'],
            'form_hidden_fields': [],
            'form_field_labels': {
                'author': 'Author',
                'publisher': 'Publisher',
                'isbn': 'ISBN',
                'subjects': 'Subjects/Genres',
                'languages': 'Languages',
                'book_format': 'Format',
                'year': 'Publication Year'
            },
            'form_field_help': {
                'author': 'Author of the book',
                'publisher': 'Publishing company',
                'isbn': 'ISBN-10 or ISBN-13 (book data will be auto-fetched)',
                'subjects': 'Genres, topics, or subjects (comma-separated)',
                'languages': 'Languages the book is available in',
                'book_format': 'Physical or digital format',
                'year': 'Year the book was published'
            }
        },
        'Tools': {
            'form_required_fields': ['author'],
            'form_optional_fields': ['publisher', 'year', 'estimated_value'],
            'form_hidden_fields': ['languages', 'book_format', 'subjects'],
            'form_field_labels': {
                'author': 'Brand/Manufacturer',
                'publisher': 'Distributor (optional)',
                'isbn': 'Serial Number',
                'year': 'Manufacture Year',
                'estimated_value': 'Replacement Value'
            },
            'form_field_help': {
                'author': 'Tool brand or manufacturer (e.g., DeWalt, Makita, Stanley)',
                'publisher': 'Where you purchased it (optional)',
                'isbn': 'Serial number for warranty/tracking purposes',
                'year': 'Year of manufacture',
                'estimated_value': 'Current replacement value for insurance purposes'
            }
        },
        'Electronics': {
            'form_required_fields': ['author'],
            'form_optional_fields': ['publisher', 'year', 'estimated_value'],
            'form_hidden_fields': ['languages', 'book_format', 'subjects'],
            'form_field_labels': {
                'author': 'Brand',
                'publisher': 'Retailer (optional)',
                'isbn': 'Serial Number',
                'year': 'Model Year',
                'estimated_value': 'Replacement Value'
            },
            'form_field_help': {
                'author': 'Electronics brand (e.g., Apple, Sony, Samsung)',
                'publisher': 'Retailer where purchased (optional)',
                'isbn': 'Serial number for warranty/support',
                'year': 'Model year or year of purchase',
                'estimated_value': 'Current replacement value'
            }
        },
        'Sports & Outdoors': {
            'form_required_fields': [],
            'form_optional_fields': ['author', 'year', 'estimated_value'],
            'form_hidden_fields': ['publisher', 'languages', 'book_format', 'subjects', 'isbn'],
            'form_field_labels': {
                'author': 'Brand (optional)',
                'year': 'Year (optional)',
                'estimated_value': 'Replacement Value (optional)'
            },
            'form_field_help': {
                'author': 'Brand if applicable (e.g., Nike, Coleman, Patagonia)',
                'year': 'Year of manufacture or purchase',
                'estimated_value': 'Replacement value for insurance'
            }
        },
        'Home & Garden': {
            'form_required_fields': [],
            'form_optional_fields': ['author', 'year', 'estimated_value'],
            'form_hidden_fields': ['publisher', 'languages', 'book_format', 'subjects', 'isbn'],
            'form_field_labels': {
                'author': 'Brand (optional)',
                'year': 'Year (optional)',
                'estimated_value': 'Replacement Value (optional)'
            },
            'form_field_help': {
                'author': 'Brand if applicable (e.g., Cuisinart, OXO, Rubbermaid)',
                'year': 'Year of purchase or manufacture',
                'estimated_value': 'Replacement value'
            }
        },
        'Games & Hobbies': {
            'form_required_fields': [],
            'form_optional_fields': ['author', 'publisher', 'year'],
            'form_hidden_fields': ['languages', 'book_format', 'subjects', 'isbn'],
            'form_field_labels': {
                'author': 'Publisher/Developer',
                'publisher': 'Distributor (optional)',
                'year': 'Release Year'
            },
            'form_field_help': {
                'author': 'Game publisher or developer',
                'publisher': 'Distributor or publisher (if different)',
                'year': 'Year of release'
            }
        }
    }

    # Update existing categories with configurations
    for category_name, config in category_configs.items():
        try:
            category = ItemCategory.objects.get(name=category_name, is_active=True)
            for field, value in config.items():
                setattr(category, field, value)
            category.save()
        except ItemCategory.DoesNotExist:
            # Skip if category doesn't exist
            pass


def reverse_populate_category_form_configs(apps, schema_editor):
    """Reverse migration: clear form configurations."""
    ItemCategory = apps.get_model('items', 'ItemCategory')

    # Clear all form configurations
    ItemCategory.objects.update(
        form_required_fields=[],
        form_optional_fields=[],
        form_hidden_fields=[],
        form_field_labels={},
        form_field_help={}
    )


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0012_add_category_form_config'),  # Migration that adds the form config fields
    ]

    operations = [
        migrations.RunPython(
            populate_category_form_configs,
            reverse_code=reverse_populate_category_form_configs
        ),
    ]
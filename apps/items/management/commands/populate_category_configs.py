"""
Management command to populate category form configurations with defaults.
"""

from django.core.management.base import BaseCommand
from apps.items.models import ItemCategory


class Command(BaseCommand):
    help = 'Populate category form configurations with default settings'

    def handle(self, *args, **options):
        """Populate categories with form configurations."""
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

        updated_count = 0
        for category_name, config in category_configs.items():
            try:
                category = ItemCategory.objects.get(name=category_name, is_active=True)
                for field, value in config.items():
                    setattr(category, field, value)
                category.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Updated form config for category: {category_name}')
                )
            except ItemCategory.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Category not found: {category_name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated_count} categories with form configurations')
        )
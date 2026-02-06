from django.core.management.base import BaseCommand
from apps.items.models import Item


class Command(BaseCommand):
    help = 'Clean up ISBNs by removing hyphens and normalizing format'

    def handle(self, *args, **options):
        self.stdout.write('Cleaning up ISBNs in database...\n')

        # Find items with hyphens in ISBN
        items_with_hyphens = Item.objects.filter(isbn__contains='-')

        cleaned_count = 0
        for item in items_with_hyphens:
            # Remove hyphens and normalize
            clean_isbn = item.isbn.replace('-', '')
            if clean_isbn != item.isbn:
                old_isbn = item.isbn
                item.isbn = clean_isbn
                item.save(update_fields=['isbn'])
                self.stdout.write(f'Cleaned: {item.title} - {old_isbn} → {clean_isbn}')
                cleaned_count += 1

        # Also check for any other non-standard characters
        items_with_spaces = Item.objects.filter(isbn__regex=r'\s')
        for item in items_with_spaces:
            clean_isbn = item.isbn.replace(' ', '')
            if clean_isbn != item.isbn:
                item.isbn = clean_isbn
                item.save(update_fields=['isbn'])
                self.stdout.write(f'Removed spaces: {item.title} - {item.isbn}')

        self.stdout.write(f'\nCompleted! Cleaned {cleaned_count} ISBNs')

        # Show final statistics
        total_items = Item.objects.count()
        items_with_isbn = Item.objects.filter(isbn__isnull=False, isbn__gt='').count()
        items_with_hyphens = Item.objects.filter(isbn__contains='-').count()

        self.stdout.write(f'Total items: {total_items}')
        self.stdout.write(f'Items with ISBN: {items_with_isbn}')
        self.stdout.write(f'Items with hyphens remaining: {items_with_hyphens}')
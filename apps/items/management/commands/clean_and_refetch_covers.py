"""
Management command to clean ISBNs and re-fetch covers for existing items.
"""

import re
from django.core.management.base import BaseCommand

from apps.books.services import BookCoverService
from apps.items.models import Item


class Command(BaseCommand):
    help = "Clean ISBNs (remove hyphens) and re-fetch covers for existing items"

    def handle(self, *args, **options):
        # Find items with ISBNs containing hyphens
        items_with_hyphens = Item.objects.filter(isbn__regex=r'-')

        if not items_with_hyphens.exists():
            self.stdout.write(self.style.SUCCESS("No items found with hyphens in ISBN"))
            return

        self.stdout.write(f"Found {items_with_hyphens.count()} items with hyphens in ISBN")

        fixed_count = 0
        cover_refetched_count = 0

        for item in items_with_hyphens:
            old_isbn = item.isbn
            # Clean the ISBN
            clean_isbn = BookCoverService.normalize_isbn(old_isbn)

            if clean_isbn != old_isbn:
                item.isbn = clean_isbn
                item.isbn_lookup_attempted = False  # Reset so it will try again
                item.save(update_fields=['isbn', 'isbn_lookup_attempted'])

                self.stdout.write(
                    self.style.SUCCESS(f"Cleaned ISBN for '{item.title}': {old_isbn} -> {clean_isbn}")
                )

                # Re-fetch cover
                success, message = BookCoverService.process_item_cover(item)
                if success:
                    cover_refetched_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"Re-fetched cover for '{item.title}': {message}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"Failed to re-fetch cover for '{item.title}': {message}")
                    )

                fixed_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted! Fixed {fixed_count} ISBNs, re-fetched {cover_refetched_count} covers."
            )
        )
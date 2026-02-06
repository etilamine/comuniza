"""
Management command to fetch book covers for items with ISBN.
"""

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from apps.items.models import Item
from apps.books.services import BookCoverService


class Command(BaseCommand):
    help = 'Fetch book covers for items with ISBN'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of items to process'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force refetch even if cover already exists'
        )
        parser.add_argument(
            '--source',
            type=str,
            default='openlibrary',
            choices=['openlibrary'],
            help='Cover source to use'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        force = options['force']
        source = options['source']
        
        self.stdout.write(f"📚 Fetching book covers (limit: {limit}, force: {force})")
        
        # Get items with ISBN but no cover
        queryset = Item.objects.filter(
            isbn__isnull=False
        ).exclude(isbn='')
        
        if not force:
            queryset = queryset.filter(images__isnull=True)
        
        items = queryset[:limit]
        
        if not items.exists():
            self.stdout.write(
                self.style.WARNING("No items found that need cover fetching")
            )
            return
        
        self.stdout.write(f"Processing {items.count()} items...")
        
        success_count = 0
        error_count = 0
        skip_count = 0
        
        for i, item in enumerate(items, 1):
            status = f"[{i}/{items.count()}] Processing: {item.title[:50]}..."
            
            # Check if user already uploaded cover
            if item.images.filter(is_primary=True).exists():
                self.stdout.write(
                    self.style.WARNING(f"{status} SKIPPED (user has cover)")
                )
                skip_count += 1
                continue
            
            # Process cover
            success, message = BookCoverService.process_item_cover(item)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f"{status} ✅ {message}")
                )
                success_count += 1
            else:
                self.stdout.write(
                    self.style.ERROR(f"{status} ❌ {message}")
                )
                error_count += 1
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(f"📊 SUMMARY:")
        self.stdout.write(f"  ✅ Successfully processed: {success_count}")
        self.stdout.write(f"  ❌ Errors: {error_count}")
        self.stdout.write(f"  ⏭️ Skipped: {skip_count}")
        self.stdout.write(f"  📚 Total: {items.count()}")
        
        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n🎉 Book cover fetching completed successfully!")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"\n⚠️  No covers were fetched. Check ISBN formats and API availability.")
            )
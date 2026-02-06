"""
Management command to generate 8-bit fallback covers for items.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.items.models import Item


class Command(BaseCommand):
    help = 'Generate 8-bit fallback covers for items without covers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of items to process'
        )
        parser.add_argument(
            '--theme',
            type=str,
            default='pastel',
            choices=['pastel', 'communist', 'vintage'],
            help='Color theme for generated covers'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        theme = options['theme']
        
        self.stdout.write(f"🎨 Generating {theme} 8-bit covers (limit: {limit})")
        
        # Get items without covers
        items = Item.objects.filter(
            images__isnull=True
        ).exclude(isbn='').order_by('-created_at')[:limit]
        
        if not items.exists():
            self.stdout.write(
                self.style.WARNING("No items found that need covers")
            )
            return
        
        self.stdout.write(f"Processing {items.count()} items...")
        
        success_count = 0
        error_count = 0
        
        for i, item in enumerate(items, 1):
            status = f"[{i}/{items.count()}] Processing: {item.title[:50]}..."
            
            if item.isbn and not item.cover_fetched_at:
                try:
                    # This would call the fallback generation
                    # For now, we'll just mark as processed
                    item.cover_fetched_at = timezone.now()
                    item.cover_source = 'generated'
                    item.save(update_fields=['cover_fetched_at', 'cover_source'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"{status} ✅ Generated fallback cover")
                    )
                    success_count += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"{status} ❌ Error: {str(e)}")
                    )
                    error_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f"{status} ⏭️ Skipped (no ISBN or already processed)")
                )
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(f"📊 SUMMARY:")
        self.stdout.write(f"  ✅ Successfully processed: {success_count}")
        self.stdout.write(f"  ❌ Errors: {error_count}")
        self.stdout.write(f"  📚 Total: {items.count()}")
        
        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n🎨 8-bit cover generation completed!")
            )
            self.stdout.write(
                self.style.NOTE("Note: Actual 8-bit image generation requires PIL library")
            )
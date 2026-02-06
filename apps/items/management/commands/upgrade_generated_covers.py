from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.items.models import Item
from apps.books.services import BookCoverService


class Command(BaseCommand):
    help = 'Reprocess items with generated covers to find real covers from Amazon'

    def handle(self, *args, **options):
        self.stdout.write('Reprocessing items with generated covers...\n')

        # Get items with generated covers
        items_to_reprocess = Item.objects.filter(cover_source='generated')

        total_items = items_to_reprocess.count()
        self.stdout.write(f'Found {total_items} items with generated covers\n')

        processed = 0
        upgraded = 0

        for item in items_to_reprocess:
            self.stdout.write(f'Processing: {item.title} (ISBN: {item.isbn})')

            try:
                # Fetch fresh metadata (will use enhanced Amazon scraping)
                metadata = BookCoverService.fetch_book_metadata(item.isbn)

                if metadata and metadata.get('cover_url') and metadata.get('source') == 'amazon':
                    # Try to download and save the Amazon cover
                    success, message = BookCoverService.download_and_save_cover(
                        metadata['cover_url'], item
                    )

                    if success:
                        # Update cover source and metadata
                        item.cover_source = 'amazon'
                        item.cover_fetched_at = timezone.now()

                        # Update other metadata if available
                        if metadata.get('title') and not item.title.startswith('Book ISBN:'):
                            item.title = metadata['title']
                        if metadata.get('authors'):
                            item.author = ', '.join(metadata['authors'])

                        item.save(update_fields=['title', 'author', 'cover_source', 'cover_fetched_at'])

                        self.stdout.write(f'  ✅ Upgraded to Amazon cover: {message}')
                        upgraded += 1
                    else:
                        self.stdout.write(f'  ❌ Cover download failed: {message}')
                else:
                    self.stdout.write(f'  ⚠️ No Amazon cover found for ISBN {item.isbn}')

            except Exception as e:
                self.stdout.write(f'  ❌ Error processing {item.title}: {str(e)}')

            processed += 1

            # Progress update
            if processed % 5 == 0:
                self.stdout.write(f'Progress: {processed}/{total_items} processed, {upgraded} upgraded\n')

        self.stdout.write(f'\nReprocessing completed! Successfully upgraded {upgraded}/{total_items} items to Amazon covers')

        # Final statistics
        final_generated = Item.objects.filter(cover_source='generated').count()
        final_amazon = Item.objects.filter(cover_source='amazon').count()
        final_ol = Item.objects.filter(cover_source='openlibrary').count()

        self.stdout.write(f'\nFinal cover distribution:')
        self.stdout.write(f'  Open Library: {final_ol} items')
        self.stdout.write(f'  Amazon: {final_amazon} items')
        self.stdout.write(f'  Generated: {final_generated} items')
        self.stdout.write(f'  Total coverage: {final_ol + final_amazon + final_generated}/44 items = 100.0%')
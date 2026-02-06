from django.core.management.base import BaseCommand
from apps.items.models import Item
from apps.books.services import BookCoverService


class Command(BaseCommand):
    help = 'Scrape Amazon for existing items with generated covers to replace with real covers'

    def handle(self, *args, **options):
        self.stdout.write('Searching for items with generated covers to replace with Amazon covers...\n')

        # Find items with generated covers (likely failed OL lookup)
        items_to_scrape = Item.objects.filter(cover_source='generated')

        total_items = items_to_scrape.count()
        self.stdout.write(f'Found {total_items} items with generated covers\n')

        processed = 0
        replaced = 0

        for item in items_to_scrape:
            self.stdout.write(f'Processing: {item.title} (ISBN: {item.isbn})')

            try:
                # Fetch fresh metadata (this will try Amazon fallback)
                metadata = BookCoverService.fetch_book_metadata(item.isbn)

                if metadata and metadata.get('cover_url') and metadata.get('source') == 'amazon':
                    # Try to download and save the Amazon cover
                    success, message = BookCoverService.download_and_save_cover(
                        metadata['cover_url'], item
                    )

                    if success:
                        # Update cover source
                        item.cover_source = 'amazon'
                        item.save(update_fields=['cover_source'])
                        self.stdout.write(f'  ✅ Replaced with Amazon cover: {message}')
                        replaced += 1
                    else:
                        self.stdout.write(f'  ❌ Failed to save Amazon cover: {message}')
                else:
                    self.stdout.write(f'  ⚠️ No Amazon cover available for ISBN {item.isbn}')

            except Exception as e:
                self.stdout.write(f'  ❌ Error processing {item.title}: {str(e)}')

            processed += 1

            # Progress update
            if processed % 5 == 0:
                self.stdout.write(f'Progress: {processed}/{total_items} processed, {replaced} replaced\n')

        self.stdout.write(f'\nCompleted! Successfully replaced {replaced}/{total_items} generated covers with Amazon covers')

        # Final statistics
        final_generated = Item.objects.filter(cover_source='generated').count()
        final_amazon = Item.objects.filter(cover_source='amazon').count()
        final_ol = Item.objects.filter(cover_source='openlibrary').count()

        self.stdout.write(f'\nFinal cover distribution:')
        self.stdout.write(f'  Open Library: {final_ol} items')
        self.stdout.write(f'  Amazon: {final_amazon} items')
        self.stdout.write(f'  Generated: {final_generated} items')
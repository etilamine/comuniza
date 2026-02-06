from django.core.management.base import BaseCommand
from apps.items.models import Item
from apps.books.services import BookCoverService


class Command(BaseCommand):
    help = 'Retrieve cover art for existing items that have ISBN but no cover image'

    def handle(self, *args, **options):
        self.stdout.write('Starting cover art retrieval for existing items...\n')

        # Get items that have ISBN but no primary image
        items_to_process = Item.objects.filter(
            isbn__isnull=False,
            isbn__gt=''
        ).exclude(
            images__is_primary=True
        ).distinct()

        total_items = items_to_process.count()
        self.stdout.write(f'Found {total_items} items to process\n')

        processed = 0
        successful = 0

        for item in items_to_process:
            self.stdout.write(f'Processing: {item.title} (ISBN: {item.isbn})')

            try:
                # Try to get cover from ISBN lookup
                metadata = BookCoverService.fetch_book_metadata(item.isbn)

                if metadata and metadata.get('cover_url'):
                    # Use the cover_url from metadata (already selected by fetch_book_metadata)
                    cover_url = metadata['cover_url']

                    # Try to download and save the cover
                    success, message = BookCoverService.download_and_save_cover(
                        cover_url, item
                    )

                    if success:
                        self.stdout.write(f'  ✅ Cover saved: {message}')
                        successful += 1
                    else:
                        self.stdout.write(f'  ❌ Failed to save cover: {message}')
                else:
                    self.stdout.write(f'  ⚠️ No cover found for ISBN {item.isbn}')

            except Exception as e:
                self.stdout.write(f'  ❌ Error processing {item.title}: {str(e)}')

            processed += 1

            # Progress update every 10 items
            if processed % 10 == 0:
                self.stdout.write(f'Progress: {processed}/{total_items} items processed\n')

        self.stdout.write(f'\nCompleted! Successfully added covers to {successful}/{total_items} items')
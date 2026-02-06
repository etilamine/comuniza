from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.items.models import TempItemImage


class Command(BaseCommand):
    help = 'Cleanup temporary images older than 24 hours'
    
    def handle(self, *args, **options):
        cutoff = timezone.now() - timezone.timedelta(hours=24)
        deleted_count, _ = TempItemImage.objects.filter(uploaded_at__lt=cutoff).delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Deleted {deleted_count} temporary images')
        )
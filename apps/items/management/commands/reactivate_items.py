"""
Management command to reactivate inactive items.
"""

from django.core.management.base import BaseCommand

from apps.items.models import Item


class Command(BaseCommand):
    help = "Reactivate all inactive items"

    def handle(self, *args, **options):
        inactive_items = Item.objects.filter(is_active=False)

        if not inactive_items.exists():
            self.stdout.write(
                self.style.SUCCESS("No inactive items found.")
            )
            return

        count = inactive_items.update(is_active=True)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully reactivated {count} items:")
        )

        for item in inactive_items:
            self.stdout.write(f"  - {item.identifier}: {item.title}")

        self.stdout.write(
            self.style.SUCCESS("All items are now active.")
        )
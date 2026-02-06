"""Management command to sync item statuses with loan states."""
from django.core.management.base import BaseCommand
from apps.items.models import Item
from apps.loans.models import Loan


class Command(BaseCommand):
    help = 'Sync item statuses with loan states'

    def handle(self, *args, **options):
        self.stdout.write("Syncing item statuses with loan states...")

        # Find items that have active loans but aren't marked as borrowed
        items_needing_borrowed = Item.objects.filter(
            loans__status='active'
        ).exclude(status='borrowed').distinct()

        # Find items marked as borrowed but have no active loans
        items_needing_available = Item.objects.filter(
            status='borrowed'
        ).exclude(
            loans__status='active'
        ).distinct()

        total_updates = 0

        if items_needing_borrowed.exists():
            self.stdout.write(
                f"🔧 Found {items_needing_borrowed.count()} items that should be 'borrowed'"
            )

            for item in items_needing_borrowed:
                active_loan = item.loans.filter(
                    status__in=['approved', 'active']
                ).first()

                if active_loan:
                    item.status = 'borrowed'
                    item.current_borrower = active_loan.borrower
                    item.save()
                    total_updates += 1
                    self.stdout.write(
                        f"✅ Updated {item.identifier}: {item.title} status to 'borrowed'"
                    )

        if items_needing_available.exists():
            self.stdout.write(
                f"🔧 Found {items_needing_available.count()} items that should be 'available'"
            )

            for item in items_needing_available:
                item.status = 'available'
                item.current_borrower = None
                item.save()
                total_updates += 1
                self.stdout.write(
                    f"✅ Updated {item.identifier}: {item.title} status to 'available'"
                )

        if total_updates == 0:
            self.stdout.write("✅ No items needing status sync found")
        else:
            self.stdout.write(f"✅ Status sync completed. Updated {total_updates} items.")

        self.stdout.write("Status sync completed.")
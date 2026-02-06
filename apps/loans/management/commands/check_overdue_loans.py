"""Management command to check overdue loans."""
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.loans.models import Loan


class Command(BaseCommand):
    help = 'Check for overdue loans and send reminders'

    def handle(self, *args, **options):
        self.stdout.write("Checking for overdue loans...")
        
        # Get all overdue active/approved loans
        overdue_loans = Loan.objects.filter(
            status__in=['active', 'approved'],
            due_date__lt=timezone.now().date()
        ).select_related('borrower', 'item', 'lender')
        
        if overdue_loans.exists():
            self.stdout.write(
                f"⚠️  Found {overdue_loans.count()} overdue loan(s):"
            )
            
            for loan in overdue_loans:
                days_overdue = loan.days_overdue
                self.stdout.write(
                    f"  - {loan.item.title} (Borrower: {loan.borrower.get_display_name()}) "
                    f"is {days_overdue} days overdue (Due: {loan.due_date})"
                )
        else:
            self.stdout.write("✅ No overdue loans found")
        
        self.stdout.write("Overdue check completed.")
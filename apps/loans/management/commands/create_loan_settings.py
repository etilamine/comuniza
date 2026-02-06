"""
Management command to create UserLoanSettings for existing users.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.loans.models import UserLoanSettings


class Command(BaseCommand):
    help = 'Create UserLoanSettings for all existing users'

    def handle(self, *args, **options):
        User = get_user_model()
        users_created = 0
        users_existing = 0
        
        self.stdout.write("Creating UserLoanSettings for existing users...")
        
        for user in User.objects.all():
            settings, created = UserLoanSettings.objects.get_or_create(user=user)
            if created:
                users_created += 1
                self.stdout.write(f"✅ Created settings for {user.email}")
            else:
                users_existing += 1
                self.stdout.write(f"ℹ️ Settings already exist for {user.email}")
        
        self.stdout.write(
            f"✅ Completed! Created: {users_created}, Already existed: {users_existing}"
        )
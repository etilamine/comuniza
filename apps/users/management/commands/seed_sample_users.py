"""
Management command to seed sample users with realistic data.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.groups.models import Group, GroupMembership

User = get_user_model()


class Command(BaseCommand):
    help = "Seed sample users with realistic data for testing"

    def handle(self, *args, **options):
        # Sample users with realistic data
        sample_users = [
            {
                "email": "anna.schmidt@example.com",
                "first_name": "Anna",
                "last_name": "Schmidt",
                "username": "anna_schmidt",
                "city": "Berlin",
                "country": "Germany",
            },
            {
                "email": "marcus.mueller@example.com",
                "first_name": "Marcus",
                "last_name": "Mueller",
                "username": "marcus_mueller",
                "city": "Munich",
                "country": "Germany",
            },
            {
                "email": "lena.wagner@example.com",
                "first_name": "Lena",
                "last_name": "Wagner",
                "username": "lena_wagner",
                "city": "Hamburg",
                "country": "Germany",
            },
            {
                "email": "tobias.fischer@example.com",
                "first_name": "Tobias",
                "last_name": "Fischer",
                "username": "tobias_fischer",
                "city": "Cologne",
                "country": "Germany",
            },
            {
                "email": "sara.becker@example.com",
                "first_name": "Sara",
                "last_name": "Becker",
                "username": "sara_becker",
                "city": "Frankfurt",
                "country": "Germany",
            },
            {
                "email": "lukas.hoffmann@example.com",
                "first_name": "Lukas",
                "last_name": "Hoffmann",
                "username": "lukas_hoffmann",
                "city": "Dresden",
                "country": "Germany",
            },
            {
                "email": "julia.schulz@example.com",
                "first_name": "Julia",
                "last_name": "Schulz",
                "username": "julia_schulz",
                "city": "Leipzig",
                "country": "Germany",
            },
            {
                "email": "alexander.krause@example.com",
                "first_name": "Alexander",
                "last_name": "Krause",
                "username": "alexander_krause",
                "city": "Berlin",
                "country": "Germany",
            },
            {
                "email": "emma.koch@example.com",
                "first_name": "Emma",
                "last_name": "Koch",
                "username": "emma_koch",
                "city": "Munich",
                "country": "Germany",
            },
            {
                "email": "david.richter@example.com",
                "first_name": "David",
                "last_name": "Richter",
                "username": "david_richter",
                "city": "Hamburg",
                "country": "Germany",
            },
        ]

        created_count = 0
        updated_count = 0

        for user_data in sample_users:
            user, created = User.objects.get_or_create(
                email=user_data["email"],
                defaults={
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "username": user_data["username"],
                    "is_active": True,
                    "profile_visibility": "public",
                    "email_visibility": "private",
                },
            )

            if created:
                user.set_password("password123")
                user.save()
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created user: {user_data['email']}")
                )

                # Add user to appropriate group based on city
                group_name_map = {
                    "Berlin": "Berlin Book Collective",
                    "Munich": "Munich Readers Circle",
                    "Hamburg": "Hamburg Library Commune",
                    "Cologne": "Cologne Book Exchange",
                    "Frankfurt": "Frankfurt Literary Collective",
                    "Dresden": "Dresden Reading Community",
                    "Leipzig": "Leipzig Book Commons",
                }

                group_name = group_name_map.get(user_data["city"])
                if group_name:
                    try:
                        group = Group.objects.get(name=group_name)
                        GroupMembership.objects.get_or_create(
                            group=group,
                            user=user,
                            defaults={"role": "member", "status": "active"},
                        )
                        self.stdout.write(
                            self.style.SUCCESS(f"Added {user.email} to {group_name}")
                        )
                    except Group.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f"Group {group_name} not found for {user.email}")
                        )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"User {user_data['email']} already exists")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nUser seeding complete! Created {created_count} users, updated {updated_count} users."
            )
        )
        self.stdout.write(
            self.style.SUCCESS("All users have password: password123")
        )
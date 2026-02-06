"""
Management command to seed sample groups with location data.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.groups.models import Group, GroupMembership

User = get_user_model()


class Command(BaseCommand):
    help = "Seed sample groups with location data for testing the map"

    def handle(self, *args, **options):
        # Get or create a sample user
        user, created = User.objects.get_or_create(
            email="admin@comuniza.org",
            defaults={
                "first_name": "Admin",
                "last_name": "User",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )

        if created:
            user.set_password("admin123")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user"))

        # Sample groups with real German cities
        sample_groups = [
            {
                "name": "Berlin Book Collective",
                "description": "A community of book lovers in Berlin sharing their favorite reads.",
                "city": "Berlin",
                "state": "Berlin",
                "country": "Germany",
                "latitude": 52.520008,
                "longitude": 13.404954,
                "privacy": "public",
            },
            {
                "name": "Munich Readers Circle",
                "description": "Share and borrow books in the heart of Bavaria.",
                "city": "Munich",
                "state": "Bavaria",
                "country": "Germany",
                "latitude": 48.137154,
                "longitude": 11.576124,
                "privacy": "public",
            },
            {
                "name": "Hamburg Library Commune",
                "description": "Building a people's library, one book at a time.",
                "city": "Hamburg",
                "state": "Hamburg",
                "country": "Germany",
                "latitude": 53.551086,
                "longitude": 9.993682,
                "privacy": "public",
            },
            {
                "name": "Cologne Book Exchange",
                "description": "Free access to books for all Cologne residents.",
                "city": "Cologne",
                "state": "North Rhine-Westphalia",
                "country": "Germany",
                "latitude": 50.937531,
                "longitude": 6.960279,
                "privacy": "public",
            },
            {
                "name": "Frankfurt Literary Collective",
                "description": "Share knowledge, share books, build community.",
                "city": "Frankfurt",
                "state": "Hesse",
                "country": "Germany",
                "latitude": 50.110924,
                "longitude": 8.682127,
                "privacy": "public",
            },
            {
                "name": "Dresden Reading Community",
                "description": "A solidarity-based book sharing network in Dresden.",
                "city": "Dresden",
                "state": "Saxony",
                "country": "Germany",
                "latitude": 51.050409,
                "longitude": 13.737262,
                "privacy": "request",
            },
            {
                "name": "Leipzig Book Commons",
                "description": "From each according to ability, to each according to need.",
                "city": "Leipzig",
                "state": "Saxony",
                "country": "Germany",
                "latitude": 51.339695,
                "longitude": 12.373075,
                "privacy": "public",
            },
        ]

        created_count = 0
        updated_count = 0

        for group_data in sample_groups:
            group, created = Group.objects.update_or_create(
                slug=group_data["name"].lower().replace(" ", "-"),
                defaults={
                    "name": group_data["name"],
                    "description": group_data["description"],
                    "city": group_data["city"],
                    "state": group_data["state"],
                    "country": group_data["country"],
                    "latitude": group_data["latitude"],
                    "longitude": group_data["longitude"],
                    "privacy": group_data["privacy"],
                    "owner": user,
                    "is_active": True,
                },
            )

            # Add owner as member
            GroupMembership.objects.get_or_create(
                group=group,
                user=user,
                defaults={"role": "admin", "status": "active"},
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created group: {group_data['name']}")
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"Updated group: {group_data['name']}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeeding complete! Created {created_count} groups, updated {updated_count} groups."
            )
        )
        self.stdout.write(
            self.style.SUCCESS("\nYou can now view the map at http://localhost:8000/")
        )
        self.stdout.write(
            self.style.SUCCESS("Admin credentials: admin@comuniza.org / admin123")
        )

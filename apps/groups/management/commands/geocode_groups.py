"""
Management command to geocode existing groups that don't have coordinates.
"""

from django.core.management.base import BaseCommand
from apps.groups.models import Group
from apps.groups.views import geocode_location


class Command(BaseCommand):
    help = 'Geocode existing groups to populate latitude/longitude coordinates'

    def handle(self, *args, **options):
        """Geocode groups without coordinates."""
        groups_without_coords = Group.objects.filter(
            latitude__isnull=True,
            longitude__isnull=True,
            is_active=True
        ).exclude(city="Unknown")

        self.stdout.write(f"Found {groups_without_coords.count()} groups without coordinates")

        geocoded_count = 0
        for group in groups_without_coords:
            location_string = f"{group.city}, {group.state or ''}, {group.country}".strip(', ')
            self.stdout.write(f"Geocoding: {location_string}")

            coordinates = geocode_location(group.city, group.state, group.country)
            if coordinates:
                group.latitude = coordinates['lat']
                group.longitude = coordinates['lng']
                group.save()
                geocoded_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Geocoded {group.name}: {coordinates['lat']}, {coordinates['lng']}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"✗ Failed to geocode {group.name}")
                )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully geocoded {geocoded_count} groups")
        )

        # Clear cache to refresh map data
        from apps.core.ultra_cache import get_ultimate_cache
        cache = get_ultimate_cache()
        cache_key = cache.generate_cache_key('group_locations_api')
        cache.delete(cache_key)
        self.stdout.write("Cleared map cache")
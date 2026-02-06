"""
Management command to seed communist-themed badges for Comuniza.
"""

from django.core.management.base import BaseCommand

from apps.badges.models import Badge, Achievement


class Command(BaseCommand):
    help = "Seed communist-themed badges and achievements"

    def handle(self, *args, **options):
        # Define communist-themed badges
        badges_data = [
            # Lending Badges
            {
                "name": "Comrade",
                "slug": "comrade",
                "description": "Shared your first item with the community",
                "icon": "fas fa-hands-helping",
                "badge_type": "bronze",
                "category": "lending",
                "points": 10,
                "display_order": 1,
            },
            {
                "name": "Library Hero",
                "slug": "library-hero",
                "description": "Shared 10 items with the community",
                "icon": "fas fa-book-open",
                "badge_type": "silver",
                "category": "lending",
                "points": 50,
                "display_order": 2,
            },
            {
                "name": "Benefactor",
                "slug": "benefactor",
                "description": "Shared 25 items with the community",
                "icon": "fas fa-gift",
                "badge_type": "gold",
                "category": "lending",
                "points": 150,
                "display_order": 3,
            },
            {
                "name": "Collective Spirit",
                "slug": "collective-spirit",
                "description": "Shared 50+ items with the community",
                "icon": "fas fa-infinity",
                "badge_type": "platinum",
                "category": "lending",
                "points": 300,
                "display_order": 4,
            },
            
            # Borrowing Badges
            {
                "name": "Curious Mind",
                "slug": "curious-mind",
                "description": "Borrowed your first item",
                "icon": "fas fa-search",
                "badge_type": "bronze",
                "category": "borrowing",
                "points": 5,
                "display_order": 10,
            },
            {
                "name": "Knowledge Seeker",
                "slug": "knowledge-seeker",
                "description": "Borrowed 10 different items",
                "icon": "fas fa-graduation-cap",
                "badge_type": "silver",
                "category": "borrowing",
                "points": 25,
                "display_order": 11,
            },
            {
                "name": "Well-Read Comrade",
                "slug": "well-read-comrade",
                "description": "Borrowed 25 different items",
                "icon": "fas fa-book-reader",
                "badge_type": "gold",
                "category": "borrowing",
                "points": 100,
                "display_order": 12,
            },
            
            # Community Badges
            {
                "name": "Group Member",
                "slug": "group-member",
                "description": "Joined your first group",
                "icon": "fas fa-users",
                "badge_type": "bronze",
                "category": "community",
                "points": 5,
                "display_order": 20,
            },
            {
                "name": "Community Builder",
                "slug": "community-builder",
                "description": "Joined 5 different groups",
                "icon": "fas fa-city",
                "badge_type": "silver",
                "category": "community",
                "points": 30,
                "display_order": 21,
            },
            {
                "name": "Local Organizer",
                "slug": "local-organizer",
                "description": "Created your first group",
                "icon": "fas fa-flag",
                "badge_type": "silver",
                "category": "community",
                "points": 40,
                "display_order": 22,
            },
            
            # Reputation Badges
            {
                "name": "Reliable Comrade",
                "slug": "reliable-comrade",
                "description": "Maintained 5.0 average rating over 10 reviews",
                "icon": "fas fa-star",
                "badge_type": "silver",
                "category": "reputation",
                "points": 75,
                "display_order": 30,
            },
            {
                "name": "Trusted Member",
                "slug": "trusted-member",
                "description": "Achieved 90+ trust score",
                "icon": "fas fa-shield-alt",
                "badge_type": "gold",
                "category": "reputation",
                "points": 125,
                "display_order": 31,
            },
            {
                "name": "Revolutionary",
                "slug": "revolutionary",
                "description": "Achieved 95+ trust score with 50+ reviews",
                "icon": "fas fa-crown",
                "badge_type": "platinum",
                "category": "reputation",
                "points": 500,
                "display_order": 32,
            },
            
            # Special Badges
            {
                "name": "Early Adopter",
                "slug": "early-adopter",
                "description": "Joined Comuniza in the first month",
                "icon": "fas fa-rocket",
                "badge_type": "special",
                "category": "special",
                "points": 100,
                "display_order": 40,
                "is_secret": True,
            },
            {
                "name": "Marxist Scholar",
                "slug": "marxist-scholar",
                "description": "Borrowed 5+ classic Marxist texts",
                "icon": "fas fa-hammer-sickle",
                "badge_type": "gold",
                "category": "special",
                "points": 80,
                "display_order": 41,
            },
            {
                "name": "Anarchist at Heart",
                "slug": "anarchist-at-heart",
                "description": "Borrowed 5+ anarchist classics",
                "icon": "fas fa-fist-raised",
                "badge_type": "gold",
                "category": "special",
                "points": 80,
                "display_order": 42,
            },
            {
                "name": "Utopian Dreamer",
                "slug": "utopian-dreamer",
                "description": "Borrowed 5+ utopian fiction works",
                "icon": "fas fa-rainbow",
                "badge_type": "gold",
                "category": "special",
                "points": 80,
                "display_order": 43,
            },
        ]

        created_count = 0
        updated_count = 0

        for badge_data in badges_data:
            badge, created = Badge.objects.update_or_create(
                slug=badge_data["slug"],
                defaults=badge_data,
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created badge: {badge.name}")
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"Updated badge: {badge.name}")
                )

        # Create achievements for each badge
        achievements_data = [
            # Lending achievements
            {"badge_slug": "comrade", "trigger_type": "item_shared", "threshold_value": 1},
            {"badge_slug": "library-hero", "trigger_type": "item_shared", "threshold_value": 10},
            {"badge_slug": "benefactor", "trigger_type": "item_shared", "threshold_value": 25},
            {"badge_slug": "collective-spirit", "trigger_type": "item_shared", "threshold_value": 50},
            
            # Borrowing achievements
            {"badge_slug": "curious-mind", "trigger_type": "loan_completed", "threshold_value": 1},
            {"badge_slug": "knowledge-seeker", "trigger_type": "loan_completed", "threshold_value": 10},
            {"badge_slug": "well-read-comrade", "trigger_type": "loan_completed", "threshold_value": 25},
            
            # Community achievements
            {"badge_slug": "group-member", "trigger_type": "group_joined", "threshold_value": 1},
            {"badge_slug": "community-builder", "trigger_type": "group_joined", "threshold_value": 5},
            
            # Reputation achievements
            {"badge_slug": "reliable-comrade", "trigger_type": "threshold_reached", "conditions": {"type": "rating", "value": 5.0, "min_reviews": 10}},
            {"badge_slug": "trusted-member", "trigger_type": "threshold_reached", "conditions": {"type": "trust_score", "value": 90}},
            {"badge_slug": "revolutionary", "trigger_type": "threshold_reached", "conditions": {"type": "trust_score", "value": 95, "min_reviews": 50}},
        ]

        for achievement_data in achievements_data:
            try:
                badge = Badge.objects.get(slug=achievement_data["badge_slug"])
                achievement, created = Achievement.objects.get_or_create(
                    badge=badge,
                    trigger_type=achievement_data["trigger_type"],
                    defaults={
                        "threshold_value": achievement_data.get("threshold_value"),
                        "conditions": achievement_data.get("conditions", {}),
                    },
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Created achievement for: {badge.name}")
                    )

            except Badge.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Badge not found: {achievement_data['badge_slug']}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nBadges seeding complete! Created {created_count} badges, updated {updated_count} badges."
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Communist-themed badge system is ready! 🏆"
            )
        )
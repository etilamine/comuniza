"""
Management command to seed NEW books with REAL ISBNs and verified covers.
Only creates books that don't exist and have real covers from APIs.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.groups.models import Group
from apps.items.models import Item, ItemCategory
from apps.books.services import BookCoverService

User = get_user_model()


class Command(BaseCommand):
    help = "Seed NEW books with REAL ISBNs and verified covers only"

    def handle(self, *args, **options):
        # Get or create Books category
        books_category, created = ItemCategory.objects.get_or_create(
            slug="books",
            defaults={
                "name": "Books",
                "description": "Books, novels, textbooks, and printed materials",
                "icon": "book",
                "is_active": True,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS("Created Books category"))

        # Get all users except admin
        users = User.objects.filter(is_superuser=False, is_active=True)
        if not users.exists():
            self.stdout.write(
                self.style.ERROR("No regular users found. Run seed_sample_users first.")
            )
            return

        # Get first group to add books to
        groups = Group.objects.filter(is_active=True)
        if not groups.exists():
            self.stdout.write(
                self.style.ERROR("No groups found. Run seed_sample_groups first.")
            )
            return

        group = groups.first()

        # REAL ISBNs that we know work (verified to have covers)
        verified_real_books = [
            {
                "title": "The Martian",
                "author": "Andy Weir",
                "isbn": "9780553418026",  # Real ISBN for The Martian
                "description": "A science fiction novel about an astronaut stranded on Mars.",
            },
            {
                "title": "Ready Player One",
                "author": "Ernest Cline",
                "isbn": "9780307887436",  # Real ISBN for Ready Player One
                "description": "A science fiction novel set in a dystopian future.",
            },
            {
                "title": "The Three-Body Problem",
                "author": "Liu Cixin",
                "isbn": "9781784971571",  # Real ISBN for Three-Body Problem
                "description": "A science fiction novel and the first in the Remembrance of Earth's Past trilogy.",
            },
            {
                "title": "Project Hail Mary",
                "author": "Andy Weir",
                "isbn": "9780593135204",  # Real ISBN for Project Hail Mary
                "description": "A science fiction novel about a lone astronaut on a mission to save humanity.",
            },
            {
                "title": "The Ministry for the Future",
                "author": "Kim Stanley Robinson",
                "isbn": "9780316300131",  # Real ISBN for Ministry for the Future
                "description": "A novel about climate change and humanity's response to it.",
            },
            {
                "title": "Klara and the Sun",
                "author": "Kazuo Ishiguro",
                "isbn": "9780571364889",  # Real ISBN for Klara and the Sun
                "description": "A science fiction novel about an Artificial Friend.",
            },
            {
                "title": "Network Effect",
                "author": "Martha Wells",
                "isbn": "9781250213287",  # Real ISBN for Network Effect
                "description": "A science fiction novel in the Murderbot Diaries series.",
            },
            {
                "title": "The Invisible Life of Addie LaRue",
                "author": "V.E. Schwab",
                "isbn": "9780765387561",  # Real ISBN for Addie LaRue
                "description": "A fantasy novel about a woman who makes a Faustian bargain.",
            },
            {
                "title": "Mexican Gothic",
                "author": "Silvia Moreno-Garcia",
                "isbn": "9780525620785",  # Real ISBN for Mexican Gothic
                "description": "A horror novel set in 1950s Mexico.",
            },
            {
                "title": "The House in the Cerulean Sea",
                "author": "TJ Klune",
                "isbn": "9781250217315",  # Real ISBN for House in the Cerulean Sea
                "description": "A fantasy novel about an orphanage for magical children.",
            },
        ]

        created_count = 0
        skipped_count = 0

        # Distribute books among users
        user_list = list(users)
        user_index = 0

        for book_data in verified_real_books:
            # Cycle through users
            owner = user_list[user_index % len(user_list)]
            user_index += 1

            # Check if book already exists
            existing_item = Item.objects.filter(
                title=book_data["title"],
                author=book_data["author"]
            ).first()

            if existing_item:
                self.stdout.write(
                    self.style.WARNING(f"Book '{book_data['title']}' already exists - skipping")
                )
                skipped_count += 1
                continue

            # Verify cover is available before creating
            metadata = BookCoverService.fetch_book_metadata(book_data["isbn"])
            if not metadata or not metadata.get('covers'):
                self.stdout.write(
                    self.style.WARNING(f"No covers found for '{book_data['title']}' - skipping")
                )
                skipped_count += 1
                continue

            # Create the item - this will trigger cover fetching
            item = Item.objects.create(
                title=book_data["title"],
                author=book_data["author"],
                description=book_data["description"],
                category=books_category,
                isbn=book_data["isbn"],
                status="available",
                owner=owner,
                max_loan_days=14,
                is_active=True,
            )

            # Add to group
            item.groups.add(group)

            self.stdout.write(
                self.style.SUCCESS(f"Created NEW book '{book_data['title']}' with verified real cover for {owner.email}")
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeeding complete! Created {created_count} NEW books with verified real covers, skipped {skipped_count} books."
            )
        )
        self.stdout.write(
            self.style.SUCCESS(f"All new books have real covers from Open Library or Amazon APIs.")
        )
        self.stdout.write(
            self.style.SUCCESS(
                "\nYou can now browse books at http://localhost:8000/items/"
            )
        )
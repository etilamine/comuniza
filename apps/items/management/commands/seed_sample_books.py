"""
Management command to seed sample books with realistic data.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.groups.models import Group
from apps.items.models import Item, ItemCategory

User = get_user_model()


class Command(BaseCommand):
    help = "Seed sample books with realistic data for testing"

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

        # Get admin user
        try:
            user = User.objects.get(email="admin@comuniza.org")
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("Admin user not found. Run seed_sample_groups first.")
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

        # Sample books with realistic data
        sample_books = [
            {
                "title": "The Dispossessed",
                "author": "Ursula K. Le Guin",
                "publisher": "Harper & Row",
                "year": 1974,
                "isbn": "978-0061054884",
                "description": "A brilliant physicist finds himself torn between an anarchist world and a capitalist society in this profound exploration of freedom, society, and utopia.",
                "condition": "good",
            },
            {
                "title": "Das Kapital",
                "author": "Karl Marx",
                "publisher": "Verlag von Otto Meisner",
                "year": 1867,
                "isbn": "978-0140445688",
                "description": "A foundational theoretical text in materialist philosophy, economics and politics, analyzing capitalism and its effects on labor.",
                "condition": "excellent",
            },
            {
                "title": "Mutual Aid: A Factor of Evolution",
                "author": "Peter Kropotkin",
                "publisher": "William Heinemann",
                "year": 1902,
                "isbn": "978-1604595888",
                "description": "A treatise on cooperation and reciprocity as drivers of evolution, challenging Social Darwinism.",
                "condition": "good",
            },
            {
                "title": "The Conquest of Bread",
                "author": "Peter Kropotkin",
                "publisher": "G. P. Putnam's Sons",
                "year": 1892,
                "isbn": "978-1926958033",
                "description": "An anarchist manifesto advocating for a decentralized economy based on mutual aid, voluntary cooperation, and self-governance.",
                "condition": "fair",
            },
            {
                "title": "Fully Automated Luxury Communism",
                "author": "Aaron Bastani",
                "publisher": "Verso Books",
                "year": 2019,
                "isbn": "978-1786632630",
                "description": "A manifesto for a future society built on radical abundance, enabled by technology and shared resources.",
                "condition": "new",
            },
            {
                "title": "The Right to Be Lazy",
                "author": "Paul Lafargue",
                "publisher": "Charles H. Kerr",
                "year": 1883,
                "isbn": "978-1434452139",
                "description": "A scathing critique of industrial capitalism and the cult of work, advocating for leisure and human fulfillment.",
                "condition": "good",
            },
            {
                "title": "Debt: The First 5000 Years",
                "author": "David Graeber",
                "publisher": "Melville House",
                "year": 2011,
                "isbn": "978-1612194196",
                "description": "An anthropological history of debt, money, and human exchange, challenging conventional economic wisdom.",
                "condition": "excellent",
            },
            {
                "title": "The Ecology of Freedom",
                "author": "Murray Bookchin",
                "publisher": "Cheshire Books",
                "year": 1982,
                "isbn": "978-0981867519",
                "description": "An exploration of the relationship between social hierarchy, domination, and ecological crisis.",
                "condition": "good",
            },
            {
                "title": "Woman on the Edge of Time",
                "author": "Marge Piercy",
                "publisher": "Alfred A. Knopf",
                "year": 1976,
                "isbn": "978-0449210826",
                "description": "A feminist utopian novel depicting a future anarchist society built on equality, sustainability, and communal care.",
                "condition": "good",
            },
            {
                "title": "The Soul of Man Under Socialism",
                "author": "Oscar Wilde",
                "publisher": "Arthur L. Humphreys",
                "year": 1891,
                "isbn": "978-1420952520",
                "description": "A libertarian socialist critique arguing that capitalism suppresses individualism and that socialism would liberate it.",
                "condition": "excellent",
            },
            {
                "title": "Demanding the Impossible",
                "author": "Peter Marshall",
                "publisher": "PM Press",
                "year": 1992,
                "isbn": "978-1604860641",
                "description": "A comprehensive history of anarchist thought from ancient China to the modern era.",
                "condition": "good",
            },
            {
                "title": "The Principle of Hope",
                "author": "Ernst Bloch",
                "publisher": "Suhrkamp Verlag",
                "year": 1959,
                "isbn": "978-0262520370",
                "description": "A monumental philosophical work exploring utopian thinking and the human capacity to imagine better futures.",
                "condition": "fair",
            },
            {
                "title": "Homage to Catalonia",
                "author": "George Orwell",
                "publisher": "Secker and Warburg",
                "year": 1938,
                "isbn": "978-0156421171",
                "description": "A personal account of Orwell's experiences fighting in the Spanish Civil War alongside anarchist militias.",
                "condition": "good",
            },
            {
                "title": "The Communist Manifesto",
                "author": "Karl Marx and Friedrich Engels",
                "publisher": "Penguin Classics",
                "year": 1848,
                "isbn": "978-0140447576",
                "description": "The foundational text of modern communism, calling for working class revolution and the abolition of private property.",
                "condition": "excellent",
            },
            {
                "title": "Utopia",
                "author": "Thomas More",
                "publisher": "Penguin Classics",
                "year": 1516,
                "isbn": "978-0140449105",
                "description": "A work of fiction and political philosophy depicting an ideal island society with common property and rational governance.",
                "condition": "good",
            },
            {
                "title": "News from Nowhere",
                "author": "William Morris",
                "publisher": "Reeves and Turner",
                "year": 1890,
                "isbn": "978-0140433302",
                "description": "A utopian romance envisioning a future socialist society where work is pleasurable and hierarchy has been abolished.",
                "condition": "good",
            },
            {
                "title": "The Principles of Communism",
                "author": "Friedrich Engels",
                "publisher": "Progress Publishers",
                "year": 1847,
                "isbn": "978-1514651827",
                "description": "A brief introduction to communist theory in a question-and-answer format, written as a draft for the Communist Manifesto.",
                "condition": "fair",
            },
            {
                "title": "Fields, Factories and Workshops",
                "author": "Peter Kropotkin",
                "publisher": "Thomas Nelson and Sons",
                "year": 1899,
                "isbn": "978-1926958064",
                "description": "An examination of agriculture, industry, and education in a decentralized communist society.",
                "condition": "good",
            },
            {
                "title": "The Accumulation of Capital",
                "author": "Rosa Luxemburg",
                "publisher": "Routledge",
                "year": 1913,
                "isbn": "978-0415304252",
                "description": "A critique of capitalism's economic imperialism and its inherent need for continuous expansion.",
                "condition": "excellent",
            },
            {
                "title": "Anarchism and Other Essays",
                "author": "Emma Goldman",
                "publisher": "Mother Earth Publishing",
                "year": 1910,
                "isbn": "978-1420941906",
                "description": "A collection of essays on anarchism, feminism, individual liberty, and social revolution.",
                "condition": "good",
            },
        ]

        created_count = 0
        updated_count = 0

        for book_data in sample_books:
            item, created = Item.objects.update_or_create(
                title=book_data["title"],
                author=book_data["author"],
                defaults={
                    "slug": "",  # Will be auto-generated
                    "description": book_data["description"],
                    "category": books_category,
                    "publisher": book_data["publisher"],
                    "isbn": book_data["isbn"],
                    "year": book_data["year"],
                    "condition": book_data["condition"],
                    "status": "available",
                    "owner": user,
                    "max_loan_days": 14,
                    "is_active": True,
                },
            )

            # Add to group
            item.groups.add(group)

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created book: {book_data['title']}")
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"Updated book: {book_data['title']}")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeeding complete! Created {created_count} books, updated {updated_count} books."
            )
        )
        self.stdout.write(
            self.style.SUCCESS(f"Books added to group: {group.name} in {group.city}")
        )
        self.stdout.write(
            self.style.SUCCESS(
                "\nYou can now browse books at http://localhost:8000/items/"
            )
        )

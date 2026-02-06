import random
import secrets
from typing import List, Optional

class UsernameGenerator:
    """
    Generates Reddit-style usernames for privacy.
    Format: [Adjective][Noun][Number]
    Example: BrilliantTiger42, CosmicPanda87
    """

    ADJECTIVES = [
        "Brilliant", "Cosmic", "Daring", "Electric", "Fantastic", "Galactic",
        "Harmonious", "Infinite", "Jubilant", "Kinetic", "Luminous", "Magnetic",
        "Nebulous", "Organic", "Pioneering", "Quantum", "Radiant", "Sonic",
        "Titanium", "Ultimate", "Vibrant", "Wonderful", "Xenon", "Yielding",
        "Zephyr", "Amber", "Bold", "Crimson", "Dynamo", "Echo", "Frost",
        "Glacier", "Horizon", "Ivory", "Jade", "Krypton", "Lavender", "Mystic",
        "Nova", "Opal", "Phoenix", "Quasar", "Ruby", "Sapphire", "Thunder",
        "Unity", "Vortex", "Whisper", "Xenial", "Yonder", "Zesty"
    ]

    NOUNS = [
        "Tiger", "Panda", "Eagle", "Wolf", "Bear", "Lion", "Owl", "Fox",
        "Raven", "Hawk", "Dragon", "Phoenix", "Storm", "River", "Mountain",
        "Forest", "Ocean", "Star", "Moon", "Sun", "Comet", "Galaxy", "Nebula",
        "Aurora", "Thunder", "Lightning", "Crystal", "Diamond", "Ruby", "Pearl",
        "Jade", "Amber", "Copper", "Silver", "Gold", "Platinum", "Iron", "Steel",
        "Bronze", "Titanium", "Zircon", "Quartz", "Marble", "Granite", "Basalt",
        "Coral", "Lagoon", "Canyon", "Valley", "Summit", "Zenith", "Nadir",
        "Equinox", "Solstice", "Horizon", "Zenith", "Cascade", "Tempest",
        "Blizzard", "Monsoon", "Typhoon", "Hurricane", "Tornado", "Cyclone",
        "Avalanche", "Earthquake", "Volcano", "Meteor", "Asteroid", "Satellite",
        "Rocket", "Spaceship", "Astronaut", "Explorer", "Pioneer", "Inventor",
        "Scientist", "Engineer", "Artist", "Musician", "Writer", "Poet"
    ]

    @classmethod
    def generate_username(cls, existing_usernames: Optional[List[str]] = None) -> str:
        """
        Generate a unique username.
        """
        if existing_usernames is None:
            existing_usernames = []

        max_attempts = 100
        for _ in range(max_attempts):
            adjective = random.choice(cls.ADJECTIVES)
            noun = random.choice(cls.NOUNS)
            number = secrets.randbelow(99) + 1  # 1-99

            username = f"{adjective}{noun}{number}"

            if username not in existing_usernames:
                return username

        # Fallback: add timestamp-style suffix
        import time
        timestamp = str(int(time.time()))[-4:]  # Last 4 digits of timestamp
        adjective = random.choice(cls.ADJECTIVES)
        noun = random.choice(cls.NOUNS)
        return f"{adjective}{noun}{timestamp}"

    @classmethod
    def generate_multiple_usernames(cls, count: int = 5, existing_usernames: Optional[List[str]] = None) -> List[str]:
        """
        Generate multiple unique username options.
        """
        if existing_usernames is None:
            existing_usernames = []

        usernames = []
        attempts = 0
        max_total_attempts = count * 20  # Prevent infinite loops

        while len(usernames) < count and attempts < max_total_attempts:
            username = cls.generate_username(existing_usernames + usernames)
            if username not in usernames:
                usernames.append(username)
            attempts += 1

        return usernames

    @classmethod
    def is_valid_username(cls, username: str) -> bool:
        """
        Check if username follows expected format.
        """
        if not username or len(username) < 5 or len(username) > 50:
            return False

        # Should end with number
        if not username[-1].isdigit() or not username[-2].isdigit():
            return False

        # Should contain at least one letter before numbers
        number_start = len(username)
        for i, char in enumerate(username):
            if char.isdigit():
                number_start = i
                break

        if number_start < 3:  # At least 3 characters before numbers
            return False

        return True
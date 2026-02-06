"""
Signals for Users app.
Initialize UserReputation when a new user is created.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_reputation(sender, instance, created, **kwargs):
    """
    Create a UserReputation object when a new user is created.
    This ensures that every user has a reputation record.
    """
    if created:
        from apps.loans.models import UserReputation
        UserReputation.objects.get_or_create(user=instance)


def ready():
    """Initialize signals when the app is ready."""
    pass
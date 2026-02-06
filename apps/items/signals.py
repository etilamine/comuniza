"""
Django signals for Items app.
Handles badge awarding on item creation.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import connection


@receiver(post_save, sender='items.Item')
def on_item_created(sender, instance, created, **kwargs):
    """
    Award badge when an item is created.
    """
    if not created:
        return
    
    # Skip during migrations
    if connection.in_atomic_block:
        return
    
    # Award badge for sharing item
    try:
        from apps.badges.services import BadgeService
        BadgeService.process_item_creation(instance)
    except Exception as e:
        # Log error but don't fail the save
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to award badge for item creation: {e}")

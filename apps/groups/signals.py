"""
Django signals for Groups app.
Handles badge awarding and notification triggers.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import connection


@receiver(post_save)
def on_group_membership_saved(sender, instance, created, **kwargs):
    """
    Handle group membership events.
    Awards badges when users join groups.
    """
    # Check if this is a GroupMembership model
    if sender.__name__ != 'GroupMembership':
        return
    
    if not created:
        return
    
    # Skip during migrations to avoid circular import issues
    if connection.in_atomic_block:
        return
    
    # Award badge on group join
    if instance.status == 'active':
        try:
            from apps.badges.services import BadgeService
            BadgeService.process_group_join(instance.user, instance.group)
        except Exception as e:
            # Log error but don't fail the save
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to award badge for group join: {e}")

"""
Cache invalidation signals for Comuniza.
Automatically invalidates relevant caches when models change.
"""

from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from apps.core.ultra_cache import get_ultimate_cache
from apps.badges.models import Badge, UserBadge, Leaderboard
from apps.items.models import Item, ItemImage, ItemCategory
from apps.groups.models import Group, GroupMembership
from apps.loans.models import Loan, LoanReview


@receiver(post_save, sender=Item)
@receiver(post_delete, sender=Item)
def invalidate_item_caches(sender, instance, **kwargs):
    """Invalidate caches when Item changes."""
    # Invalidate all item-related caches
    get_ultimate_cache().invalidate_pattern('items_list:*')
    get_ultimate_cache().invalidate_pattern(f'item_detail:{instance.id}:*')
    
    # Invalidate user-specific caches
    if instance.owner_id:
        get_ultimate_cache().invalidate_pattern(f'user_item_stats:{instance.owner_id}:*')
    
    # Invalidate category-based caches
    if instance.category_id:
        get_ultimate_cache().invalidate_pattern(f'items_list:category:{instance.category_id}:*')


@receiver(post_save, sender=ItemImage)
@receiver(post_delete, sender=ItemImage)
def invalidate_item_image_caches(sender, instance, **kwargs):
    """Invalidate caches when ItemImage changes."""
    # Invalidate item detail cache
    get_ultimate_cache().invalidate_pattern(f'item_detail:{instance.item_id}:*')
    get_ultimate_cache().invalidate_pattern(f'items_list:*')


@receiver(post_save, sender=ItemCategory)
@receiver(post_delete, sender=ItemCategory)
def invalidate_category_caches(sender, instance, **kwargs):
    """Invalidate caches when ItemCategory changes."""
    # Invalidate all item lists with category filtering
    get_ultimate_cache().invalidate_pattern('items_list:category:*')
    get_ultimate_cache().invalidate_pattern('items_list:*')


@receiver(post_save, sender=UserBadge)
@receiver(post_delete, sender=UserBadge)
def invalidate_user_badge_caches(sender, instance, **kwargs):
    """Invalidate caches when UserBadge changes."""
    # Invalidate user badge caches
    get_ultimate_cache().invalidate_pattern(f'user_badges:{instance.user_id}:*')
    get_ultimate_cache().invalidate_pattern(f'badge_type_count:{instance.user_id}:*')
    get_ultimate_cache().invalidate_pattern(f'total_badge_points:{instance.user_id}:*')
    get_ultimate_cache().invalidate_pattern(f'user_has_badge:{instance.user_id}:*')
    
    # Invalidate leaderboard caches
    get_ultimate_cache().invalidate_pattern('leaderboard:*')
    
    # Invalidate user stats
    get_ultimate_cache().invalidate_pattern(f'user_scores:{instance.user_id}:*')


@receiver(post_save, sender=Leaderboard)
@receiver(post_delete, sender=Leaderboard)
def invalidate_leaderboard_caches(sender, instance, **kwargs):
    """Invalidate caches when Leaderboard changes."""
    # Invalidate all leaderboard caches
    get_ultimate_cache().invalidate_pattern('leaderboard:*')
    
    # Invalidate user stats
    if instance.user_id:
        get_ultimate_cache().invalidate_pattern(f'user_scores:{instance.user_id}:*')


@receiver(post_save, sender=Group)
@receiver(post_delete, sender=Group)
def invalidate_group_caches(sender, instance, **kwargs):
    """Invalidate caches when Group changes."""
    # Invalidate site settings and group-related caches
    get_ultimate_cache().invalidate_pattern('site_settings:*')
    get_ultimate_cache().invalidate_pattern('items_list:group:*')


@receiver(m2m_changed, sender=GroupMembership)
def invalidate_group_membership_caches(sender, instance, action, **kwargs):
    """Invalidate caches when GroupMembership changes."""
    if action in ['post_add', 'post_remove', 'post_clear']:
        # Invalidate user-specific caches
        if hasattr(instance, 'user'):
            get_ultimate_cache().invalidate_pattern(f'user_item_stats:{instance.user.id}:*')
        
        # Invalidate item lists with group filtering
        get_ultimate_cache().invalidate_pattern('items_list:group:*')
        get_ultimate_cache().invalidate_pattern('items_list:*')


@receiver(post_delete, sender=Loan)
def invalidate_loan_caches(sender, instance, **kwargs):
    """Invalidate caches when Loan is deleted."""
    # Invalidate item detail caches (borrower and lender items)
    if instance.item_id:
        get_ultimate_cache().invalidate_pattern(f'item_detail:{instance.item_id}:*')
    
    # Invalidate user item stats for both borrower and lender
    if instance.borrower_id:
        get_ultimate_cache().invalidate_pattern(f'user_item_stats:{instance.borrower_id}:*')
        get_ultimate_cache().invalidate_pattern(f'user_scores:{instance.borrower_id}:*')
    
    if instance.lender_id:
        get_ultimate_cache().invalidate_pattern(f'user_item_stats:{instance.lender_id}:*')
        get_ultimate_cache().invalidate_pattern(f'user_scores:{instance.lender_id}:*')
    
    # Invalidate loan-related caches
    get_ultimate_cache().invalidate_pattern('user_loans:*')
    get_ultimate_cache().invalidate_pattern('my_loans:*')


@receiver(post_save, sender=LoanReview)
@receiver(post_delete, sender=LoanReview)
def invalidate_review_caches(sender, instance, **kwargs):
    """Invalidate caches when LoanReview changes."""
    # Invalidate item detail cache
    if instance.loan_id:
        get_ultimate_cache().invalidate_pattern(f'item_detail:{instance.loan.item_id}:*')
    
    # Invalidate user reputation caches
    if instance.reviewee_id:
        get_ultimate_cache().invalidate_pattern(f'user_scores:{instance.reviewee_id}:*')
        get_ultimate_cache().invalidate_pattern('leaderboard:*')
    
    if instance.reviewer_id:
        get_ultimate_cache().invalidate_pattern(f'user_scores:{instance.reviewer_id}:*')


@receiver(post_save, sender=Badge)
@receiver(post_delete, sender=Badge)
def invalidate_badge_caches(sender, instance, **kwargs):
    """Invalidate caches when Badge changes."""
    # Invalidate all badge-related caches
    get_ultimate_cache().invalidate_pattern('user_badges:*')
    get_ultimate_cache().invalidate_pattern('badge_type_count:*')
    get_ultimate_cache().invalidate_pattern('total_badge_points:*')
    get_ultimate_cache().invalidate_pattern('user_has_badge:*')
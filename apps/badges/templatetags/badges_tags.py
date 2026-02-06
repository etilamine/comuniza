"""
Template tags for badges app.
"""

from django import template
from apps.badges.services import BadgeService
from apps.core.ultra_cache import get_ultimate_cache

register = template.Library()


@register.filter
def get_user_badges(user):
    """Get all badges earned by a user."""
    if not user or not user.is_authenticated:
        return []
    # BadgeService already implements caching
    return BadgeService.get_user_badges(user)

@register.filter  
def badge_count_by_type(user_badges, badge_type):
    """Count badges of specific type."""
    # Cache badge type counts for performance
    cache_key = get_ultimate_cache().generate_cache_key('badge_type_count', user_badges, badge_type)
    
    def loader():
        return user_badges.filter(badge__badge_type=badge_type).count()
    
    return get_ultimate_cache().get(cache_key, loader_func=loader, ttl=1800, segment='warm')

@register.filter
def total_badge_points(user_badges):
    """Calculate total points from all badges."""
    # Cache total points calculation
    cache_key = get_ultimate_cache().generate_cache_key('total_badge_points', user_badges)
    
    def loader():
        return sum(badge.badge.points for badge in user_badges)
    
    return get_ultimate_cache().get(cache_key, loader_func=loader, ttl=1800, segment='warm')

@register.simple_tag
def user_has_badge(user, badge_slug):
    """Check if user has earned a specific badge."""
    if not user or not user.is_authenticated:
        return False
    
    # Cache badge existence check
    cache_key = get_ultimate_cache().generate_cache_key('user_has_badge', user.id, badge_slug)
    
    def loader():
        return user.badges.filter(badge__slug=badge_slug).exists()
    
    return get_ultimate_cache().get(cache_key, loader_func=loader, ttl=900, segment='warm')
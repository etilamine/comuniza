"""
Cache warming utilities for Comuniza.
Pre-warms frequently accessed cache entries for optimal performance.
"""

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from apps.core.ultra_cache import get_ultimate_cache
from apps.badges.services import BadgeService
from apps.items.models import Item, ItemCategory
from apps.groups.models import Group
from apps.loans.models import Loan

User = get_user_model()


class CacheWarmer:
    """Utility class for warming up critical cache entries."""
    
    @staticmethod
    def warm_common_cache_entries():
        """Warm up frequently accessed cache entries."""
        CacheWarmer.warm_item_listings()
        CacheWarmer.warm_categories()
        CacheWarmer.warm_popular_badges()
        CacheWarmer.warm_site_settings()
        
    @staticmethod
    def warm_item_listings():
        """Warm up common item listing queries."""
        pass
        
        # Warm main item list
        cache_key = get_ultimate_cache().generate_cache_key('items_list')
        
        def loader():
            items = list(
                Item.objects.filter(is_active=True)
                .select_related("owner", "category")
                .prefetch_related("images", "groups")
                .order_by("-created_at")[:24]  # First page
            )
            return items
        
        get_ultimate_cache().get(cache_key, loader_func=loader, ttl=900, segment='hot')
        pass
        
        # Warm category-specific listings
        categories = ItemCategory.objects.filter(is_active=True)[:5]
        for category in categories:
            cache_key = get_ultimate_cache().generate_cache_key('items_list', category=category.id)
            
            def category_loader():
                category_items = list(
                    Item.objects.filter(is_active=True, category=category)
                    .select_related("owner", "category")
                    .prefetch_related("images", "groups")
                    .order_by("-created_at")[:24]
                )
                return category_items
            
            get_ultimate_cache().get(cache_key, loader_func=category_loader, ttl=900, segment='warm')
            pass
    
    @staticmethod
    def warm_categories():
        """Warm up active categories cache."""
        pass
        
        # This is typically cached in context processor
        cache_key = get_ultimate_cache().generate_cache_key('active_categories')
        
        def loader():
            return list(ItemCategory.objects.filter(is_active=True))
        
        get_ultimate_cache().get(cache_key, loader_func=loader, ttl=3600, segment='hot')
        pass
    
    @staticmethod
    def warm_popular_badges():
        """Warm up popular badge queries."""
        pass
        
        # Warm leaderboards
        leaderboard_types = ['overall', 'lending', 'reputation']
        for l_type in leaderboard_types:
            BadgeService.get_leaderboard(l_type, limit=10)
            pass
        
        # Warm user badge stats for active users
        active_users = User.objects.filter(is_active=True).annotate(
            item_count=Count('owned_items')
        ).order_by('-item_count')[:10]
        
        for user in active_users:
            BadgeService.get_user_badges(user)
            BadgeService._calculate_leaderboard_scores(user)
            pass
    
    @staticmethod
    def warm_site_settings():
        """Warm up site settings cache."""
        pass
        
        cache_key = get_ultimate_cache().generate_cache_key('site_settings')
        
        def loader():
            try:
                from django.contrib.sites.models import Site
                from django.conf import settings
                site = Site.objects.get_current()
                return {
                    "SITE_NAME": site.name,
                    "SITE_DOMAIN": site.domain,
                    "ENABLE_REGISTRATION": getattr(settings, "ENABLE_REGISTRATION", True),
                    "ENABLE_EMAIL_VERIFICATION": getattr(
                        settings, "ENABLE_EMAIL_VERIFICATION", False
                    ),
                    "DEBUG": settings.DEBUG,
                }
            except Exception:
                from django.conf import settings
                return {
                    "SITE_NAME": getattr(settings, "SITE_NAME", "Comuniza"),
                    "SITE_DOMAIN": getattr(settings, "SITE_DOMAIN", "localhost:8000"),
                    "ENABLE_REGISTRATION": getattr(settings, "ENABLE_REGISTRATION", True),
                    "ENABLE_EMAIL_VERIFICATION": getattr(
                        settings, "ENABLE_EMAIL_VERIFICATION", False
                    ),
                    "DEBUG": settings.DEBUG,
                }
        
        get_ultimate_cache().get(cache_key, loader_func=loader, ttl=3600, segment='hot')
        pass
    
    @staticmethod
    def warm_user_specific_cache(user):
        """Warm up user-specific cache entries."""
        pass
        
        # Warm user item stats
        from apps.items.views import MyItemsView
        request = type('MockRequest', (), {'user': user})()
        my_items_view = MyItemsView()
        my_items_view.request = request
        
        # This will warm the user item stats cache
        try:
            my_items_view.get_context_data()
            pass
        except Exception as e:
            pass
        
        # Warm user badges
        BadgeService.get_user_badges(user)
        pass
    
    @staticmethod
    def warm_search_cache(search_terms):
        """Warm up common search queries."""
        pass
        
        for term in search_terms:
            cache_key = get_ultimate_cache().generate_cache_key('items_list', q=term)
            
            def search_loader():
                search_items = list(
                    Item.objects.filter(
                        is_active=True
                    ).filter(
                        Q(title__icontains=term)
                        | Q(description__icontains=term)
                        | Q(author__icontains=term)
                    ).select_related("owner", "category")
                    .prefetch_related("images", "groups")
                    .order_by("-created_at")[:24]
                )
                return search_items
            
            get_ultimate_cache().get(cache_key, loader_func=search_loader, ttl=600, segment='warm')
            pass
    
    @staticmethod
    def get_cache_warming_stats():
        """Get statistics about cache warming process."""
        stats = get_ultimate_cache().get_stats()
        
        return {
            'cache_size': stats['l1_size'],
            'hit_rate': stats['metrics']['hit_rate'],
            'l2_available': stats['l2_available'],
            'total_requests': stats['metrics']['hits'] + stats['metrics']['misses'],
            'errors': stats['metrics']['errors']
        }


def warm_cache_on_startup():
    """Cache warming function to be called on application startup."""
    pass
    pass
    
    try:
        CacheWarmer.warm_common_cache_entries()
        
        # Get final stats
        stats = CacheWarmer.get_cache_warming_stats()
        
        pass
        pass
        pass
        pass
        pass
        pass
        
        pass
        pass
        
    except Exception as e:
        pass
        pass

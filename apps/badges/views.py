"""
Views for badges and leaderboards.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView, DetailView

from apps.badges.models import Badge, UserBadge
from apps.badges.services import BadgeService


class BadgeListView(ListView):
    """List all available badges."""
    
    model = Badge
    template_name = 'badges/badge_list.html'
    context_object_name = 'badges'
    
    def get_queryset(self):
        from apps.core.ultra_cache import get_ultimate_cache
        
        # Generate cache key for badge list
        cache_key = get_ultimate_cache().generate_cache_key('badge_list')
        
        def loader():
            return list(Badge.objects.filter(is_active=True).order_by('display_order', 'category', 'badge_type'))
        
        # Cache badge list for 1 hour (changes rarely)
        return get_ultimate_cache().get(cache_key, loader_func=loader, ttl=3600, segment='hot')


class UserBadgeListView(LoginRequiredMixin, ListView):
    """List badges earned by the current user."""
    
    model = UserBadge
    template_name = 'badges/user_badges.html'
    context_object_name = 'user_badges'
    
    def get_queryset(self):
        return BadgeService.get_user_badges(self.request.user)


class LeaderboardView(ListView):
    """Display leaderboards."""
    
    model = Badge
    template_name = 'badges/leaderboard.html'
    context_object_name = 'leaderboard_entries'
    
    def get_context_data(self, **kwargs):
        from apps.core.ultra_cache import get_ultimate_cache
        
        context = super().get_context_data(**kwargs)
        
        # Generate cache key for leaderboards context
        cache_key = get_ultimate_cache().generate_cache_key(
            'leaderboards_view', 
            self.request.user.id if self.request.user.is_authenticated else 'anonymous'
        )
        
        def loader():
            # Get different leaderboard types
            leaderboard_types = ['overall', 'lending', 'borrowing', 'reputation']
            leaderboards = {}
            
            for leaderboard_type in leaderboard_types:
                leaderboards[leaderboard_type] = BadgeService.get_leaderboard(
                    leaderboard_type, 
                    limit=20
                )
            
            context_data = {'leaderboards': leaderboards}
            
            # Get current user's ranks if logged in
            if self.request.user.is_authenticated:
                user_ranks = {}
                for leaderboard_type in leaderboard_types:
                    rank = BadgeService.get_user_rank(self.request.user, leaderboard_type)
                    user_ranks[leaderboard_type] = rank
                context_data['user_ranks'] = user_ranks
            
            return context_data
        
        # Cache leaderboard context for 5 minutes (leaderboards change frequently)
        cached_context = get_ultimate_cache().get(cache_key, loader_func=loader, ttl=300, segment='hot')
        
        context.update(cached_context)
        return context


def badge_detail(request, slug):
    """Show details for a specific badge."""
    from apps.core.ultra_cache import get_ultimate_cache
    
    # Generate cache key for badge detail
    cache_key = get_ultimate_cache().generate_cache_key(
        'badge_detail', 
        slug,
        request.user.id if request.user.is_authenticated else 'anonymous'
    )
    
    def loader():
        badge = Badge.objects.get(slug=slug, is_active=True)
        
        # Get users who have earned this badge
        user_badges = list(
            UserBadge.objects.filter(badge=badge)
            .select_related('user')
            .order_by('-earned_at')[:20]
        )
        
        # Check if current user has earned this badge
        has_earned = False
        if request.user.is_authenticated:
            has_earned = UserBadge.objects.filter(
                user=request.user, 
                badge=badge
            ).exists()
        
        # Get total count
        total_earned = UserBadge.objects.filter(badge=badge).count()
        
        return {
            'badge': badge,
            'user_badges': user_badges,
            'has_earned': has_earned,
            'total_earned': total_earned,
            'badge_id': badge.id,  # For cache invalidation
        }
    
    # Cache badge detail for 30 minutes (badge details change rarely)
    cached_context = get_ultimate_cache().get(cache_key, loader_func=loader, ttl=1800, segment='warm')
    
    return render(request, 'badges/badge_detail.html', cached_context)
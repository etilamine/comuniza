"""
Badge service for Comuniza gamification system.
Handles achievement tracking and badge awarding.
"""

from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils import timezone

from apps.badges.models import Badge, UserBadge, Achievement, ReputationPoints, Leaderboard
from apps.loans.models import Loan, LoanReview
from apps.groups.models import GroupMembership
from apps.core.ultra_cache import get_ultimate_cache

User = get_user_model()


class BadgeService:
    """Service for managing badges and achievements."""

    @staticmethod
    @transaction.atomic
    def check_and_award_badges(user, trigger_type, context_data=None):
        """
        Check if user qualifies for any badges based on trigger type.
        """
        if context_data is None:
            context_data = {}

        # Get all active achievements for this trigger type
        achievements = Achievement.objects.filter(
            trigger_type=trigger_type,
            is_active=True,
            badge__is_active=True,
        ).select_related('badge')

        for achievement in achievements:
            if BadgeService._check_achievement_criteria(user, achievement, context_data):
                BadgeService._award_badge(user, achievement.badge, context_data)

    @staticmethod
    def _check_achievement_criteria(user, achievement, context_data):
        """Check if user meets the criteria for an achievement."""
        
        if achievement.trigger_type == "item_shared":
            # Count user's shared items
            count = user.owned_items.filter(is_active=True).count()
            return count >= achievement.threshold_value

        elif achievement.trigger_type == "loan_completed":
            # Count user's completed loans
            count = Loan.objects.filter(
                borrower=user, 
                status="returned"
            ).count()
            return count >= achievement.threshold_value

        elif achievement.trigger_type == "group_joined":
            # Count user's group memberships
            count = GroupMembership.objects.filter(user=user).count()
            return count >= achievement.threshold_value

        elif achievement.trigger_type == "threshold_reached":
            # Check custom threshold conditions
            conditions = achievement.conditions or {}
            condition_type = conditions.get("type")
            
            if condition_type == "rating":
                # Check average rating
                reviews = LoanReview.objects.filter(reviewee=user)
                if reviews.count() >= conditions.get("min_reviews", 1):
                    avg_rating = reviews.aggregate(
                        models.Avg("rating")
                    )["rating__avg"] or 0
                    return avg_rating >= conditions.get("value", 0)
            
            elif condition_type == "trust_score":
                # Check trust score from reputation
                try:
                    reputation = user.reputation
                    min_reviews = conditions.get("min_reviews", 0)
                    if min_reviews > 0:
                        return (reputation.trust_score >= conditions.get("value", 0) and 
                                reputation.total_reviews >= min_reviews)
                    else:
                        return reputation.trust_score >= conditions.get("value", 0)
                except User.reputation.RelatedObjectDoesNotExist:
                    return False

        return False

    @staticmethod
    def _award_badge(user, badge, context_data):
        """Award a badge to a user."""
        
        # Check if user already has this badge
        if UserBadge.objects.filter(user=user, badge=badge).exists():
            return False

        # Create user badge entry
        user_badge = UserBadge.objects.create(
            user=user,
            badge=badge,
            context_data=context_data,
        )

        # Award reputation points
        BadgeService._add_reputation_points(
            user, 
            "achievement", 
            badge.points, 
            f"Earned {badge.name} badge",
            related_badge=user_badge
        )

        # Update leaderboards and invalidate caches
        BadgeService._update_and_invalidate_leaderboards(user)

        return True

    @staticmethod
    def _add_reputation_points(user, transaction_type, points, description, **kwargs):
        """Add reputation points to a user."""
        
        ReputationPoints.objects.create(
            user=user,
            transaction_type=transaction_type,
            points=points,
            description=description,
            **kwargs
        )

        # Update user's total reputation score
        try:
            reputation = user.reputation
            # Recalculate trust score based on new points
            reputation.calculate_ratings()
        except User.reputation.RelatedObjectDoesNotExist:
            # Create reputation if it doesn't exist
            from apps.loans.models import UserReputation
            UserReputation.objects.create(user=user)
        
        # Invalidate user scores cache since reputation changed
        user_scores_key = get_ultimate_cache().generate_cache_key('user_scores', user)
        get_ultimate_cache().delete(user_scores_key)

    @staticmethod
    def _update_leaderboards(user):
        """Update leaderboard rankings for a user."""
        
        # Calculate scores for different leaderboard types
        scores = BadgeService._calculate_leaderboard_scores(user)
        
        # Update or create leaderboard entries
        for leaderboard_type, score in scores.items():
            Leaderboard.objects.update_or_create(
                user=user,
                leaderboard_type=leaderboard_type,
                period_start=None,
                period_end=None,
                defaults={"score": score}
            )

        # Update ranks
        BadgeService._update_leaderboard_ranks()

    @staticmethod
    def _calculate_leaderboard_scores(user):
        """Calculate leaderboard scores for a user."""
        
        # Generate cache key for user scores
        cache_key = get_ultimate_cache().generate_cache_key('user_scores', user)
        
        def loader():
            scores = {}
            
            # Overall score (combination of all activities)
            total_points = ReputationPoints.objects.filter(
                user=user
            ).aggregate(models.Sum("points"))["points__sum"] or 0
            scores["overall"] = total_points

            # Lending score (points from lending activities)
            lending_points = ReputationPoints.objects.filter(
                user=user,
                transaction_type__in=["earned", "bonus", "achievement"]
            ).aggregate(models.Sum("points"))["points__sum"] or 0
            scores["lending"] = lending_points

            # Borrowing score (based on completed loans)
            borrowing_score = Loan.objects.filter(
                borrower=user, 
                status="returned"
            ).count() * 10
            scores["borrowing"] = borrowing_score

            # Reputation score (trust score)
            try:
                scores["reputation"] = user.reputation.trust_score
            except User.reputation.RelatedObjectDoesNotExist:
                scores["reputation"] = 50

            return scores
        
        return get_ultimate_cache().get(cache_key, loader_func=loader, ttl=1800, segment='warm')

    @staticmethod
    def _update_leaderboard_ranks():
        """Update rank positions for all leaderboards."""
        
        leaderboard_types = [choice[0] for choice in Leaderboard.LEADERBOARD_TYPES]
        
        for leaderboard_type in leaderboard_types:
            # Get entries ordered by score (descending)
            entries = Leaderboard.objects.filter(
                leaderboard_type=leaderboard_type,
                period_start__isnull=True,
                period_end__isnull=True,
            ).order_by("-score", "last_updated")
            
            # Update ranks
            for rank, entry in enumerate(entries, 1):
                entry.rank = rank
                entry.save(update_fields=["rank"])

    @staticmethod
    def process_loan_completion(loan):
        """Process badge checks when a loan is completed."""
        
        # Check borrower achievements
        BadgeService.check_and_award_badges(
            loan.borrower, 
            "loan_completed",
            {"loan_id": loan.id, "item_title": loan.item.title}
        )

        # Check lender achievements (if this is their first successful loan)
        completed_lending_loans = Loan.objects.filter(
            lender=loan.lender, 
            status="returned"
        ).count()
        
        if completed_lending_loans == 1:
            BadgeService.check_and_award_badges(
                loan.lender,
                "loan_completed",
                {"loan_id": loan.id, "as_lender": True}
            )

    @staticmethod
    def process_item_creation(item):
        """Process badge checks when an item is created."""
        
        BadgeService.check_and_award_badges(
            item.owner,
            "item_shared",
            {"item_id": item.id, "item_title": item.title}
        )

    @staticmethod
    def process_group_join(user, group):
        """Process badge checks when a user joins a group."""
        
        BadgeService.check_and_award_badges(
            user,
            "group_joined",
            {"group_id": group.id, "group_name": group.name}
        )

    @staticmethod
    def process_review(review):
        """Process badge checks when a review is given."""
        
        BadgeService.check_and_award_badges(
            review.reviewer,
            "review_given",
            {"review_id": review.id, "rating": review.rating}
        )

        # Check if reviewee qualifies for reputation badges
        BadgeService.check_and_award_badges(
            review.reviewee,
            "threshold_reached",
            {"review_received": True, "rating": review.rating}
        )

    @staticmethod
    def get_user_badges(user):
        """Get all badges earned by a user, ordered by earn date."""
        
        # Generate cache key
        cache_key = get_ultimate_cache().generate_cache_key('user_badges', user)
        
        def loader():
            return list(UserBadge.objects.filter(user=user).select_related('badge').order_by('-earned_at'))
        
        return get_ultimate_cache().get(cache_key, loader_func=loader, ttl=3600, segment='warm')

    @staticmethod
    def get_leaderboard(leaderboard_type="overall", limit=50):
        """Get top users for a specific leaderboard type."""
        
        # Generate cache key with type and limit
        cache_key = get_ultimate_cache().generate_cache_key('leaderboard', leaderboard_type=leaderboard_type, limit=limit)
        
        def loader():
            return list(Leaderboard.objects.filter(
                leaderboard_type=leaderboard_type,
                period_start__isnull=True,
                period_end__isnull=True,
            ).select_related('user').order_by('rank')[:limit])
        
        # Different TTL based on limit - smaller limits change more frequently
        ttl = 300 if limit <= 10 else 900  # 5 min for top 10, 15 min for others
        return get_ultimate_cache().get(cache_key, loader_func=loader, ttl=ttl, segment='hot')

    @staticmethod
    def get_user_rank(user, leaderboard_type="overall"):
        """Get a user's rank on a specific leaderboard."""
        
        try:
            entry = Leaderboard.objects.get(
                user=user,
                leaderboard_type=leaderboard_type,
                period_start__isnull=True,
                period_end__isnull=True,
            )
            return entry.rank
        except Leaderboard.DoesNotExist:
            return None

    @staticmethod
    def _invalidate_user_caches(user):
        """Invalidate cache entries for a specific user."""
        # Invalidate user badges cache
        user_badges_key = get_ultimate_cache().generate_cache_key('user_badges', user)
        get_ultimate_cache().delete(user_badges_key)
        
        # Invalidate user scores cache
        user_scores_key = get_ultimate_cache().generate_cache_key('user_scores', user)
        get_ultimate_cache().delete(user_scores_key)
        
        # Invalidate any leaderboard caches that might include this user
        BadgeService._invalidate_leaderboard_caches()

    @staticmethod
    def _invalidate_leaderboard_caches():
        """Invalidate all leaderboard-related caches."""
        # Invalidate all leaderboard caches using pattern matching
        get_ultimate_cache().invalidate_pattern('leaderboard:*')

    @staticmethod
    def _update_and_invalidate_leaderboards(user):
        """Update leaderboards and invalidate relevant caches."""
        BadgeService._update_leaderboards(user)
        BadgeService._invalidate_user_caches(user)
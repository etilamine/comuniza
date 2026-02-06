"""
Badges models for Comuniza gamification system.
Communist-themed badges and achievements for user engagement.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Badge(models.Model):
    """
    A badge that can be earned by users through various actions.
    Communist-themed badges for the P2P library system.
    """

    BADGE_TYPES = [
        ("bronze", _("Bronze")),
        ("silver", _("Silver")),
        ("gold", _("Gold")),
        ("platinum", _("Platinum")),
        ("special", _("Special")),
    ]

    BADGE_CATEGORIES = [
        ("lending", _("Lending")),
        ("borrowing", _("Borrowing")),
        ("community", _("Community")),
        ("reputation", _("Reputation")),
        ("special", _("Special")),
    ]

    # Basic Information
    name = models.CharField(_("name"), max_length=100)
    slug = models.SlugField(_("slug"), max_length=120, unique=True)
    description = models.TextField(_("description"))
    icon = models.CharField(
        _("icon"), max_length=50, help_text=_("Font Awesome icon class")
    )
    
    # Badge Properties
    badge_type = models.CharField(
        _("badge type"), max_length=10, choices=BADGE_TYPES, default="bronze"
    )
    category = models.CharField(
        _("category"), max_length=15, choices=BADGE_CATEGORIES, default="community"
    )
    points = models.PositiveIntegerField(
        _("points"), default=10, help_text=_("Reputation points awarded")
    )
    
    # Visibility
    is_active = models.BooleanField(_("active"), default=True)
    is_secret = models.BooleanField(
        _("secret badge"),
        default=False,
        help_text=_("Badge is hidden until earned"),
    )
    display_order = models.PositiveIntegerField(_("display order"), default=0)

    # Metadata
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        db_table = "badges"
        verbose_name = _("badge")
        verbose_name_plural = _("badges")
        ordering = ["display_order", "category", "badge_type", "name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["badge_type", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_badge_type_display()})"


class UserBadge(models.Model):
    """
    Junction table tracking which users have earned which badges.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="badges",
        verbose_name=_("user"),
    )
    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name="awarded_to",
        verbose_name=_("badge"),
    )
    
    # Earning Details
    earned_at = models.DateTimeField(_("earned at"), auto_now_add=True)
    progress = models.PositiveIntegerField(
        _("progress"),
        default=100,
        help_text=_("Progress percentage for multi-step badges"),
    )
    context_data = models.JSONField(
        _("context data"),
        default=dict,
        blank=True,
        help_text=_("Additional data about how the badge was earned"),
    )

    class Meta:
        db_table = "user_badges"
        verbose_name = _("user badge")
        verbose_name_plural = _("user badges")
        ordering = ["-earned_at"]
        unique_together = [["user", "badge"]]
        indexes = [
            models.Index(fields=["user", "earned_at"]),
            models.Index(fields=["badge", "earned_at"]),
        ]

    def __str__(self):
        return f"{self.user.email} earned {self.badge.name}"


class Achievement(models.Model):
    """
    Specific achievements that can unlock badges.
    Defines the criteria for earning badges.
    """

    TRIGGER_TYPES = [
        ("loan_completed", _("Loan Completed")),
        ("item_shared", _("Item Shared")),
        ("review_given", _("Review Given")),
        ("group_joined", _("Group Joined")),
        ("streak_maintained", _("Streak Maintained")),
        ("threshold_reached", _("Threshold Reached")),
        ("special_action", _("Special Action")),
    ]

    badge = models.ForeignKey(
        Badge,
        on_delete=models.CASCADE,
        related_name="achievements",
        verbose_name=_("badge"),
    )
    
    # Achievement Criteria
    trigger_type = models.CharField(
        _("trigger type"), max_length=20, choices=TRIGGER_TYPES
    )
    threshold_value = models.PositiveIntegerField(
        _("threshold value"),
        null=True,
        blank=True,
        help_text=_("Value needed to trigger this achievement"),
    )
    conditions = models.JSONField(
        _("conditions"),
        default=dict,
        blank=True,
        help_text=_("Additional conditions for earning this achievement"),
    )
    
    # State
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        db_table = "achievements"
        verbose_name = _("achievement")
        verbose_name_plural = _("achievements")
        ordering = ["badge", "trigger_type"]

    def __str__(self):
        return f"Achievement for {self.badge.name}"


class Leaderboard(models.Model):
    """
    Leaderboard entries for different ranking categories.
    """

    LEADERBOARD_TYPES = [
        ("overall", _("Overall")),
        ("lending", _("Lending")),
        ("borrowing", _("Borrowing")),
        ("reputation", _("Reputation")),
        ("streak", _("Streak")),
        ("monthly", _("Monthly")),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="leaderboard_entries",
        verbose_name=_("user"),
    )
    
    # Ranking Data
    leaderboard_type = models.CharField(
        _("leaderboard type"), max_length=15, choices=LEADERBOARD_TYPES
    )
    score = models.DecimalField(
        _("score"), max_digits=10, decimal_places=2, default=0.0
    )
    rank = models.PositiveIntegerField(_("rank"), default=0)
    
    # Time Period
    period_start = models.DateTimeField(_("period start"), null=True, blank=True)
    period_end = models.DateTimeField(_("period end"), null=True, blank=True)
    
    # Metadata
    last_updated = models.DateTimeField(_("last updated"), auto_now=True)

    class Meta:
        db_table = "leaderboards"
        verbose_name = _("leaderboard")
        verbose_name_plural = _("leaderboards")
        ordering = ["leaderboard_type", "-score"]
        unique_together = [["user", "leaderboard_type", "period_start", "period_end"]]
        indexes = [
            models.Index(fields=["leaderboard_type", "-score"]),
            models.Index(fields=["user", "leaderboard_type"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_leaderboard_type_display()} #{self.rank}"


class ReputationPoints(models.Model):
    """
    Point transactions for user reputation system.
    Tracks all point gains and losses.
    """

    TRANSACTION_TYPES = [
        ("earned", _("Points Earned")),
        ("bonus", _("Bonus Points")),
        ("penalty", _("Points Deducted")),
        ("streak_bonus", _("Streak Bonus")),
        ("achievement", _("Achievement")),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reputation_transactions",
        verbose_name=_("user"),
    )
    
    # Transaction Details
    transaction_type = models.CharField(
        _("transaction type"), max_length=15, choices=TRANSACTION_TYPES
    )
    points = models.IntegerField(_("points"))
    description = models.CharField(_("description"), max_length=200)
    
    # Context
    related_loan = models.ForeignKey(
        "loans.Loan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reputation_transactions",
        verbose_name=_("related loan"),
    )
    related_badge = models.ForeignKey(
        UserBadge,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reputation_transactions",
        verbose_name=_("related badge"),
    )
    
    # Metadata
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        db_table = "reputation_points"
        verbose_name = _("reputation points")
        verbose_name_plural = _("reputation points")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["transaction_type", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user.email}: {self.points} points ({self.transaction_type})"
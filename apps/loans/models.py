"""
Loans models for Comuniza.
Tracks borrowing/lending transactions and user reputation.
"""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save
from django.dispatch import receiver


class Loan(models.Model):
    """
    A loan transaction - someone borrowing an item from someone else.
    """

    STATUS_CHOICES = [
        ("requested", _("Requested")),
        ("approved", _("Approved")),
        ("rejected", _("Rejected")),
        ("active", _("Active")),
        ("borrower_returned", _("Borrower Returned")),
        ("returned", _("Returned")),
        ("overdue", _("Overdue")),
        ("cancelled", _("Cancelled")),
    ]

    # Relationships
    item = models.ForeignKey(
        "items.Item",
        on_delete=models.CASCADE,
        related_name="loans",
        verbose_name=_("item"),
    )
    borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrowed_loans",
        verbose_name=_("borrower"),
    )
    lender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lent_loans",
        verbose_name=_("lender"),
    )
    group = models.ForeignKey(
        "groups.Group",
        on_delete=models.SET_NULL,
        null=True,
        related_name="loans",
        verbose_name=_("group"),
        help_text=_("The group through which this loan was made"),
    )

    # Loan details
    status = models.CharField(
        _("status"), max_length=20, choices=STATUS_CHOICES, default="requested"
    )
    request_message = models.TextField(
        _("request message"), blank=True, help_text=_("Message from borrower to lender")
    )
    rejection_reason = models.TextField(_("rejection reason"), blank=True)

    # Dates
    requested_at = models.DateTimeField(_("requested at"), auto_now_add=True)
    approved_at = models.DateTimeField(_("approved at"), null=True, blank=True)
    start_date = models.DateField(_("start date"), null=True, blank=True)
    due_date = models.DateField(_("due date"), null=True, blank=True)
    returned_at = models.DateTimeField(_("returned at"), null=True, blank=True)

    # Deposit
    deposit_paid = models.BooleanField(_("deposit paid"), default=False)
    deposit_amount = models.DecimalField(
        _("deposit amount"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    deposit_returned = models.BooleanField(_("deposit returned"), default=False)

    # Extension requests
    extension_requested = models.BooleanField(_("extension requested"), default=False)
    extension_days = models.PositiveIntegerField(
        _("extension days"), null=True, blank=True
    )
    extension_approved = models.BooleanField(_("extension approved"), default=False)
    extension_reason = models.TextField(_("extension reason"), blank=True)

    # Condition tracking
    condition_at_pickup = models.CharField(
        _("condition at pickup"), max_length=100, blank=True
    )
    condition_at_return = models.CharField(
        _("condition at return"), max_length=100, blank=True
    )
    damage_reported = models.BooleanField(_("damage reported"), default=False)
    damage_description = models.TextField(_("damage description"), blank=True)

    # Privacy and visibility
    privacy = models.CharField(
        _("privacy"),
        max_length=15,
        choices=[
            ("participants", _("Participants only")),
            ("group_admins", _("Group admins can view")),
            ("group_public", _("Visible to group members")),
        ],
        default="participants",
        help_text=_("Who can view this loan"),
    )

    # Metadata
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    notes = models.TextField(_("notes"), blank=True, help_text=_("Internal notes"))

    class Meta:
        db_table = "loans"
        verbose_name = _("loan")
        verbose_name_plural = _("loans")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["borrower", "status"]),
            models.Index(fields=["lender", "status"]),
            models.Index(fields=["item", "status"]),
            models.Index(fields=["status", "due_date"]),
            models.Index(fields=["group", "status"]),
        ]

    def __str__(self):
        return f"{self.borrower.email} borrowing {self.item.title} from {self.lender.email}"

    def save(self, *args, **kwargs):
        # Track status change for badge awarding - capture old status BEFORE any modifications
        old_status = self.status if self.pk else None

        # Auto-set lender from item owner
        if not self.lender_id:
            self.lender = self.item.owner

        # When loan is approved, set dates if not set
        if self.status == "approved" and not self.start_date:
            self.start_date = timezone.now().date()
            self.due_date = self.start_date + timedelta(days=self.item.max_loan_days)
            self.approved_at = timezone.now()

        # Update item status based on loan status
        item_status_changed = False
        if self.status == "active":
            self.item.status = "borrowed"
            self.item.current_borrower = self.borrower
            item_status_changed = True
            self.item.save()
        elif self.status == "borrower_returned":
            # Item marked as returned by borrower, waiting for lender confirmation
            pass
        elif self.status == "returned":
            if not self.returned_at:
                self.returned_at = timezone.now()
            self.item.status = "available"
            self.item.current_borrower = None
            self.item.borrow_count += 1
            item_status_changed = True
            self.item.save()
        elif self.status in ["rejected", "cancelled"]:
            # If this was an approved loan being cancelled, make item available if no other active loans
            active_loans = self.item.loans.filter(status='active').exclude(pk=self.pk)
            if not active_loans.exists():
                self.item.status = "available"
                self.item.current_borrower = None
                item_status_changed = True
                self.item.save()

        # Auto-mark overdue loans
        if self.status in ['active', 'approved'] and self.is_overdue and self.status != 'overdue':
            old_status_for_overdue = self.status
            self.status = 'overdue'
            # Store the old status for notification logic
            if not hasattr(self, '_previous_status'):
                self._previous_status = old_status_for_overdue

        super().save(*args, **kwargs)

        # Invalidate item caches when item status changes
        if item_status_changed:
            from apps.core.ultra_cache import get_ultimate_cache
            cache = get_ultimate_cache()
            # Invalidate all item detail caches for this item
            cache.invalidate_pattern(f'item_detail:*:{self.item.id}:*')
            cache.invalidate_pattern(f'item_detail_v2:{self.item.id}:*')
            cache.invalidate_pattern(f'item_detail_v3:{self.item.id}:*')
            # Invalidate item list cache
            cache.invalidate_pattern('items_list:*')

        # Emit LoanCompleted event when loan is completed
        if old_status != "returned" and self.status == "returned":
            from apps.core.events import event_bus, LoanCompletedEvent
            event = LoanCompletedEvent(
                loan_id=self.pk,
                user_id=self.borrower_id,
                item_id=self.item_id,
                days_outstanding=(timezone.now().date() - self.start_date).days,
                condition_rating=getattr(self, 'condition_rating', 5) if hasattr(self, 'condition_rating') else 5
            )
            event_bus.publish(event)

    @property
    def is_overdue(self):
        """Check if loan is overdue."""
        if self.status in ["active", "approved"] and self.due_date:
            return timezone.now().date() > self.due_date
        return False

    @property
    def days_until_due(self):
        """Calculate days until due date."""
        if self.due_date:
            delta = self.due_date - timezone.now().date()
            return delta.days
        return None

    @property
    def days_overdue(self):
        """Calculate days overdue."""
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0

    def approve(self, start_date=None):
        """Approve the loan request."""
        self.status = "approved"
        self.approved_at = timezone.now()
        if start_date:
            self.start_date = start_date
        else:
            self.start_date = timezone.now().date()
        self.due_date = self.start_date + timedelta(days=self.item.max_loan_days)
        self.save()

    def reject(self, reason=""):
        """Reject the loan request."""
        self.status = "rejected"
        self.rejection_reason = reason
        self.save()

    def mark_as_active(self):
        """Mark loan as active (item has been picked up)."""
        self.status = "active"
        # Set start_date to current date if not already set (when item is actually picked up)
        if not self.start_date:
            self.start_date = timezone.now().date()
        self.save()

    def mark_as_returned(self, condition=""):
        """Mark loan as returned by borrower (awaiting lender confirmation)."""
        self.status = "borrower_returned"
        self.condition_at_return = condition
        self.save()

    def confirm_return(self):
        """Confirm return by lender."""
        self.status = "returned"
        self.returned_at = timezone.now()
        self.save()

    def request_extension(self, days, reason=""):
        """Request an extension for the loan."""
        self.extension_requested = True
        self.extension_days = days
        self.extension_reason = reason
        self.save()

    def approve_extension(self):
        """Approve extension request."""
        if self.extension_requested and self.extension_days:
            self.due_date = self.due_date + timedelta(days=self.extension_days)
            self.extension_approved = True
            self.extension_requested = False
            self.save()

    def can_view(self, user):
        """Check if user can view this loan based on privacy settings."""
        if self.borrower == user or self.lender == user:
            return True
        if self.privacy == "participants":
            return False
        elif self.privacy == "group_admins":
            return self.group and self.group.is_admin(user)
        elif self.privacy == "group_public":
            return self.group and self.group.is_member(user)
        return False


@receiver(pre_save, sender=Loan)
def track_loan_status_change(sender, instance, **kwargs):
    """Track the previous status for notification purposes."""
    if instance.pk:
        try:
            old_instance = Loan.objects.get(pk=instance.pk)
            instance._previous_status = old_instance.status
        except Loan.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


class LoanReview(models.Model):
    """
    Reviews and ratings for completed loans - impacts user reputation.
    Reviews can be written by both lender and borrower.
    """

    REVIEWER_ROLE_CHOICES = [
        ("lender", _("Lender")),
        ("borrower", _("Borrower")),
    ]

    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("loan"),
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="loan_reviews_written",
        verbose_name=_("reviewer"),
    )
    reviewee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="loan_reviews_received",
        verbose_name=_("reviewee"),
    )
    reviewer_role = models.CharField(
        _("reviewer role"),
        max_length=10,
        choices=REVIEWER_ROLE_CHOICES,
        help_text=_("Whether the reviewer was the lender or borrower"),
    )

    # Rating and feedback
    rating = models.PositiveSmallIntegerField(
        _("rating"),
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text=_("Rating from 1 to 5"),
    )
    comment = models.TextField(_("comment"), blank=True)

    # Specific ratings
    communication_rating = models.PositiveSmallIntegerField(
        _("communication"), choices=[(i, str(i)) for i in range(1, 6)], default=5
    )
    reliability_rating = models.PositiveSmallIntegerField(
        _("reliability"), choices=[(i, str(i)) for i in range(1, 6)], default=5
    )
    condition_rating = models.PositiveSmallIntegerField(
        _("item condition"),
        choices=[(i, str(i)) for i in range(1, 6)],
        default=5,
        help_text=_(
            "For lender: item returned condition. For borrower: item received condition"
        ),
    )

    # Flags
    would_lend_again = models.BooleanField(_("would lend/borrow again"), default=True)
    is_public = models.BooleanField(_("public review"), default=True)

    # Metadata
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        db_table = "loan_reviews"
        verbose_name = _("loan review")
        verbose_name_plural = _("loan reviews")
        ordering = ["-created_at"]
        unique_together = [["loan", "reviewer"]]
        indexes = [
            models.Index(fields=["reviewee", "is_public"]),
            models.Index(fields=["loan"]),
        ]

    def __str__(self):
        return f"Review by {self.reviewer.email} for {self.reviewee.email}"

    def save(self, *args, **kwargs):
        # Auto-set reviewee based on reviewer role
        if self.reviewer_role == "lender":
            self.reviewee = self.loan.borrower
        else:
            self.reviewee = self.loan.lender
        super().save(*args, **kwargs)


class UserReputation(models.Model):
    """
    Aggregated reputation score for users based on their loan history.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reputation",
        verbose_name=_("user"),
    )

    # Lending stats
    items_lent = models.PositiveIntegerField(_("items lent"), default=0)
    lending_rating = models.DecimalField(
        _("lending rating"),
        max_digits=3,
        decimal_places=2,
        default=0.0,
        help_text=_("Average rating as a lender (0-5)"),
    )

    # Borrowing stats
    items_borrowed = models.PositiveIntegerField(_("items borrowed"), default=0)
    borrowing_rating = models.DecimalField(
        _("borrowing rating"),
        max_digits=3,
        decimal_places=2,
        default=0.0,
        help_text=_("Average rating as a borrower (0-5)"),
    )

    # Overall stats
    overall_rating = models.DecimalField(
        _("overall rating"),
        max_digits=3,
        decimal_places=2,
        default=0.0,
        help_text=_("Combined average rating (0-5)"),
    )
    total_reviews = models.PositiveIntegerField(_("total reviews"), default=0)

    # Reliability metrics
    on_time_returns = models.PositiveIntegerField(_("on-time returns"), default=0)
    late_returns = models.PositiveIntegerField(_("late returns"), default=0)
    cancellations = models.PositiveIntegerField(_("cancellations"), default=0)

    # Trust score (0-100)
    trust_score = models.PositiveIntegerField(
        _("trust score"),
        default=50,
        help_text=_("Algorithmic trust score from 0-100"),
    )

    # Badges/achievements
    verified = models.BooleanField(_("verified user"), default=False)
    top_lender = models.BooleanField(_("top lender badge"), default=False)
    reliable_borrower = models.BooleanField(_("reliable borrower badge"), default=False)

    # Metadata
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        db_table = "user_reputations"
        verbose_name = _("user reputation")
        verbose_name_plural = _("user reputations")

    def __str__(self):
        return f"Reputation for {self.user.email}"

    def calculate_ratings(self):
        """Recalculate all ratings based on reviews."""
        # Get all reviews received by this user
        lender_reviews = LoanReview.objects.filter(
            reviewee=self.user, reviewer_role="borrower"
        )
        borrower_reviews = LoanReview.objects.filter(
            reviewee=self.user, reviewer_role="lender"
        )

        # Calculate lending rating
        if lender_reviews.exists():
            self.lending_rating = (
                lender_reviews.aggregate(models.Avg("rating"))["rating__avg"] or 0.0
            )

        # Calculate borrowing rating
        if borrower_reviews.exists():
            self.borrowing_rating = (
                borrower_reviews.aggregate(models.Avg("rating"))["rating__avg"] or 0.0
            )

        # Calculate overall rating
        all_reviews = lender_reviews | borrower_reviews
        if all_reviews.exists():
            self.overall_rating = (
                all_reviews.aggregate(models.Avg("rating"))["rating__avg"] or 0.0
            )
            self.total_reviews = all_reviews.count()

        # Update loan counts
        self.items_lent = Loan.objects.filter(
            lender=self.user, status="returned"
        ).count()
        self.items_borrowed = Loan.objects.filter(
            borrower=self.user, status="returned"
        ).count()

        # Calculate on-time vs late returns
        borrower_loans = Loan.objects.filter(borrower=self.user, status="returned")
        self.on_time_returns = borrower_loans.filter(
            returned_at__lte=models.F("due_date")
        ).count()
        self.late_returns = borrower_loans.filter(
            returned_at__gt=models.F("due_date")
        ).count()

        # Calculate trust score (simplified algorithm)
        trust = 50  # Start at 50
        if self.total_reviews > 0:
            trust += int(self.overall_rating * 10) - 25  # +/- based on ratings
        if self.on_time_returns > 0:
            trust += min(self.on_time_returns * 2, 20)  # Up to +20 for on-time
        if self.late_returns > 0:
            trust -= min(self.late_returns * 5, 30)  # Up to -30 for late returns

        self.trust_score = max(0, min(100, trust))  # Keep between 0-100

        # Award badges
        self.top_lender = self.items_lent >= 10 and self.lending_rating >= 4.5
        self.reliable_borrower = (
            self.items_borrowed >= 5
            and self.borrowing_rating >= 4.5
            and self.late_returns == 0
        )

        self.save()


class UserLoanSettings(models.Model):
    """
    Global and group-specific loan term settings for users.
    Allows users to set their preferred loan terms globally or per group.
    """

    # Global settings (applied to all groups unless overridden)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="loan_settings",
        verbose_name=_("user"),
    )

    # Default loan terms
    default_loan_days = models.PositiveIntegerField(
        _("default loan days"),
        default=14,
        help_text=_("Default number of days for loans")
    )
    allow_extensions = models.BooleanField(
        _("allow extensions"),
        default=True,
        help_text=_("Whether borrower can request extensions")
    )
    require_approval_for_extensions = models.BooleanField(
        _("require approval for extensions"),
        default=True,
        help_text=_("Whether extensions require approval or are automatic")
    )
    max_extension_days = models.PositiveIntegerField(
        _("maximum extension days"),
        default=7,
        help_text=_("Maximum days that can be requested for extension")
    )

    # Privacy settings
    default_loan_privacy = models.CharField(
        _("default loan privacy"),
        max_length=15,
        choices=[
            ("participants", _("Participants only")),
            ("group_admins", _("Group admins can view")),
            ("group_public", _("Visible to group members")),
        ],
        default="participants",
        help_text=_("Default visibility for new loans")
    )

    # Notification preferences
    email_notifications = models.BooleanField(
        _("email notifications"),
        default=True,
        help_text=_("Receive email notifications for loan activities")
    )
    message_notifications = models.BooleanField(
        _("message notifications"),
        default=True,
        help_text=_("Receive in-app message notifications")
    )

    # Metadata
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        db_table = "user_loan_settings"
        verbose_name = _("user loan settings")
        verbose_name_plural = _("user loan settings")

    def __str__(self):
        return f"Loan settings for {self.user.email}"


class GroupLoanSettings(models.Model):
    """
    Group-specific loan term overrides for users.
    Allows users to have different loan terms for different groups.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_loan_settings",
        verbose_name=_("user"),
    )
    group = models.ForeignKey(
        "groups.Group",
        on_delete=models.CASCADE,
        related_name="user_loan_settings",
        verbose_name=_("group"),
    )

    # Group-specific loan terms (override global settings)
    loan_days = models.PositiveIntegerField(
        _("loan days"),
        null=True,
        blank=True,
        help_text=_("Number of days for loans in this group (null = use global setting)")
    )
    allow_extensions = models.BooleanField(
        _("allow extensions"),
        null=True,
        blank=True,
        help_text=_("Allow extensions in this group (null = use global setting)")
    )
    require_approval_for_extensions = models.BooleanField(
        _("require approval for extensions"),
        null=True,
        blank=True,
        help_text=_("Extensions require approval in this group (null = use global setting)")
    )
    max_extension_days = models.PositiveIntegerField(
        _("maximum extension days"),
        null=True,
        blank=True,
        help_text=_("Maximum extension days in this group (null = use global setting)")
    )

    # Group-specific privacy
    loan_privacy = models.CharField(
        _("loan privacy"),
        max_length=15,
        choices=[
            ("participants", _("Participants only")),
            ("group_admins", _("Group admins can view")),
            ("group_public", _("Visible to group members")),
        ],
        blank=True,
        help_text=_("Visibility for loans in this group (blank = use global setting)")
    )

    # Metadata
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        db_table = "group_loan_settings"
        verbose_name = _("group loan settings")
        verbose_name_plural = _("group loan settings")
        unique_together = [["user", "group"]]
        indexes = [
            models.Index(fields=["user", "group"]),
        ]

    def __str__(self):
        return f"{self.user.email} settings for {self.group.name}"

    def get_effective_loan_days(self):
        """Get effective loan days, falling back to global settings."""
        if self.loan_days is not None:
            return self.loan_days
        return self.user.loan_settings.default_loan_days

    def get_effective_allow_extensions(self):
        """Get effective extensions setting, falling back to global settings."""
        if self.allow_extensions is not None:
            return self.allow_extensions
        return self.user.loan_settings.allow_extensions

    def get_effective_require_approval(self):
        """Get effective approval requirement, falling back to global settings."""
        if self.require_approval_for_extensions is not None:
            return self.require_approval_for_extensions
        return self.user.loan_settings.require_approval_for_extensions

    def get_effective_max_extension_days(self):
        """Get effective max extension days, falling back to global settings."""
        if self.max_extension_days is not None:
            return self.max_extension_days
        return self.user.loan_settings.max_extension_days

    def get_effective_privacy(self):
        """Get effective privacy setting, falling back to global settings."""
        if self.loan_privacy:
            return self.loan_privacy
        return self.user.loan_settings.default_loan_privacy

"""
Admin configuration for Loans app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Loan, LoanReview, UserReputation


class LoanReviewInline(admin.TabularInline):
    """Inline admin for loan reviews."""

    model = LoanReview
    extra = 0
    fk_name = "loan"
    fields = [
        "reviewer",
        "reviewee",
        "reviewer_role",
        "rating",
        "comment",
        "created_at",
    ]
    readonly_fields = ["created_at", "reviewee"]
    autocomplete_fields = ["reviewer"]


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """Admin configuration for Loan model."""

    list_display = [
        "item",
        "borrower",
        "lender",
        "status",
        "start_date",
        "due_date",
        "is_overdue",
        "requested_at",
    ]
    list_filter = [
        "status",
        "deposit_paid",
        "deposit_returned",
        "damage_reported",
        "requested_at",
        "start_date",
        "due_date",
    ]
    search_fields = [
        "item__title",
        "borrower__email",
        "lender__email",
        "group__name",
        "request_message",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
        "requested_at",
        "approved_at",
        "returned_at",
        "is_overdue",
        "days_until_due",
        "days_overdue",
        "lender",
    ]
    autocomplete_fields = ["item", "borrower", "group"]
    inlines = [LoanReviewInline]
    date_hierarchy = "requested_at"

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "item",
                    "borrower",
                    "lender",
                    "group",
                    "status",
                )
            },
        ),
        (
            _("Request Details"),
            {
                "fields": (
                    "request_message",
                    "rejection_reason",
                )
            },
        ),
        (
            _("Dates"),
            {
                "fields": (
                    "requested_at",
                    "approved_at",
                    "start_date",
                    "due_date",
                    "returned_at",
                    "is_overdue",
                    "days_until_due",
                    "days_overdue",
                )
            },
        ),
        (
            _("Deposit"),
            {
                "fields": (
                    "deposit_paid",
                    "deposit_amount",
                    "deposit_returned",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Extension"),
            {
                "fields": (
                    "extension_requested",
                    "extension_days",
                    "extension_reason",
                    "extension_approved",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Condition & Damage"),
            {
                "fields": (
                    "condition_at_pickup",
                    "condition_at_return",
                    "damage_reported",
                    "damage_description",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("notes", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["mark_as_approved", "mark_as_active", "mark_as_returned"]

    def mark_as_approved(self, request, queryset):
        """Bulk action to approve selected loans."""
        count = 0
        affected_users = set()
        for loan in queryset.filter(status="requested"):
            loan.approve()
            count += 1
            affected_users.add(loan.borrower.id)
            affected_users.add(loan.lender.id)

        for user_id in affected_users:
            from apps.core.ultra_cache import get_ultimate_cache
            get_ultimate_cache().invalidate_pattern(f'my_loans_context:{user_id}:*')

        self.message_user(request, f"{count} loan(s) approved.")

    mark_as_approved.short_description = _("Approve selected loans")

    def mark_as_active(self, request, queryset):
        """Bulk action to mark selected loans as active."""
        count = 0
        affected_users = set()
        for loan in queryset.filter(status="approved"):
            loan.mark_as_active()
            count += 1
            affected_users.add(loan.borrower.id)
            affected_users.add(loan.lender.id)

        for user_id in affected_users:
            from apps.core.ultra_cache import get_ultimate_cache
            get_ultimate_cache().invalidate_pattern(f'my_loans_context:{user_id}:*')

        self.message_user(request, f"{count} loan(s) marked as active.")

    mark_as_active.short_description = _("Mark selected loans as active")

    def mark_as_returned(self, request, queryset):
        """Bulk action to mark selected loans as returned."""
        count = 0
        affected_users = set()
        for loan in queryset.filter(status="active"):
            loan.mark_as_returned()
            count += 1
            affected_users.add(loan.borrower.id)
            affected_users.add(loan.lender.id)

        for user_id in affected_users:
            from apps.core.ultra_cache import get_ultimate_cache
            get_ultimate_cache().invalidate_pattern(f'my_loans_context:{user_id}:*')

        self.message_user(request, f"{count} loan(s) marked as returned.")

    mark_as_returned.short_description = _("Mark selected loans as returned")


@admin.register(LoanReview)
class LoanReviewAdmin(admin.ModelAdmin):
    """Admin configuration for LoanReview model."""

    list_display = [
        "loan",
        "reviewer",
        "reviewee",
        "reviewer_role",
        "rating",
        "would_lend_again",
        "is_public",
        "created_at",
    ]
    list_filter = [
        "reviewer_role",
        "rating",
        "would_lend_again",
        "is_public",
        "created_at",
    ]
    search_fields = [
        "loan__item__title",
        "reviewer__email",
        "reviewee__email",
        "comment",
    ]
    readonly_fields = ["created_at", "updated_at", "reviewee"]
    autocomplete_fields = ["loan", "reviewer"]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "loan",
                    "reviewer",
                    "reviewee",
                    "reviewer_role",
                )
            },
        ),
        (
            _("Rating"),
            {
                "fields": (
                    "rating",
                    "communication_rating",
                    "reliability_rating",
                    "condition_rating",
                )
            },
        ),
        (
            _("Feedback"),
            {
                "fields": (
                    "comment",
                    "would_lend_again",
                    "is_public",
                )
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(UserReputation)
class UserReputationAdmin(admin.ModelAdmin):
    """Admin configuration for UserReputation model."""

    list_display = [
        "user",
        "overall_rating",
        "lending_rating",
        "borrowing_rating",
        "trust_score",
        "items_lent",
        "items_borrowed",
        "top_lender",
        "reliable_borrower",
    ]
    list_filter = [
        "verified",
        "top_lender",
        "reliable_borrower",
        "updated_at",
    ]
    search_fields = ["user__email"]
    readonly_fields = [
        "items_lent",
        "lending_rating",
        "items_borrowed",
        "borrowing_rating",
        "overall_rating",
        "total_reviews",
        "on_time_returns",
        "late_returns",
        "cancellations",
        "trust_score",
        "updated_at",
    ]
    autocomplete_fields = ["user"]

    fieldsets = (
        (
            None,
            {"fields": ("user",)},
        ),
        (
            _("Lending Stats"),
            {
                "fields": (
                    "items_lent",
                    "lending_rating",
                )
            },
        ),
        (
            _("Borrowing Stats"),
            {
                "fields": (
                    "items_borrowed",
                    "borrowing_rating",
                )
            },
        ),
        (
            _("Overall Stats"),
            {
                "fields": (
                    "overall_rating",
                    "total_reviews",
                    "trust_score",
                )
            },
        ),
        (
            _("Reliability Metrics"),
            {
                "fields": (
                    "on_time_returns",
                    "late_returns",
                    "cancellations",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Badges & Achievements"),
            {
                "fields": (
                    "verified",
                    "top_lender",
                    "reliable_borrower",
                )
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("updated_at",),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["recalculate_ratings"]

    def recalculate_ratings(self, request, queryset):
        """Bulk action to recalculate ratings for selected users."""
        count = 0
        for reputation in queryset:
            reputation.calculate_ratings()
            count += 1
        self.message_user(request, f"{count} reputation(s) recalculated.")

    recalculate_ratings.short_description = _("Recalculate ratings for selected users")

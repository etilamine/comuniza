"""
Admin configuration for Groups app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Group, GroupInvitation, GroupMembership


class GroupMembershipInline(admin.TabularInline):
    """Inline admin for group memberships."""

    model = GroupMembership
    extra = 0
    fields = ["user", "role", "status", "joined_at", "invited_by"]
    readonly_fields = ["joined_at"]
    autocomplete_fields = ["user", "invited_by"]


class GroupInvitationInline(admin.TabularInline):
    """Inline admin for group invitations."""

    model = GroupInvitation
    extra = 0
    fields = ["email", "invited_by", "status", "created_at", "expires_at"]
    readonly_fields = ["created_at", "token"]


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Admin configuration for Group model."""

    list_display = [
        "name",
        "owner",
        "privacy",
        "member_count",
        "item_count",
        "is_active",
        "created_at",
    ]
    list_filter = ["privacy", "is_active", "created_at"]
    search_fields = ["name", "description", "owner__email"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at", "member_count", "item_count"]
    autocomplete_fields = ["owner"]
    
    inlines = [GroupMembershipInline, GroupInvitationInline]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "description",
                    "image",
                    "owner",
                )
            },
        ),
        (
            _("Privacy & Settings"),
            {
                "fields": (
                    "privacy",
                    "allow_member_invites",
                    "require_approval_for_items",
                )
            },
        ),
        (
            _("Status"),
            {"fields": ("is_active",)},
        ),
        (
            _("Statistics"),
            {
                "fields": ("member_count", "item_count"),
                "classes": ("collapse",),
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


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    """Admin configuration for GroupMembership model."""

    list_display = ["user", "group", "role", "status", "joined_at"]
    list_filter = ["role", "status", "joined_at"]
    search_fields = ["user__email", "group__name"]
    readonly_fields = ["joined_at"]
    autocomplete_fields = ["group", "user", "invited_by"]

    fieldsets = (
        (
            None,
            {"fields": ("group", "user", "role", "status")},
        ),
        (
            _("Invitation Details"),
            {
                "fields": ("invited_by", "joined_at"),
            },
        ),
    )


@admin.register(GroupInvitation)
class GroupInvitationAdmin(admin.ModelAdmin):
    """Admin configuration for GroupInvitation model."""

    list_display = [
        "email",
        "group",
        "invited_by",
        "status",
        "created_at",
        "expires_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["email", "group__name", "invited_by__email"]
    readonly_fields = ["created_at", "token", "responded_at"]
    autocomplete_fields = ["group", "invited_by"]

    fieldsets = (
        (
            None,
            {"fields": ("group", "email", "invited_by", "message")},
        ),
        (
            _("Status"),
            {
                "fields": ("status", "token"),
            },
        ),
        (
            _("Dates"),
            {
                "fields": ("created_at", "expires_at", "responded_at"),
            },
        ),
    )

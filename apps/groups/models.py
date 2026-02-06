"""
Groups models for Comuniza.
Allows users to create private communities for sharing items.
"""

from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from apps.core.validators import (
    sanitized_text, coordinate_validator, no_profanity,
    validate_group_image
)
from easy_thumbnails.fields import ThumbnailerImageField


class Group(models.Model):
    """
    A group/community where members can share and borrow items.
    """

    PRIVACY_CHOICES = [
        ("private", _("Private - Invite only")),
        ("public", _("Public - Anyone can join")),
        ("request", _("Join by request")),
    ]

    name = models.CharField(
        _("name"),
        max_length=100,
        validators=[sanitized_text, no_profanity]
    )
    slug = models.SlugField(_("slug"), max_length=120, unique=True)
    description = models.TextField(
        _("description"),
        blank=True,
        validators=[sanitized_text]
    )
    privacy = models.CharField(
        _("privacy"), max_length=10, choices=PRIVACY_CHOICES, default="private"
    )
    image = ThumbnailerImageField(
        _("group image"),
        upload_to="groups/",
        blank=True,
        null=True,
        resize_source=dict(size=(2000, 2000), quality=90),

        validators=[validate_group_image]
    )

    # Location (required for map display)
    city = models.CharField(
        _("city"),
        max_length=100,
        default="Unknown",
        validators=[sanitized_text],
        help_text=_("City where the group is located"),
    )
    state = models.CharField(
        _("state/region"),
        max_length=100,
        blank=True,
        validators=[sanitized_text],
        help_text=_("State, province, or region"),
    )
    country = models.CharField(
        _("country"),
        max_length=100,
        default="Germany",
        validators=[sanitized_text]
    )
    latitude = models.DecimalField(
        _("latitude"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[coordinate_validator],
        help_text=_("Latitude coordinate (auto-filled if possible)"),
    )
    longitude = models.DecimalField(
        _("longitude"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[coordinate_validator],
        help_text=_("Longitude coordinate (auto-filled if possible)"),
    )

    # Relationships
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_groups",
        verbose_name=_("owner"),
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="GroupMembership",
        through_fields=("group", "user"),
        related_name="comuniza_groups",
        verbose_name=_("members"),
    )

    # Settings
    allow_member_invites = models.BooleanField(
        _("allow members to invite others"), default=True
    )
    require_approval_for_items = models.BooleanField(
        _("require approval for new items"), default=False
    )
    loan_visibility = models.CharField(
        _("loan visibility"),
        max_length=15,
        choices=[
            ("hidden", _("Hidden from members")),
            ("admin_only", _("Admins only")),
            ("public", _("Public to members")),
        ],
        default="public",
        help_text=_("Who can see loans made within this group")
    )

    # Metadata
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        db_table = "groups"
        verbose_name = _("group")
        verbose_name_plural = _("groups")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["privacy", "is_active"]),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        from django.db import connection

        update_fields = kwargs.get('update_fields')



        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("groups:detail", kwargs={"slug": self.slug})

    def is_member(self, user):
        """Check if user is a member of this group."""
        return self.members.filter(pk=user.pk).exists()

    def is_admin(self, user):
        """Check if user is an admin of this group."""
        if user == self.owner:
            return True
        return self.memberships.filter(user=user, role="admin").exists()

    def can_manage_items(self, user):
        """Check if user can manage items in this group."""
        return self.is_admin(user) or (
            self.is_member(user) and not self.require_approval_for_items
        )

    @property
    def member_count(self):
        """Return the number of members in the group."""
        return self.members.count()

    @property
    def item_count(self):
        """Return the number of items shared in the group."""
        return self.items.filter(is_active=True).count()


class GroupMembership(models.Model):
    """
    Through model for Group members with additional fields.
    """

    ROLE_CHOICES = [
        ("member", _("Member")),
        ("admin", _("Admin")),
    ]

    STATUS_CHOICES = [
        ("active", _("Active")),
        ("pending", _("Pending")),
        ("banned", _("Banned")),
    ]

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name=_("group"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="group_memberships",
        verbose_name=_("user"),
    )
    role = models.CharField(
        _("role"), max_length=10, choices=ROLE_CHOICES, default="member"
    )
    status = models.CharField(
        _("status"), max_length=10, choices=STATUS_CHOICES, default="active"
    )

    # Metadata
    joined_at = models.DateTimeField(_("joined at"), auto_now_add=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="group_invitations_sent",
        verbose_name=_("invited by"),
    )

    class Meta:
        db_table = "group_memberships"
        verbose_name = _("group membership")
        verbose_name_plural = _("group memberships")
        unique_together = [["group", "user"]]
        ordering = ["-joined_at"]
        indexes = [
            models.Index(fields=["group", "status"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.user.email} in {self.group.name}"


class GroupInvitation(models.Model):
    """
    Model for pending group invitations.
    """

    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("accepted", _("Accepted")),
        ("declined", _("Declined")),
        ("expired", _("Expired")),
    ]

    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="invitations",
        verbose_name=_("group"),
    )
    email = models.EmailField(_("email address"))
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_invitations",
        verbose_name=_("invited by"),
    )
    status = models.CharField(
        _("status"), max_length=10, choices=STATUS_CHOICES, default="pending"
    )
    token = models.CharField(_("token"), max_length=100, unique=True)
    message = models.TextField(_("message"), blank=True)

    # Metadata
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    expires_at = models.DateTimeField(_("expires at"))
    responded_at = models.DateTimeField(_("responded at"), null=True, blank=True)

    class Meta:
        db_table = "group_invitations"
        verbose_name = _("group invitation")
        verbose_name_plural = _("group invitations")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email", "status"]),
            models.Index(fields=["token"]),
        ]

    def __str__(self):
        return f"Invitation to {self.email} for {self.group.name}"

    def is_expired(self):
        """Check if the invitation has expired."""
        from django.utils import timezone

        return timezone.now() > self.expires_at

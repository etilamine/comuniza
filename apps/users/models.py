from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from .utils.privacy import hash_email, hash_phone
from .utils.username_generator import UsernameGenerator
from apps.core.validators import (
    sanitized_text, phone_validator, username_validator, no_profanity,
    validate_avatar_image
)
from easy_thumbnails.fields import ThumbnailerImageField

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    # Remove username from AbstractUser and add our own privacy-focused username
    username = models.CharField(
        _('username'),
        max_length=50,
        unique=True,
        validators=[username_validator],
        help_text=_('Public identifier (Reddit-style generated)'),
        blank=True  # Will be auto-generated during signup
    )

    # Authentication email (never displayed publicly)
    email = models.EmailField(_('email address'), unique=True)

    # Hashed versions for privacy (stored alongside plain for verification)
    email_hash = models.CharField(
        _('email hash'),
        max_length=200,
        blank=True,
        help_text=_('HMAC-SHA256 hash of email for GDPR privacy protection')
    )
    phone_hash = models.CharField(
        _('phone hash'),
        max_length=200,
        blank=True,
        help_text=_('HMAC-SHA256 hash of phone for privacy')
    )

    # Timestamps for audit trail
    created_at = models.DateTimeField(_('created at'), auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True, null=True, blank=True)

    # Optional contact info (plain text for user convenience)
    phone = models.CharField(
        _('phone number'),
        max_length=20,
        blank=True,
        validators=[phone_validator]
    )
    avatar = ThumbnailerImageField(
    upload_to='avatars/',
    blank=True,
    null=True,
    resize_source=dict(size=(500, 500), quality=90),
    validators=[validate_avatar_image]
)

    def save(self, *args, **kwargs):
        from django.db import connection

        update_fields = kwargs.get('update_fields')

        # Auto-generate email hash if not present (GDPR compliance)
        if self.email and not self.email_hash:
            self.email_hash = hash_email(self.email)

        # Auto-generate phone hash if phone is provided and hash not present
        if self.phone and not self.phone_hash:
            self.phone_hash = hash_phone(self.phone)



        super().save(*args, **kwargs)

    # Privacy controls
    profile_visibility = models.CharField(
        _('profile visibility'),
        max_length=20,
        choices=[
            ('private', _('Private - Only group members')),
            ('public', _('Public - Anyone can view')),
            ('lenders_borrowers', _('Lenders/Borrowers - Only users you\'ve transacted with')),
        ],
        default='private',
        help_text=_('Who can see your profile information')
    )

    groups_visibility = models.CharField(
        _('groups visibility'),
        max_length=20,
        choices=[
            ('private', _('Private - Only group members')),
            ('public', _('Public - Anyone can view')),
            ('lenders_borrowers', _('Lenders/Borrowers - Only users you\'ve transacted with in that group')),
        ],
        default='private',
        help_text=_('Who can see your groups')
    )

    location_visibility = models.CharField(
        _('location visibility'),
        max_length=20,
        choices=[
            ('private', _('Private - Only group members')),
            ('public', _('Public - Anyone can view')),
            ('lenders_borrowers', _('Lenders/Borrowers - Only users you\'ve transacted with')),
        ],
        default='private',
        help_text=_('Who can see your location')
    )

    email_visibility = models.CharField(
        _('email visibility'),
        max_length=20,
        choices=[
            ('private', _('Private - Never shown')),
            ('members', _('Group members only')),
            ('public', _('Public - Everyone')),
        ],
        default='private',
        help_text=_('Who can see your email address')
    )

    activity_visibility = models.CharField(
        _('activity visibility'),
        max_length=20,
        choices=[
            ('private', _('Private - No activity shown')),
            ('limited', _('Limited - Basic stats only')),
            ('public', _('Public - Full activity')),
        ],
        default='private',
        help_text=_('How much of your sharing activity is visible')
    )

    # Default item visibility
    default_item_visibility = models.CharField(
        _('default item visibility'),
        max_length=10,
        choices=[
            ('public', _('Public')),
            ('private', _('Private')),
            ('restricted', _('Restricted')),
        ],
        default='public',
        help_text=_('Default visibility for new items')
    )

    # Security settings
    last_password_change = models.DateTimeField(_('last password change'), null=True, blank=True)
    password_reset_required = models.BooleanField(_('password reset required'), default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    @property
    def loan_settings(self):
        """
        Get user's loan settings.
        Creates default settings if they don't exist.
        Handles DoesNotExist gracefully.
        """
        try:
            from apps.loans.models import UserLoanSettings
            return self.loan_settings
        except UserLoanSettings.DoesNotExist:
            # Create default settings if they don't exist
            from apps.loans.models import UserLoanSettings
            settings = UserLoanSettings.objects.get_or_create(user=self)
            return settings
        except Exception:
            # Fallback: try to create settings if they don't exist
            try:
                from apps.loans.models import UserLoanSettings
                settings = UserLoanSettings.objects.get_or_create(user=self)
                return settings
            except:
                # Last resort: return None but don't crash
                return None

    def __str__(self):
        return self.username or self.email

    def get_display_name(self):
        """Get the name to display publicly."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username

    def can_view_email(self, viewer):
        """Check if a user can view this user's email."""
        if viewer == self:
            return True  # Users can always see their own email

        if self.email_visibility == 'public':
            return True
        elif self.email_visibility == 'members':
            # Check if they share any groups
            return self.groups.filter(members=viewer).exists()
        else:  # private
            return False

    def can_view_profile(self, viewer):
        """Check if a user can view this user's profile."""
        if viewer == self:
            return True  # Users can always see their own profile

        if self.profile_visibility == 'public':
            return True
        elif self.profile_visibility == 'private':
            # Check if they share any groups
            return self.groups.filter(members=viewer).exists()
        elif self.profile_visibility == 'lenders_borrowers':
            # Check if they have transacted (loans) with this user
            from apps.loans.models import Loan
            return Loan.objects.filter(
                Q(borrower=self, lender=viewer) |
                Q(borrower=viewer, lender=self)
            ).exists()
        else:
            return False

    def can_view_groups(self, viewer):
        """Check if a user can view this user's groups."""
        if viewer == self:
            return True  # Users can always see their own groups

        if self.groups_visibility == 'public':
            return True
        elif self.groups_visibility == 'private':
            # Check if they share any groups
            return self.groups.filter(members=viewer).exists()
        elif self.groups_visibility == 'lenders_borrowers':
            # Check if they have transacted in specific groups
            from apps.loans.models import Loan
            # For each group, check if viewer has loans with this user in that group
            for group in self.groups.all():
                if Loan.objects.filter(
                    Q(borrower=self, lender=viewer, group=group) |
                    Q(borrower=viewer, lender=self, group=group)
                ).exists():
                    return True
            return False
        else:
            return False

    def can_view_location(self, viewer):
        """Check if a user can view this user's location."""
        if viewer == self:
            return True  # Users can always see their own location

        if self.location_visibility == 'public':
            return True
        elif self.location_visibility == 'private':
            # Check if they share any groups
            return self.groups.filter(members=viewer).exists()
        elif self.location_visibility == 'lenders_borrowers':
            # Check if they have transacted with this user
            from apps.loans.models import Loan
            return Loan.objects.filter(
                Q(borrower=self, lender=viewer) |
                Q(borrower=viewer, lender=self)
            ).exists()
        else:
            return False

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email_hash']),
            models.Index(fields=['username']),
            models.Index(fields=['-created_at']),
        ]

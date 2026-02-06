"""
Custom authentication backend for GDPR-compliant email authentication.
Supports both plain email and hashed email lookups for backward compatibility.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .utils.privacy import hash_email, verify_email_hash

User = get_user_model()


class EmailAuthenticationBackend(ModelBackend):
    """
    Custom authentication backend that:
    - Authenticates users by email instead of username
    - Supports both plain and hashed email verification
    - Provides GDPR-compliant authentication
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user by email and password.
        Supports both plain and hashed email lookups.
        """
        if username is None or password is None:
            return None

        try:
            # First, try to find user by email (exact match, case-insensitive)
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            # If not found by plain email, try to verify against hashed emails
            # This is for backward compatibility during transition
            try:
                # Get all users with email hashes and verify
                all_users = User.objects.filter(email_hash__isnull=False).exclude(email_hash='')
                for potential_user in all_users:
                    if verify_email_hash(username, potential_user.email_hash):
                        user = potential_user
                        break
                else:
                    # No user found with matching hash
                    return None
            except Exception:
                return None

        # Check password
        if user is not None and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id):
        """
        Get user by ID.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
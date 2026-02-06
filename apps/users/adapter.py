"""
Custom Allauth adapter for Comuniza.
Handles email verification flow, template context, and GDPR-compliant email hashing.
"""

import logging
from django.conf import settings
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from .utils.privacy import hash_email
from .models import User

logger = logging.getLogger(__name__)


class ComunizaSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter that generates usernames for OAuth users.
    """
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save user from social login and generate a username.
        """
        # Call parent to create the user
        user = super().save_user(request, sociallogin, form)
        
        # Generate username if not present
        if not user.username:
            from .utils.username_generator import UsernameGenerator
            existing_usernames = list(User.objects.values_list('username', flat=True))
            user.username = UsernameGenerator.generate_username(existing_usernames)
            user.save(update_fields=['username'])
            
            logger.info(f"Generated username '{user.username}' for social user {user.email}")
        
        # Auto-generate email hash if not present (GDPR compliance)
        if user.email and not user.email_hash:
            user.email_hash = hash_email(user.email)
            user.save(update_fields=['email_hash'])
        
        # Store email in session for verification_sent template
        if sociallogin:
            email = sociallogin.email_addresses[0].email if sociallogin.email_addresses else None
            if email:
                request.session['signup_email'] = email
        
        return user


class ComunizaAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter that:
    - Passes email to verification_sent template
    - Automatically hashes emails for GDPR compliance
    - Supports email-based authentication
    """

    def save_user(self, request, user, form=None):
        """
        Save user and store email in session for verification template.
        Automatically generates email hash for GDPR compliance.
        """
        user = super().save_user(request, user, form)
        
        # Auto-generate email hash if not present (GDPR compliance)
        if user.email and not user.email_hash:
            user.email_hash = hash_email(user.email)
            user.save(update_fields=['email_hash'])
        
        # Store email in session for verification_sent template
        if hasattr(form, 'cleaned_data'):
            email = form.cleaned_data.get('email')
            if email:
                request.session['signup_email'] = email
        
        return user

    def get_signup_redirect_url(self, request):
        """
        Get URL to redirect to after successful signup.
        """
        return super().get_signup_redirect_url(request)
    
    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """
        Override to add expire_days to email context.
        This is the correct method to override for Allauth 0.58.2+ versions.
        """
        # Get expiration days setting
        expire_days = int(getattr(settings, 'ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS', 7))
        
        # Build context (same as parent but with expire_days added)
        ctx = {
            "user": emailconfirmation.email_address.user,
            "expire_days": expire_days,  # ← ADD THIS
            "expiration_days": expire_days,  # Alternative name for compatibility
        }
        
        # Check if EMAIL_VERIFICATION_BY_CODE_ENABLED exists (may not in older Allauth versions)
        try:
            from allauth.account import app_settings
            email_verification_by_code_enabled = app_settings.EMAIL_VERIFICATION_BY_CODE_ENABLED
        except (ImportError, AttributeError):
            # Fallback for older Allauth versions that don't have this setting
            email_verification_by_code_enabled = False
        
        if email_verification_by_code_enabled:
            ctx.update({"code": emailconfirmation.key})
        else:
            ctx.update(
                {
                    "key": emailconfirmation.key,
                    "activate_url": self.get_email_confirmation_url(
                        request, emailconfirmation
                    ),
                }
            )
        
        if signup:
            email_template = "account/email/email_confirmation_signup"
        else:
            email_template = "account/email/email_confirmation"
        
        # Call send_mail with our context that includes expire_days
        self.send_mail(email_template, emailconfirmation.email_address.email, ctx)

    def render_mail(self, template_prefix, email, context, headers=None):
        """
        Override render_mail to ensure expire_days is present.
        This method is called by send_mail to render the email message.
        """
        # Call parent's render_mail with context (which should now have expire_days)
        msg = super().render_mail(template_prefix, email, context, headers)
        
        return msg

    def pre_authenticate(self, request, **kwargs):
        """
        Hook before authentication - can be used for audit logging.
        """
        return super().pre_authenticate(request, **kwargs)
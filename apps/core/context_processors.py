"""
Simple Context Processor for Comuniza.
Minimal dependencies and proper error handling.
"""

from django.conf import settings


def site_settings(request):
    """
    Add site-wide settings and session data to template context.
    Prioritizes database Site model over environment variables.
    Passes signup_email from session for email verification page.
    """
    try:
        # Try to get from database first
        from django.contrib.sites.models import Site
        site = Site.objects.get_current()
        site_name = site.name
        site_domain = site.domain
    except Exception:
        # Fallback to environment variables
        site_name = getattr(settings, 'SITE_NAME', 'Comuniza')
        site_domain = getattr(settings, 'SITE_DOMAIN', 'localhost:8000')

    # Get signup_email from session (set by ComunizaAccountAdapter during signup)
    signup_email = request.session.get('signup_email', '')

    return {
        'SITE_NAME': site_name,
        'SITE_DOMAIN': site_domain,
        'ENABLE_REGISTRATION': getattr(settings, 'ENABLE_REGISTRATION', True),
        'ENABLE_EMAIL_VERIFICATION': getattr(
            settings, 'ENABLE_EMAIL_VERIFICATION', False
        ),
        'DEBUG': getattr(settings, 'DEBUG', False),
        'signup_email': signup_email,  # Pass signup_email to all templates
    }


def notification_counts(request):
    """
    Add notification counts to template context for navigation badges.
    Uses signal-based notifications for efficiency.
    """
    if not request.user.is_authenticated:
        return {
            'unread_messages': 0,
            'pending_loans': 0,
        }

    user = request.user

    # Count unread notifications
    try:
        from apps.notifications.models import Notification
        unread_messages = Notification.objects.filter(
            user=user,
            notification_type='message',
            is_read=False
        ).count()

        # Count pending loan actions
        pending_loans = Notification.objects.filter(
            user=user,
            notification_type__in=['loan_request', 'loan_approved', 'loan_return_initiated', 'loan_returned', 'loan_extension_request', 'loan_extension_decision', 'loan_overdue'],
            is_read=False
        ).count()
    except Exception:
        # Fallback if models aren't available
        unread_messages = 0
        pending_loans = 0

    return {
        'unread_messages': unread_messages,
        'pending_loans': pending_loans,
    }

"""
Email notification service for Loans app.
Handles sending emails for loan activities.
"""

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from apps.core.utils import get_site_from_context


class EmailNotificationService:
    """
    Service for sending loan-related email notifications.
    """
    
    @staticmethod
    def send_loan_notification(loan, notification_type, recipient=None, request=None):
        """
        Send loan-related email notifications.

        Args:
            loan: Loan instance
            notification_type: Template name (e.g., 'loan_requested', 'loan_approved', 'loan_rejected',
                              'loan_return_request', 'loan_returned', 'loan_extension_request')
            recipient: User instance (defaults to appropriate user based on type)
        """
        if recipient is None:
            # Determine recipient based on notification type
            if notification_type == 'loan_requested':
                recipient = loan.lender
            elif notification_type in ['loan_approved', 'loan_rejected']:
                recipient = loan.borrower
            elif notification_type == 'loan_return_request':
                recipient = loan.lender
            elif notification_type == 'loan_returned':
                recipient = loan.lender
            elif notification_type == 'loan_extension_request':
                recipient = loan.lender
            elif notification_type == 'loan_extension_decision':
                recipient = loan.borrower
            else:
                return  # No valid recipient
        
        # Check if user wants email notifications
        user_settings = recipient.loan_settings
        if not user_settings.email_notifications:
            return
        
        # Prepare context
        site = get_site_from_context(request=request)
        
        # Get the proper site domain with protocol
        from django.conf import settings
        site_domain = getattr(settings, 'SITE_DOMAIN', site.domain)
        
        # Ensure the domain has the proper protocol
        if not site_domain.startswith('http://') and not site_domain.startswith('https://'):
            site_domain = f'https://{site_domain}'
        
        context = {
            'loan_id': loan.id,
            'recipient_id': recipient.id,
            'notification_type': notification_type,
            'site_domain': site_domain,
            'site_name': getattr(settings, 'SITE_NAME', site.name),
            'item_identifier': loan.item.identifier,  # Use identifier instead of slug
            'loan_id_for_url': loan.id,
            # Additional context for loan_requested template
            'request_message': getattr(loan, 'request_message', ''),
            'requested_at': getattr(loan, 'created_at', loan.created_at),
            'group': getattr(loan, 'group', None),
        }
        
        # Send email asynchronously
        from apps.notifications.tasks import send_loan_email_async
        send_loan_email_async.delay(
            recipient.email,
            notification_type,  # Template name already includes 'loan_' prefix in directory structure
            context
        )
    
    @staticmethod
    def send_message_notification(message, recipient):
        """
        Send email notification for loan-related messages.
        """
        # Check if user wants email notifications
        user_settings = recipient.loan_settings
        if not user_settings.message_notifications:
            return
        
        # Check if message has loan context
        loan_context = EmailNotificationService._extract_loan_context(message)
        if not loan_context['has_loan_context']:
            return  # Only send for loan-related messages
        
        site = get_site_from_context()
        
        # Get the proper site domain with protocol
        site_domain = getattr(settings, 'SITE_DOMAIN', site.domain)
        if not site_domain.startswith('http://') and not site_domain.startswith('https://'):
            site_domain = f'https://{site_domain}'
        
        context = {
            'message_id': message.id,
            'recipient_id': recipient.id,
            'sender_id': message.sender.id,
            'conversation_id': message.conversation.id,
            'site_domain': site_domain,
            'site_name': getattr(settings, 'SITE_NAME', site.name),
        }
        
        # Send email asynchronously
        from apps.notifications.tasks import send_message_email_async
        send_message_email_async.delay(
            recipient.email,
            'loan_message',
            context
        )
    
    @staticmethod
    def _extract_loan_context(message):
        """
        Extract loan context from message content.
        """
        if message.message_type != 'system':
            # Try to decrypt message to check content
            try:
                content = message.decrypt_content()
                if 'LOAN_CONTEXT:' in content:
                    return {'has_loan_context': True, 'context': content}
            except (ValueError, KeyError, AttributeError, Exception):
                pass
        else:
            if 'LOAN_CONTEXT:' in message.encrypted_content:
                return {'has_loan_context': True, 'context': message.encrypted_content}
        
        return {'has_loan_context': False}
    
    @staticmethod
    def send_review_notification(review):
        """
        Send email notification when a review is left.
        """
        recipient = review.reviewee
        
        # Check if user wants email notifications
        user_settings = recipient.loan_settings
        if not user_settings.email_notifications:
            return
        
        site = get_site_from_context()
        
        # Get the proper site domain with protocol
        site_domain = getattr(settings, 'SITE_DOMAIN', site.domain)
        if not site_domain.startswith('http://') and not site_domain.startswith('https://'):
            site_domain = f'https://{site_domain}'
        
        context = {
            'review_id': review.id,
            'recipient_id': recipient.id,
            'reviewer_id': review.reviewer.id,
            'loan_id': review.loan.id,
            'site_domain': site_domain,
            'site_name': getattr(settings, 'SITE_NAME', site.name),
            'loan_id_for_url': review.loan.id,
            'recipient_username': recipient.username,
        }
        
        # Send email asynchronously
        from apps.notifications.tasks import send_loan_email_async
        send_loan_email_async.delay(
            recipient.email,
            'loan_review',
            context
        )
    
    @staticmethod
    def send_overdue_reminder(loan):
        """
        Send overdue loan reminder to borrower.
        """
        if loan.status not in ['active', 'approved'] or not loan.is_overdue:
            return
        
        recipient = loan.borrower
        
        # Check if user wants email notifications
        user_settings = recipient.loan_settings
        if not user_settings.email_notifications:
            return
        
        site = get_site_from_context()
        
        # Get the proper site domain with protocol
        site_domain = getattr(settings, 'SITE_DOMAIN', site.domain)
        if not site_domain.startswith('http://') and not site_domain.startswith('https://'):
            site_domain = f'https://{site_domain}'
        
        context = {
            'loan_id': loan.id,
            'recipient_id': recipient.id,
            'site_domain': site_domain,
            'site_name': getattr(settings, 'SITE_NAME', site.name),
            'loan_id_for_url': loan.id,
            'days_overdue': loan.days_overdue,
            'due_date': loan.due_date,
        }
        
        # Send email asynchronously
        from apps.notifications.tasks import send_loan_email_async
        send_loan_email_async.delay(
            recipient.email,
            'loan_overdue',
            context
        )
    
    @staticmethod
    def send_extension_approval_notification(loan):
        """
        Send notification when extension is approved or rejected.
        """
        recipient = loan.borrower
        
        # Check if user wants email notifications
        user_settings = recipient.loan_settings
        if not user_settings.email_notifications:
            return
        
        site = get_site_from_context()
        
        # Get the proper site domain with protocol
        site_domain = getattr(settings, 'SITE_DOMAIN', site.domain)
        if not site_domain.startswith('http://') and not site_domain.startswith('https://'):
            site_domain = f'https://{site_domain}'
        
        context = {
            'loan_id': loan.id,
            'recipient_id': recipient.id,
            'site_domain': site_domain,
            'site_name': getattr(settings, 'SITE_NAME', site.name),
            'loan_id_for_url': loan.id,
            'extension_approved': loan.extension_approved,
            'new_due_date': loan.due_date,
        }
        
        # Send email asynchronously
        from apps.notifications.tasks import send_loan_email_async
        send_loan_email_async.delay(
            recipient.email,
            'loan_extension_decision',
            context
        )
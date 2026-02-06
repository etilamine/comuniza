"""
Celery tasks for async email sending and notifications.
"""

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import models
from apps.core.utils import get_site_from_context


@shared_task
def send_loan_email_async(recipient_email, template_name, context):
    """
    Send loan-related email asynchronously.

    Args:
        recipient_email: Email address to send to
        template_name: Template name (e.g., 'loan_requested', 'loan_approved', 'loan_returned')
        context: Template context dictionary
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"📧 Email task received - Recipient: {recipient_email}, Template: {template_name}")
    
    from apps.notifications import services as notification_services
    
    # Load loan from loan_id if present
    if 'loan_id' in context:
        from apps.loans.models import Loan
        try:
            loan = Loan.objects.select_related('borrower', 'lender', 'item').get(id=context['loan_id'])
            context['loan'] = loan
            
            # Add top-level variables for template compatibility
            context['borrower'] = loan.borrower
            context['lender'] = loan.lender
            context['item'] = loan.item
            
            # Add loan-specific variables
            if hasattr(loan, 'start_date') and loan.start_date:
                context['start_date'] = loan.start_date
            if hasattr(loan, 'due_date') and loan.due_date:
                context['due_date'] = loan.due_date
            if hasattr(loan, 'rejection_reason') and loan.rejection_reason:
                context['rejection_reason'] = loan.rejection_reason
            if hasattr(loan, 'extension_approved') and loan.extension_approved is not None:
                context['extension_approved'] = loan.extension_approved
            if hasattr(loan, 'new_due_date') and loan.new_due_date:
                context['new_due_date'] = loan.new_due_date
            # Additional variables for loan_requested template
            if hasattr(loan, 'request_message') and loan.request_message:
                context['request_message'] = loan.request_message
            if hasattr(loan, 'created_at') and loan.created_at:
                context['requested_at'] = loan.created_at
            elif hasattr(loan, 'created') and loan.created:
                context['requested_at'] = loan.created
            if hasattr(loan, 'group') and loan.group:
                context['group'] = loan.group
            
        except Exception as e:
            logger.error(f"Failed to load loan: {e}")
            return f"Failed to load loan: {str(e)}"

    # Load review from review_id if present
    if 'review_id' in context:
        from apps.loans.models import LoanReview
        review = LoanReview.objects.select_related('reviewer', 'reviewee', 'loan').get(id=context['review_id'])
        context['review'] = review

    # Load recipient from recipient_id if present
    if 'recipient_id' in context:
        from apps.users.models import User
        try:
            recipient = User.objects.get(id=context['recipient_id'])
            context['recipient'] = recipient
        except Exception as e:
            logger.error(f"Failed to load recipient: {e}")
            return f"Failed to load recipient: {str(e)}"

    # Load reviewer from reviewer_id if present
    if 'reviewer_id' in context:
        from apps.users.models import User
        reviewer = User.objects.get(id=context['reviewer_id'])
        context['reviewer'] = reviewer

    # Reconstruct URLs if components are provided
    # site_domain now includes the protocol (e.g., "https://comuniza.org")
    site_domain = context.get('site_domain', 'https://comuniza.org')
    
    # Ensure site_domain has protocol
    if not site_domain.startswith('http://') and not site_domain.startswith('https://'):
        site_domain = f'https://{site_domain}'
    
    if 'item_slug' in context:
        context['item_url'] = f"{site_domain}/i/{context['item_slug']}/"
    if 'loan_id_for_url' in context:
        context['loan_url'] = f"{site_domain}/loans/{context['loan_id_for_url']}/"
    context['messages_url'] = f"{site_domain}/messages/"
    if 'recipient_username' in context:
        context['profile_url'] = f"{site_domain}/users/{context['recipient_username']}/"
    
    # Get site - handles both request objects and domain strings
    if 'site_domain' in context:
        site = get_site_from_context(site_domain=context['site_domain'])
    else:
        site = get_site_from_context()
    
    # Render email templates
    template_path = f'notifications/email/{template_name}/'
    
    try:
        subject = render_to_string(
            f'{template_path}subject.txt',
            context
            ).strip()
        if not subject:
            logger.error("Subject is empty!")
            return "Subject template rendered empty content"
    except Exception as e:
        logger.error(f"Failed to render subject template: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Failed to render subject template: {str(e)}"
    
    try:
        html_message = render_to_string(
            f'{template_path}message.html',
            context
            )
        if len(html_message) < 50:
            logger.warning(f"HTML message seems short, preview: {html_message[:100]}")
    except Exception as e:
        logger.error(f"Failed to render HTML template: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Failed to render HTML template: {str(e)}"
    
    try:
        text_message = render_to_string(
            f'{template_path}message.txt',
            context
            )
        if len(text_message) < 20:
            logger.warning(f"Text message seems short, preview: {text_message[:100]}")
    except Exception as e:
        logger.error(f"Failed to render text template: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return f"Failed to render text template: {str(e)}"
    
    # Send email
    try:
        result = send_mail(
            subject=subject,
            message=text_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', f"noreply@{site.domain}"),
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email sent successfully to {recipient_email}")
        return f"Email sent successfully to {recipient_email}"
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {e}")
        import traceback
        logger.error(f"Email sending traceback: {traceback.format_exc()}")
        return f"Failed to send email to {recipient_email}: {str(e)}"


@shared_task
def send_message_email_async(recipient_email, template_name, context):
    """
    Send message-related email asynchronously.
    
    Args:
        recipient_email: Email address to send to
        template_name: Template name (e.g., 'loan_message')
        context: Template context dictionary
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Load message from message_id if present
        if 'message_id' in context:
            from apps.messaging.models import Message
            message = Message.objects.select_related('sender', 'conversation').get(id=context['message_id'])
            context['message'] = message

        # Load conversation from conversation_id if present
        if 'conversation_id' in context:
            from apps.messaging.models import Conversation
            conversation = Conversation.objects.get(id=context['conversation_id'])
            context['conversation'] = conversation

        # Load sender from sender_id if present
        if 'sender_id' in context:
            from apps.users.models import User
            sender = User.objects.get(id=context['sender_id'])
            context['sender'] = sender

        # Load recipient from recipient_id if present
        if 'recipient_id' in context:
            from apps.users.models import User
            recipient = User.objects.get(id=context['recipient_id'])
            context['recipient'] = recipient

        # Get site
        site = get_site_from_context()

        # Render email templates
        template_path = f'notifications/email/{template_name}/'
        
        subject = render_to_string(
            f'{template_path}subject.txt',
            context
        ).strip()
        
        html_message = render_to_string(
            f'{template_path}message.html',
            context
        )
        
        text_message = render_to_string(
            f'{template_path}message.txt',
            context
        )
        
        # Send email
        send_mail(
            subject=subject,
            message=text_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', f"noreply@{site.domain}"),
            recipient_list=[recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Message email sent successfully to {recipient_email}")
        return f"Message email sent successfully to {recipient_email}"
        
    except Exception as e:
        logger.error(f"Failed to send message email to {recipient_email}: {e}")
        return f"Failed to send message email to {recipient_email}: {str(e)}"


@shared_task
def send_overdue_reminders():
    """
    Daily task to send overdue loan reminders.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    from apps.loans.models import Loan
    from apps.notifications.services import EmailNotificationService
    from apps.notifications.tasks import send_loan_email_async
    
    try:
        # Get all overdue active loans
        overdue_loans = Loan.objects.filter(
            status__in=['active', 'approved'],
            due_date__lt=timezone.now().date()
        ).select_related('borrower', 'item', 'lender')
        
        for loan in overdue_loans:
            # Send reminder to borrower
            EmailNotificationService.send_overdue_reminder(loan)
        
        logger.info(f"Sent {len(overdue_loans)} overdue reminders")
        return f"Sent {len(overdue_loans)} overdue reminders"
        
    except Exception as e:
        logger.error(f"Failed to send overdue reminders: {e}")
        return f"Failed to send overdue reminders: {str(e)}"


@shared_task
def create_loan_conversations_for_new_loans():
    """
    Background task to create conversations for new loan requests.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    from apps.loans.models import Loan
    from apps.loans.services import LoanService
    
    try:
        # Get loans without conversations
        new_loans = Loan.objects.filter(
            status='requested'
        ).select_related('borrower', 'lender', 'item')
        
        for loan in new_loans:
            # Check if conversation already exists
            from apps.messaging.models import Conversation
            existing_conversation = Conversation.objects.filter(
                participants=loan.borrower
            ).filter(participants=loan.lender).annotate(
                num_participants=models.Count('participants')
            ).filter(num_participants=2).first()
            
            if not existing_conversation:
                LoanService.create_loan_conversation(loan)
        
        logger.info(f"Created conversations for {len(new_loans)} loans")
        return f"Created conversations for {len(new_loans)} loans"
        
    except Exception as e:
        logger.error(f"Failed to create loan conversations: {e}")
        return f"Failed to create loan conversations: {str(e)}"


@shared_task
def update_loan_reputations():
    """
    Daily task to update user reputations based on completed loans.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    from apps.loans.models import LoanReview
    
    try:
        # Get recent reviews that haven't been processed
        recent_reviews = LoanReview.objects.all()
        
        updated_users = set()
        for review in recent_reviews:
            if review.reviewee.reputation.calculate_ratings():
                updated_users.add(review.reviewee.id)
        
        logger.info(f"Updated reputations for {len(updated_users)} users")
        return f"Updated reputations for {len(updated_users)} users"
        
    except Exception as e:
        logger.error(f"Failed to update reputations: {e}")
        return f"Failed to update reputations: {str(e)}"
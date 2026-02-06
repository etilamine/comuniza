from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.conf import settings

# Import models when needed to avoid circular imports
def get_notification_model():
    from .models import Notification
    return Notification

def get_loan_model():
    from apps.loans.models import Loan
    return Loan

def get_conversation_model():
    from apps.messaging.models import Conversation
    return Conversation

def get_message_model():
    from apps.messaging.models import Message
    return Message

def get_loan_review_model():
    from apps.loans.models import LoanReview
    return LoanReview

@receiver(post_save, sender=get_message_model())
def create_message_notification(sender, instance, created, **kwargs):
    """Create notification when a new message is sent."""
    if not created:
        return

    # Create notifications for all participants except the sender
    conversation = instance.conversation
    for participant_detail in conversation.participant_details.exclude(user=instance.sender):
        Notification = get_notification_model()
        Notification.objects.create(
            user=participant_detail.user,
            notification_type='message',
            title=f"New message in conversation",
            message=instance.encrypted_content[:100] + ('...' if len(instance.encrypted_content) > 100 else ''),
            related_conversation=conversation,
        )

@receiver(post_save, sender=get_loan_model())
def create_loan_notifications(sender, instance, created, **kwargs):
    """Create notifications for loan status changes."""
    Notification = get_notification_model()

    if created:
        # Handle new loan requests
        if instance.status == 'requested':
            Notification.objects.create(
                user=instance.lender,
                notification_type='loan_request',
                title=f"Loan request for {instance.item.title}",
                message=f"{instance.borrower.get_display_name()} wants to borrow your item.",
                related_loan=instance,
            )
        return

    # Handle status changes for existing loans
    old_status = getattr(instance, '_previous_status', None)
    if old_status is None or old_status == instance.status:
        return

    if instance.status == 'approved':
        # Notify borrower of approval
        Notification.objects.create(
            user=instance.borrower,
            notification_type='loan_approved',
            title=f"Loan approved for {instance.item.title}",
            message="Your loan request has been approved. Please arrange pickup.",
            related_loan=instance,
        )
    elif instance.status == 'active':
        # Notify lender that item was picked up
        Notification.objects.create(
            user=instance.lender,
            notification_type='loan_pickup',
            title=f"Item picked up: {instance.item.title}",
            message=f"{instance.borrower.get_display_name()} has picked up your item and the loan is now active.",
            related_loan=instance,
        )
    elif instance.status == 'borrower_returned':
        # Notify lender that borrower has returned the item
        Notification.objects.create(
            user=instance.lender,
            notification_type='loan_return_initiated',
            title=f"Item returned by borrower: {instance.item.title}",
            message=f"{instance.borrower.get_display_name()} has marked your item as returned. Please confirm receipt.",
            related_loan=instance,
        )
    elif instance.status == 'returned':
        # Notify lender that item has been returned
        Notification.objects.create(
            user=instance.lender,
            notification_type='loan_returned',
            title=f"Item returned: {instance.item.title}",
            message=f"{instance.borrower.get_display_name()} has returned your item.",
            related_loan=instance,
        )
    elif instance.status == 'rejected':
        # Notify borrower of rejection
        Notification.objects.create(
            user=instance.borrower,
            notification_type='loan_rejected',
            title=f"Loan rejected for {instance.item.title}",
            message=f"Your loan request was rejected.{' Reason: ' + instance.rejection_reason if hasattr(instance, 'rejection_reason') and instance.rejection_reason else ''}",
            related_loan=instance,
        )
    elif instance.status == 'overdue':
        # Notify both parties of overdue loan
        for user in [instance.borrower, instance.lender]:
            Notification.objects.create(
                user=user,
                notification_type='loan_overdue',
                title=f"Loan overdue: {instance.item.title}",
                message=f"This loan is now overdue. Please contact each other to resolve.",
                related_loan=instance,
            )

@receiver(post_save, sender=get_loan_review_model())
def create_review_notification(sender, instance, created, **kwargs):
    """Create notification when a loan review is left."""
    if not created:
        return

    Notification = get_notification_model()

    # Notify the reviewee (the person being reviewed)
    Notification.objects.create(
        user=instance.reviewee,
        notification_type='review_received',
        title=f"New review received",
        message=f"{instance.reviewer.get_display_name()} left you a review for your {instance.loan.item.title} loan.",
        related_loan=instance.loan,
    )

# Connect signals when the app is ready
def connect_signals():
    """Connect all notification signals."""
    from django.apps import apps
    from django.db import models

    # Get model classes
    try:
        Message = apps.get_model('messaging', 'Message')
        Loan = apps.get_model('loans', 'Loan')
        LoanReview = apps.get_model('loans', 'LoanReview')

        # Connect signals
        post_save.connect(create_message_notification, sender=Message)
        post_save.connect(create_loan_notifications, sender=Loan)
        post_save.connect(create_review_notification, sender=LoanReview)

    except LookupError:
        # Models not available yet
        pass
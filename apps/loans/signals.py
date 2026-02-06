"""
Django signals for Loans app.
Handles automatic creation of UserLoanSettings and email notifications.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.db import connection

User = get_user_model()


# Import models here to avoid circular imports and use actual class references
from apps.loans.models import Loan, LoanReview


@receiver(post_save, sender=User)
def create_user_loan_settings(sender, instance, created, **kwargs):
    """
    Create UserLoanSettings for new users automatically.
    
    This ensures that every user has loan settings before any loan-related
    notifications or actions are attempted, preventing DoesNotExist errors.
    """
    if created:
        from apps.loans.models import UserLoanSettings
        UserLoanSettings.objects.get_or_create(user=instance)


@receiver(pre_save, sender=Loan)
def on_loan_pre_save(sender, instance, **kwargs):
    """
    Store the old status and extension_approved before save to detect changes.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if instance.pk:
        # Get the current values from database
        try:
            old_instance = Loan.objects.filter(pk=instance.pk).only('status', 'extension_approved').first()
            if old_instance:
                instance._previous_status = old_instance.status
                instance._previous_extension_approved = old_instance.extension_approved
                logger.info(f"📊 Pre-save: Loan {instance.id} old status = {old_instance.status}, extension_approved = {old_instance.extension_approved}")
        except Loan.DoesNotExist:
            instance._previous_status = None
            instance._previous_extension_approved = None
            logger.warning(f"⚠️  Pre-save: Loan {instance.id} not found in database")
    else:
        instance._previous_status = None
        instance._previous_extension_approved = None
        logger.info(f"📊 Pre-save: New loan, no previous status")


@receiver(post_save, sender=Loan)
def on_loan_saved(sender, instance, created, **kwargs):
    """
    Send email notifications on loan status changes and new loan requests.
    Also handle cache invalidation for loan changes.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔔 Post-save: Loan {instance.id}, status: {instance.status}, created: {created}")
    
    # Note: Removed atomic block check to ensure emails are sent consistently
    # The view-level email sending has been removed to prevent duplicates
    
    # Handle cache invalidation first
    from apps.core.ultra_cache import get_ultimate_cache
    cache = get_ultimate_cache()
    
    # Invalidate item detail cache
    if instance.item_id:
        cache.invalidate_pattern(f'item_detail:{instance.item_id}:*')
    
    # Invalidate user item stats for both borrower and lender
    if instance.borrower_id:
        cache.invalidate_pattern(f'user_item_stats:{instance.borrower_id}:*')
        cache.invalidate_pattern(f'user_scores:{instance.borrower_id}:*')
    
    if instance.lender_id:
        cache.invalidate_pattern(f'user_item_stats:{instance.lender_id}:*')
        cache.invalidate_pattern(f'user_scores:{instance.lender_id}:*')
    
    # Invalidate loan-related caches
    cache.invalidate_pattern('user_loans:*')
    cache.invalidate_pattern('my_loans:*')
    
    from apps.notifications.services import EmailNotificationService
    
    # Handle new loan creation
    if created:
        if instance.status == 'requested':
            logger.info(f"📧 Sending 'loan_requested' notification to lender: {instance.lender.email}")
            EmailNotificationService.send_loan_notification(instance, 'loan_requested', instance.lender)
        else:
            logger.info(f"ℹ️  New loan created with status '{instance.status}', no notification needed")
        return
    
    # Handle status changes for existing loans
    old_status = getattr(instance, '_previous_status', None)
    old_extension_approved = getattr(instance, '_previous_extension_approved', None)
    
    if old_status is None:
        logger.info(f"ℹ️  Existing loan without previous status, skipping notification")
        return
    
    # Check for status changes
    if old_status != instance.status:
        logger.info(f"✅ Status changed: {old_status} → {instance.status}")
        
        # Send notifications based on status change
        try:
            if instance.status == 'approved':
                logger.info(f"📧 Sending 'loan_approved' notification to borrower: {instance.borrower.email}")
                EmailNotificationService.send_loan_notification(instance, 'loan_approved', instance.borrower)
            elif instance.status == 'rejected':
                logger.info(f"📧 Sending 'loan_rejected' notification to borrower: {instance.borrower.email}")
                EmailNotificationService.send_loan_notification(instance, 'loan_rejected', instance.borrower)
            elif instance.status == 'returned':
                logger.info(f"📧 Sending 'loan_returned' notification to lender: {instance.lender.email}")
                EmailNotificationService.send_loan_notification(instance, 'loan_returned', instance.lender)
            else:
                logger.info(f"ℹ️  No notification configured for status: {instance.status}")
        except Exception as e:
            logger.error(f"❌ Error sending notification: {e}", exc_info=True)
    
    # Check for extension decision changes (when extension_requested was True)
    elif old_extension_approved is not None and old_extension_approved != instance.extension_approved:
        logger.info(f"✅ Extension decision changed: {old_extension_approved} → {instance.extension_approved}")
        
        # Send extension decision notification
        try:
            logger.info(f"📧 Sending 'loan_extension_decision' notification to borrower: {instance.borrower.email}")
            EmailNotificationService.send_loan_notification(instance, 'loan_extension_decision', instance.borrower)
        except Exception as e:
            logger.error(f"❌ Error sending extension decision notification: {e}", exc_info=True)
    
    else:
        logger.info(f"⏭️  Skipping - no relevant changes detected")


@receiver(post_save, sender=LoanReview)
def on_review_saved(sender, instance, created, **kwargs):
    """
    Send email notifications when reviews are created.
    """
    if not created:
        return
    
    # Note: Removed atomic block check to ensure emails are sent consistently
    # The view-level email sending has been removed to prevent duplicates
    
    from apps.notifications.services import EmailNotificationService
    
    try:
        EmailNotificationService.send_review_notification(instance)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send review notification: {e}")

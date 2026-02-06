from django.db import models

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    """
    User notifications for messages, loans, etc.
    """

    NOTIFICATION_TYPES = [
        ('message', _('New Message')),
        ('loan_request', _('Loan Request')),
        ('loan_approved', _('Loan Approved')),
        ('loan_pickup', _('Item Picked Up')),
        ('loan_return_initiated', _('Return Initiated')),
        ('loan_returned', _('Item Returned')),
        ('loan_rejected', _('Loan Rejected')),
        ('loan_extension_request', _('Extension Request')),
        ('loan_extension_decision', _('Extension Decision')),
        ('loan_overdue', _('Loan Overdue')),
        ('review_received', _('Review Received')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('user')
    )

    notification_type = models.CharField(
        _('type'),
        max_length=25,
        choices=NOTIFICATION_TYPES,
        default='message'
    )

    title = models.CharField(_('title'), max_length=200)
    message = models.TextField(_('message'))

    # Related objects (optional)
    related_loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('related loan')
    )
    related_conversation = models.ForeignKey(
        'messaging.Conversation',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('related conversation')
    )

    # Status
    is_read = models.BooleanField(_('read'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['notification_type']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.title}"

    def mark_as_read(self):
        """Mark notification as read."""
        self.is_read = True
        self.save(update_fields=['is_read'])

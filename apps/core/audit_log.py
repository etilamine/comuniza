"""
Audit logging system for GDPR compliance and security monitoring.
Tracks sensitive operations, authentication events, and data access.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class AuditLogManager(models.Manager):
    """Custom manager for audit logs with useful query methods"""

    def get_user_activity(self, user, days=30):
        """Get recent activity for a specific user"""
        from django.utils import timezone
        since = timezone.now() - timezone.timedelta(days=days)
        return self.filter(user=user, timestamp__gte=since)

    def get_security_events(self, severity=None, days=7):
        """Get security-related events"""
        from django.utils import timezone
        since = timezone.now() - timezone.timedelta(days=days)
        queryset = self.filter(timestamp__gte=since)
        if severity:
            queryset = queryset.filter(severity=severity)
        return queryset.filter(
            action__in=[
                AuditLog.ACTION_LOGIN_FAILED,
                AuditLog.ACTION_ADMIN_ACTION,
                AuditLog.ACTION_DATA_EXPORT,
            ]
        )


class AuditLog(models.Model):
    """
    Comprehensive audit logging for security and compliance.
    Tracks all sensitive operations and authentication events.
    """

    objects = AuditLogManager()

    # Actor information
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='audit_logs',
        verbose_name=_('user')
    )
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        help_text=_('Django session key for tracking')
    )

    # Action details
    action = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name=_('action')
    )
    resource_type = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name=_('resource type')
    )
    resource_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('resource ID')
    )

    # Request context
    ip_address = models.GenericIPAddressField(
        db_index=True,
        verbose_name=_('IP address')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=_('user agent')
    )
    method = models.CharField(
        max_length=10,
        verbose_name=_('HTTP method')
    )
    path = models.TextField(
        verbose_name=_('request path')
    )

    # Event data
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name=_('timestamp')
    )
    details = models.JSONField(
        default=dict,
        help_text=_('Additional event details'),
        verbose_name=_('details')
    )
    old_values = models.JSONField(
        null=True,
        blank=True,
        help_text=_('Previous values for data changes'),
        verbose_name=_('old values')
    )
    new_values = models.JSONField(
        null=True,
        blank=True,
        help_text=_('New values for data changes'),
        verbose_name=_('new values')
    )

    # Classification
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Low')),
            ('medium', _('Medium')),
            ('high', _('High')),
            ('critical', _('Critical'))
        ],
        default='low',
        verbose_name=_('severity')
    )

    # Predefined action types for consistency
    ACTION_LOGIN_SUCCESS = 'login_success'
    ACTION_LOGIN_FAILED = 'login_failed'
    ACTION_LOGOUT = 'logout'
    ACTION_PASSWORD_CHANGE = 'password_change'
    ACTION_ITEM_CREATED = 'item_created'
    ACTION_ITEM_UPDATED = 'item_updated'
    ACTION_ITEM_DELETED = 'item_deleted'
    ACTION_ITEM_ACCESSED = 'item_accessed'
    ACTION_LOAN_CREATED = 'loan_created'
    ACTION_LOAN_COMPLETED = 'loan_completed'
    ACTION_USER_REGISTERED = 'user_registered'
    ACTION_USER_PROFILE_UPDATED = 'user_profile_updated'
    ACTION_GROUP_CREATED = 'group_created'
    ACTION_GROUP_JOINED = 'group_joined'
    ACTION_MESSAGE_SENT = 'message_sent'
    ACTION_ADMIN_ACTION = 'admin_action'
    ACTION_DATA_EXPORT = 'data_export'

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        verbose_name = _('audit log')
        verbose_name_plural = _('audit logs')
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
        ]

    def __str__(self):
        user_info = f"User {self.user_id}" if self.user else "Anonymous"
        return f"{user_info} - {self.action} - {self.timestamp}"
"""
Audit logging system for GDPR compliance and security monitoring.
Tracks sensitive operations, authentication events, and data access.
"""

import logging
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from .audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditManager:
    """
    Central audit logging manager with helper methods.
    Handles logging of security events and sensitive operations.
    """

    @staticmethod
    def log_event(request=None, action='', resource_type='', resource_id=None,
                  details=None, severity='low', old_values=None, new_values=None,
                  user=None, ip_address=None, user_agent=None):
        """
        Log an audit event with automatic context extraction.

        Args:
            request: Django request object (optional)
            action: Action being performed
            resource_type: Type of resource (item, user, loan, etc.)
            resource_id: ID of the resource
            details: Additional context data
            severity: low, medium, high, critical
            old_values: Previous values for updates
            new_values: New values for updates/creates
            user: User performing action (if not from request)
            ip_address: IP address (if not from request)
            user_agent: User agent string (if not from request)
        """
        try:
            # Extract context from request if available
            if request:
                user = user or getattr(request, 'user', None)
                if user and not user.is_authenticated:
                    user = None

                ip_address = ip_address or AuditManager._get_client_ip(request)
                user_agent = user_agent or request.META.get('HTTP_USER_AGENT', '')
                method = request.method
                path = request.path
            else:
                method = None
                path = None

            # Create audit log entry
            audit_log = AuditLog.objects.create(
                user=user,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent[:1000] if user_agent else '',  # Truncate if too long
                method=method,
                path=path,
                details=details or {},
                old_values=old_values,
                new_values=new_values,
                severity=severity
            )

            # Log security events to separate logger
            if severity in ['high', 'critical']:
                logger.warning(
                    f"AUDIT: {action} by {user} from {ip_address}",
                    extra={
                        'user_id': user.id if user else None,
                        'action': action,
                        'resource_type': resource_type,
                        'resource_id': resource_id,
                        'severity': severity
                    }
                )

            return audit_log

        except Exception as e:
            logger.error(f"Failed to create audit log: {e}", exc_info=True)
            # Don't raise exception to avoid breaking application flow
            return None

    @staticmethod
    def _get_client_ip(request):
        """Get real client IP from request headers"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def log_model_change(instance, action, request=None, old_instance=None):
        """
        Log changes to model instances.
        Automatically captures old/new values for updates.
        """
        resource_type = instance.__class__.__name__.lower()
        resource_id = instance.pk

        if action == 'update' and old_instance:
            # Compare fields to identify changes
            old_values = {}
            new_values = {}
            for field in instance._meta.fields:
                field_name = field.name
                old_value = getattr(old_instance, field_name, None)
                new_value = getattr(instance, field_name, None)
                if old_value != new_value:
                    old_values[field_name] = str(old_value) if old_value is not None else None
                    new_values[field_name] = str(new_value) if new_value is not None else None

            AuditManager.log_event(
                request=request,
                action=f"{resource_type}_updated",
                resource_type=resource_type,
                resource_id=resource_id,
                old_values=old_values,
                new_values=new_values,
                severity='low'
            )
        else:
            # Create or delete
            values = {}
            if action != 'delete':
                for field in instance._meta.fields:
                    value = getattr(instance, field.name, None)
                    if value is not None:
                        values[field.name] = str(value)

            AuditManager.log_event(
                request=request,
                action=f"{resource_type}_{action}d",
                resource_type=resource_type,
                resource_id=resource_id,
                new_values=values if action == 'create' else None,
                severity='low'
            )

    @staticmethod
    def log_auth_event(request, action, user=None, details=None):
        """Log authentication-related events"""
        severity = 'high' if action == 'login_failed' else 'low'

        AuditManager.log_event(
            request=request,
            action=action,
            resource_type='user',
            resource_id=user.id if user else None,
            details=details,
            severity=severity
        )

    @staticmethod
    def log_security_event(request, action, details=None, severity='medium'):
        """Log security-related events (failed attempts, suspicious activity)"""
        AuditManager.log_event(
            request=request,
            action=action,
            resource_type='security',
            details=details,
            severity=severity
        )
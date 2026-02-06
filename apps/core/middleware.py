"""
Middleware for automatic audit logging.
Intercepts requests and logs security events automatically.
"""

import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .audit import AuditManager
from .audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware that automatically logs security events and sensitive operations.
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Set up Django signal handlers for automatic logging"""

        # Authentication signals
        user_logged_in.connect(self._handle_login_success)
        user_logged_out.connect(self._handle_logout)
        user_login_failed.connect(self._handle_login_failed)

        # Model change signals for sensitive models
        # Note: We use selective logging to avoid performance impact
        sensitive_models = [
            'User', 'Item', 'Loan', 'Group',
            # Add other sensitive models as needed
        ]

        for model_name in sensitive_models:
            try:
                # We'll implement this in individual model save methods
                # to have more control over what gets logged
                pass
            except ImportError:
                pass  # Model might not exist yet during startup

    def process_request(self, request):
        """Store request start time for performance monitoring"""
        request._audit_start_time = None  # Could be used for performance logging
        return None

    def process_response(self, request, response):
        """Log suspicious or important requests"""

        # Log failed authentication attempts
        if (hasattr(request, 'path') and
            'login' in request.path and
            response.status_code in [401, 403]):
            AuditManager.log_security_event(
                request,
                'authentication_failed',
                details={'status_code': response.status_code},
                severity='medium'
            )

        # Log admin access
        if (hasattr(request, 'path') and
            request.path.startswith('/admin/') and
            hasattr(request, 'user') and
            request.user.is_authenticated):
            AuditManager.log_event(
                request,
                AuditLog.ACTION_ADMIN_ACTION,
                'admin',
                details={'path': request.path, 'method': request.method},
                severity='low'
            )

        return response

    def process_exception(self, request, exception):
        """Log exceptions that might indicate attacks"""
        AuditManager.log_security_event(
            request,
            'application_error',
            details={
                'exception': str(exception),
                'path': request.path,
                'method': request.method
            },
            severity='high'
        )
        return None

    # Signal handlers
    def _handle_login_success(self, sender, request, user, **kwargs):
        """Handle successful login"""
        AuditManager.log_auth_event(
            request,
            AuditLog.ACTION_LOGIN_SUCCESS,
            user=user
        )

    def _handle_logout(self, sender, request, user, **kwargs):
        """Handle user logout"""
        AuditManager.log_event(
            request,
            AuditLog.ACTION_LOGOUT,
            resource_type='user',
            resource_id=user.id if user else None,
            severity='low'
        )

    def _handle_login_failed(self, sender, credentials, **kwargs):
        """Handle failed login attempts"""
        # Note: This signal doesn't provide request object in all cases
        # We'll handle this in the middleware process_response instead
        pass


# Additional utility functions for manual logging
def log_data_access(request, resource_type, resource_id, action='access'):
    """Log data access for GDPR compliance"""
    AuditManager.log_event(
        request,
        f"{resource_type}_{action}",
        resource_type,
        resource_id,
        severity='low'
    )


def log_security_incident(request, incident_type, details=None):
    """Log security incidents"""
    AuditManager.log_security_event(
        request,
        incident_type,
        details=details,
        severity='high'
    )


def log_admin_action(request, action, details=None):
    """Log administrative actions"""
    AuditManager.log_event(
        request,
        action,
        'admin',
        details=details,
        severity='medium'
    )
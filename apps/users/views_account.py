"""
Custom account views for email confirmation and verification.
Extends allauth views to add custom context and behavior.
"""

from django.shortcuts import render, redirect
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

from allauth.account.models import EmailConfirmation, EmailAddress
from allauth.account.utils import perform_login

User = get_user_model()


class EmailConfirmationView(View):
    """
    Custom email confirmation view that passes expiration days to template.
    """
    
    template_name = "account/email_confirm.html"
    
    @method_decorator(require_http_methods(["GET", "POST"]))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Build context with expiration information."""
        context = kwargs
        context['expiration_days'] = settings.ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS
        return context
    
    def get(self, request, key):
        """
        Confirm email address with the given key.
        """
        try:
            email_confirmation = EmailConfirmation.objects.get(key=key)
            
            context = self.get_context_data()
            context['confirmation'] = email_confirmation
            context['email'] = email_confirmation.email_address.email
            
            return render(request, self.template_name, context)
        except EmailConfirmation.DoesNotExist:
            context = self.get_context_data()
            context['confirmation'] = None
            return render(request, self.template_name, context)
    
    def post(self, request, key):
        """
        Process email confirmation form submission.
        """
        try:
            email_confirmation = EmailConfirmation.objects.get(key=key)
            email_confirmation.confirm(request)
            
            # Log the user in if configured
            if settings.ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION:
                user = email_confirmation.email_address.user
                perform_login(request, user, email_verification='optional')
                messages.success(request, _("Email confirmed successfully! You are now logged in."))
                return redirect(settings.ACCOUNT_EMAIL_VERIFICATION_REDIRECT_URL)
            else:
                messages.success(request, _("Email confirmed successfully!"))
                return redirect('account_login')
                
        except EmailConfirmation.DoesNotExist:
            messages.error(request, _("Invalid or expired confirmation link."))
            context = self.get_context_data()
            context['confirmation'] = None
            return render(request, self.template_name, context)
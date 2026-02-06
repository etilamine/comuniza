"""
Core views for Comuniza.
Error handlers and utility views.
"""

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)


class HomePageView(TemplateView):
    """
    Homepage with hero section and group map.
    Shows different content for authenticated vs non-authenticated users.
    """

    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add statistics for homepage
        from apps.groups.models import Group
        from apps.items.models import Item
        from apps.users.models import User

        context["total_groups"] = Group.objects.filter(is_active=True).count()
        context["total_items"] = Item.objects.filter(is_active=True).count()
        context["total_users"] = User.objects.filter(is_active=True).count()
        context["available_items"] = Item.objects.filter(
            is_active=True, status="available"
        ).count()

        return context


def home_view(request):
    """
    Simple function-based view for homepage.
    """
    from apps.groups.models import Group
    from apps.items.models import Item
    from apps.users.models import User

    context = {
        "total_groups": Group.objects.filter(is_active=True).count(),
        "total_items": Item.objects.filter(is_active=True).count(),
        "total_users": User.objects.filter(is_active=True).count(),
        "available_items": Item.objects.filter(
            is_active=True, status="available"
        ).count(),
    }

    return render(request, "home.html", context)


# Error handlers
def handler404(request, exception):
    """
    Custom 404 error handler.
    """
    return render(request, '404.html', status=404)


def handler500(request):
    """
    Custom 500 error handler.
    """
    return render(request, '500.html', status=500)


def handler405(request, exception):
    """
    Custom 405 error handler.
    """
    return render(request, '405.html', status=405)


@csrf_exempt
def report_bug(request):
    """
    Handle bug report submissions from error pages.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        # Extract form data
        description = request.POST.get('description', '').strip()
        user_email = request.POST.get('user_email', '').strip()
        severity = request.POST.get('severity', 'medium')
        error_type = request.POST.get('error_type', 'unknown')
        current_url = request.POST.get('current_url', '')
        user_agent = request.POST.get('user_agent', '')
        referrer = request.POST.get('referrer', '')

        # Validate required fields
        if not description:
            return JsonResponse({'success': False, 'error': 'Description is required'}, status=400)

        if len(description) > 1000:
            return JsonResponse({'success': False, 'error': 'Description too long'}, status=400)

        # Prepare email content
        subject = f"[{severity.upper()}] Comuniza Bug Report - {error_type} Error"

        body = f"""
Bug Report Details:
===================

Timestamp: {timezone.now()}
Severity: {severity}
Error Type: {error_type}
URL: {current_url}
Referrer: {referrer}
User Agent: {user_agent}

Description:
{description}

Reporter Email: {user_email if user_email else 'Not provided'}

User Info:
----------
{Authenticated: {'Yes' if request.user.is_authenticated else 'No'}}
{Username: {request.user.username if request.user.is_authenticated else 'Not provided'}}
{'User ID: ' + str(request.user.id) if request.user.is_authenticated else ''}

Technical Details:
-----------------
Remote IP: {request.META.get('REMOTE_ADDR', 'Unknown')}
HTTP Method: {request.method}
Content Type: {request.META.get('CONTENT_TYPE', 'Unknown')}
"""

        # Send email
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['bugs@comuniza.org'],
            fail_silently=False
        )

        logger.info(f"Bug report sent: {severity} - {error_type} - {description[:100]}...")

        return JsonResponse({
            'success': True,
            'message': 'Bug report sent successfully! Thank you for helping us improve Comuniza.'
        })

    except Exception as e:
        logger.error(f"Failed to send bug report: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to send bug report. Please try again or contact support@comuniza.org directly.'
        }, status=500)


def bug_report_page(request):
    """
    Dedicated bug report page for users to submit issues and suggestions.
    """
    if request.method == 'POST':
        # Extract form data
        category = request.POST.get('category', '').strip()
        severity = request.POST.get('severity', 'medium')
        description = request.POST.get('description', '').strip()
        user_email = request.POST.get('user_email', '').strip()
        current_url = request.POST.get('current_url', '')
        user_agent = request.POST.get('user_agent', '')
        referrer = request.POST.get('referrer', '')

        # Validate required fields
        if not description:
            messages.error(request, 'Please provide a description of the issue.')
            return render(request, 'bug_report.html')

        if len(description) > 1000:
            messages.error(request, 'Description is too long (maximum 1000 characters).')
            return render(request, 'bug_report.html')

        if not category:
            messages.error(request, 'Please select a category.')
            return render(request, 'bug_report.html')

        # Category display names
        category_names = {
            'ui': 'User Interface',
            'functionality': 'Functionality',
            'performance': 'Performance',
            'security': 'Security',
            'feature': 'Feature Request',
            'other': 'Other'
        }

        # Prepare email content
        subject = f"[{severity.upper()}] {category_names.get(category, category)} Bug Report - Comuniza"

        body = f"""
Bug Report Details:
===================

Timestamp: {timezone.now()}
Category: {category_names.get(category, category)}
Severity: {severity}
URL: {current_url}
Referrer: {referrer}
User Agent: {user_agent}

Description:
{description}

Reporter Email: {user_email if user_email else 'Not provided'}

User Info:
----------
{Authenticated: {'Yes' if request.user.is_authenticated else 'No'}}
{Username: {request.user.username if request.user.is_authenticated else 'Not provided'}}
{'User ID: ' + str(request.user.id) if request.user.is_authenticated else ''}

Technical Details:
-----------------
Remote IP: {request.META.get('REMOTE_ADDR', 'Unknown')}
HTTP Method: {request.method}
Content Type: {request.META.get('CONTENT_TYPE', 'Unknown')}
"""

        # Send email
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['bugs@comuniza.org'],
                fail_silently=False
            )

            logger.info(f"Bug report submitted: {severity} - {category} - {description[:100]}...")
            messages.success(request, 'Bug report submitted successfully! Thank you for helping us improve Comuniza.')

            # Redirect to home page after successful submission
            return redirect('home')

        except Exception as e:
            logger.error(f"Failed to send bug report from page: {e}")
            messages.error(request, 'Failed to send bug report. Please try again or contact support@comuniza.org directly.')

    return render(request, 'bug_report.html')

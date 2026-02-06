# Template tags for loans app
from apps.loans.models import LoanReview
from django import template

register = template.Library()


@register.filter
def multiply(value, arg):
    """Multiply a string by an integer to repeat it."""
    try:
        return str(value) * int(arg)
    except (ValueError, TypeError):
        return ''


@register.filter
def stars(value):
    """Convert a rating number to star characters."""
    try:
        rating = int(value)
        return "★" * rating
    except (ValueError, TypeError):
        return ''

@register.filter
def user_has_reviewed_loan(loan, user):
    """Check if user has already reviewed this loan."""
    if not loan or not user:
        return False
    return LoanReview.objects.filter(loan=loan, reviewer=user).exists()

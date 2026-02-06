"""
Template tags for messaging app.
"""

from django import template
from django.utils.safestring import mark_safe
import re
import ast

register = template.Library()


@register.filter
def loan_context_item_title(message):
    """
    Extract item title from loan context in message.
    """
    if not message or not hasattr(message, 'decrypt_content'):
        return ""

    content = message.decrypt_content()
    match = re.search(r'\[LOAN_CONTEXT:(\{.*?\})\]', content)
    if match:
        try:
            context = ast.literal_eval(match.group(1))
            return context.get('item_title', '')
        except (ValueError, SyntaxError):
            pass
    return ""


@register.filter
def loan_context_action_required(message):
    """
    Check if loan context requires action.
    """
    if not message or not hasattr(message, 'decrypt_content'):
        return False

    content = message.decrypt_content()
    match = re.search(r'\[LOAN_CONTEXT:(\{.*?\})\]', content)
    if match:
        try:
            context = ast.literal_eval(match.group(1))
            return context.get('action_required', False)
        except (ValueError, SyntaxError):
            pass
    return False


@register.filter
def loan_context_loan(message):
    """
    Extract loan object from loan context in message.
    """
    if not message or not hasattr(message, 'decrypt_content'):
        return None

    content = message.decrypt_content()
    match = re.search(r'\[LOAN_CONTEXT:(\{.*?\})\]', content)
    if match:
        try:
            context = ast.literal_eval(match.group(1))
            loan_id = context.get('loan_id')
            if loan_id:
                from apps.loans.models import Loan
                return Loan.objects.get(id=loan_id)
        except (ValueError, SyntaxError, Loan.DoesNotExist):
            pass
    return None

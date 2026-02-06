"""
Permission mixins for Loans app.
Ensures proper access control for loan-related views.
"""

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db import models

from .models import Loan, LoanReview


class LoanParticipantMixin(UserPassesTestMixin):
    """
    Mixin that ensures the user is a participant in the loan.
    """

    def get_loan(self):
        """Get the loan object from URL parameters."""
        if not hasattr(self, 'loan'):
            loan_id = self.kwargs.get('pk') or self.kwargs.get('loan_id')
            if loan_id:
                self.loan = get_object_or_404(Loan, pk=loan_id)
            else:
                raise Http404("No loan ID provided")
        return self.loan

    def test_func(self):
        """Check if user can view this loan."""
        loan = self.get_loan()
        return loan.can_view(self.request.user)

    def handle_no_permission(self):
        """Handle permission denied."""
        raise PermissionDenied("You don't have permission to view this loan.")


class LenderOnlyMixin(UserPassesTestMixin):
    """
    Mixin that ensures the user is the lender.
    """

    def get_loan(self):
        """Get the loan object from URL parameters."""
        if not hasattr(self, 'loan'):
            loan_id = self.kwargs.get('pk') or self.kwargs.get('loan_id')
            if loan_id:
                self.loan = get_object_or_404(Loan, pk=loan_id)
            else:
                raise Http404("No loan ID provided")
        return self.loan

    def test_func(self):
        """Check if user is the lender."""
        loan = self.get_loan()
        return loan.lender == self.request.user

    def handle_no_permission(self):
        """Handle permission denied."""
        raise PermissionDenied("Only the lender can perform this action.")


class BorrowerOnlyMixin(UserPassesTestMixin):
    """
    Mixin that ensures the user is the borrower.
    """

    def get_loan(self):
        """Get the loan object from URL parameters."""
        if not hasattr(self, 'loan'):
            loan_id = self.kwargs.get('pk') or self.kwargs.get('loan_id')
            if loan_id:
                self.loan = get_object_or_404(Loan, pk=loan_id)
            else:
                raise Http404("No loan ID provided")
        return self.loan

    def test_func(self):
        """Check if user is the borrower."""
        loan = self.get_loan()
        return loan.borrower == self.request.user

    def handle_no_permission(self):
        """Handle permission denied."""
        raise PermissionDenied("Only the borrower can perform this action.")


class LoanReviewMixin(UserPassesTestMixin):
    """
    Mixin that ensures the user can review the loan.
    """

    def get_loan(self):
        """Get the loan object from URL parameters."""
        if not hasattr(self, 'loan'):
            loan_id = self.kwargs.get('pk') or self.kwargs.get('loan_id')
            if loan_id:
                self.loan = get_object_or_404(Loan, pk=loan_id)
            else:
                raise Http404("No loan ID provided")
        return self.loan

    def test_func(self):
        """Check if user can review this loan."""
        loan = self.get_loan()
        
        # Must be a participant
        if not (loan.borrower == self.request.user or loan.lender == self.request.user):
            return False
        
        # Loan must be completed
        if loan.status != 'returned':
            return False
        
        # Must not have already reviewed
        return not LoanReview.objects.filter(loan=loan, reviewer=self.request.user).exists()

    def handle_no_permission(self):
        """Handle permission denied."""
        raise PermissionDenied("You cannot review this loan.")


def get_visible_loans(user, group=None):
    """
    Get loans visible to user based on privacy settings.
    Used in views and templates.
    """
    # Base queryset - always include user's own loans
    base_queryset = Loan.objects.filter(
        models.Q(borrower=user) | models.Q(lender=user)
    )
    
    if group:
        # Add group-based visibility
        if group.loan_visibility == "public":
            # All group members can see group loans
            base_queryset |= Loan.objects.filter(group=group)
        elif group.loan_visibility == "admin_only" and group.is_admin(user):
            # Only admins can see group loans
            base_queryset |= Loan.objects.filter(group=group)
        elif group.loan_visibility == "hidden":
            # Only participants (already included above)
            pass
    
    return base_queryset.distinct()


def can_view_loan(user, loan):
    """
    Helper function to check if user can view a specific loan.
    """
    return loan.can_view(user)


def can_manage_loan(user, loan, action):
    """
    Helper function to check if user can perform specific actions on a loan.
    
    Actions: 'approve', 'reject', 'return', 'cancel', 'extend', 'review'
    """
    if action in ['approve', 'reject']:
        return loan.lender == user and loan.status == 'requested'
    elif action == 'return':
        return loan.borrower == user and loan.status in ['approved', 'active']
    elif action == 'cancel':
        return loan.borrower == user and loan.status == 'requested'
    elif action == 'extend':
        return loan.borrower == user and loan.status in ['approved', 'active']
    elif action == 'review':
        return (
            (loan.borrower == user or loan.lender == user) 
            and loan.status == 'returned'
            and not LoanReview.objects.filter(loan=loan, reviewer=user).exists()
        )
    
    return False
"""
Forms for Loans app.
Handles loan requests, reviews, extensions, and management.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from .models import Loan, LoanReview, GroupLoanSettings
from apps.items.models import Item


class LoanRequestForm(forms.ModelForm):
    """
    Form for requesting to borrow an item.
    """
    
    request_message = forms.CharField(
        label=_("Message to lender"),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': _('Introduce yourself and explain why you\'d like to borrow this item...'),
            'maxlength': 1000,
        }),
        max_length=1000,
        required=False,
        help_text=_("Optional message to the item owner")
    )
    
    group = forms.ModelChoiceField(
        label=_("Share via group"),
        queryset=None,  # Will be set in __init__
        required=False,
        help_text=_("Optional: Choose a group you share with the owner")
    )

    class Meta:
        model = Loan
        fields = ['request_message', 'group']

    def __init__(self, user, item, *args, **kwargs):
        self.user = user
        self.item = item
        super().__init__(*args, **kwargs)
        
        # Filter groups to show only groups where both user and item owner are members
        common_groups = item.owner.comuniza_groups.filter(
            members=user
        ).filter(
            members=item.owner
        )
        
        self.fields['group'].queryset = common_groups
        if common_groups.exists():
            self.fields['group'].empty_label = _("No group (direct request)")
        else:
            self.fields['group'].empty_label = _("No common groups available")
            self.fields['group'].help_text = _("You don't share any groups with this owner")

    def clean(self):
        cleaned_data = super().clean()
        
        # Check if user can borrow this item
        if not self.item.can_borrow(self.user):
            raise ValidationError(_("You cannot borrow this item."))
        
        # Check if user already has an active request for this item
        existing_request = Loan.objects.filter(
            item=self.item,
            borrower=self.user,
            status__in=['requested', 'approved', 'active']
        ).exists()
        
        if existing_request:
            raise ValidationError(_("You already have an active loan request for this item."))
        
        return cleaned_data


class LoanReviewForm(forms.ModelForm):
    """
    Form for reviewing a completed loan.
    """
    
    class Meta:
        model = LoanReview
        fields = [
            'rating', 
            'comment', 
            'communication_rating', 
            'reliability_rating', 
            'condition_rating',
            'would_lend_again',
            'is_public'
        ]
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-control'}),
            'communication_rating': forms.Select(attrs={'class': 'form-control'}),
            'reliability_rating': forms.Select(attrs={'class': 'form-control'}),
            'condition_rating': forms.Select(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Share your experience...'),
                'maxlength': 1000,
            }),
            'would_lend_again': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, user, loan, *args, **kwargs):
        self.user = user
        self.loan = loan
        super().__init__(*args, **kwargs)
        
        # Set reviewer role based on user's role in the loan
        if loan.borrower == user:
            self.fields['condition_rating'].label = _("Item condition (received)")
            self.fields['condition_rating'].help_text = _("How was the condition when you received it?")
        else:
            self.fields['condition_rating'].label = _("Item condition (returned)")
            self.fields['condition_rating'].help_text = _("How was the condition when it was returned?")
        
        # Set choices for rating fields
        rating_choices = [(i, f"{i} {'★' * i}") for i in range(1, 6)]
        self.fields['rating'].choices = rating_choices
        self.fields['communication_rating'].choices = rating_choices
        self.fields['reliability_rating'].choices = rating_choices
        self.fields['condition_rating'].choices = rating_choices

    def clean(self):
        cleaned_data = super().clean()
        
        # Note: The view already checks if loan.status is 'returned' and if user hasn't reviewed
        # So we don't need to re-validate here, just ensure rating is provided
        if 'rating' not in self.cleaned_data or not self.cleaned_data.get('rating'):
            raise ValidationError(_("Please provide a rating."))
        
        return cleaned_data


class ExtensionRequestForm(forms.ModelForm):
    """
    Form for requesting a loan extension.
    """
    
    extension_days = forms.IntegerField(
        label=_("Additional days requested"),
        min_value=1,
        max_value=30,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter number of days'),
        }),
        help_text=_("How many additional days do you need?")
    )
    
    extension_reason = forms.CharField(
        label=_("Reason for extension"),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Please explain why you need an extension...'),
            'maxlength': 500,
        }),
        max_length=500,
        required=True,
    )

    class Meta:
        model = Loan
        fields = ['extension_days', 'extension_reason']

    def __init__(self, user, loan, *args, **kwargs):
        self.user = user
        self.loan = loan
        super().__init__(*args, **kwargs)

    def clean_extension_days(self):
        days = self.cleaned_data['extension_days']
        
        # Check if user is the borrower
        if self.loan.borrower != self.user:
            raise ValidationError(_("Only the borrower can request extensions."))
        
        # Check if loan is active or approved
        if self.loan.status not in ['active', 'approved']:
            raise ValidationError(_("Extensions can only be requested for active loans."))
        
        # Check if extension is already requested
        if self.loan.extension_requested:
            raise ValidationError(_("An extension request is already pending."))
        
        # Get user's loan settings for this group
        user_settings = self.user.loan_settings
        group_settings = None
        if self.loan.group:
            group_settings = GroupLoanSettings.objects.filter(
                user=self.user, 
                group=self.loan.group
            ).first()
        
        # Check if extensions are allowed
        if group_settings:
            allow_extensions = group_settings.get_effective_allow_extensions()
            max_days = group_settings.get_effective_max_extension_days()
        else:
            allow_extensions = user_settings.allow_extensions
            max_days = user_settings.max_extension_days
        
        if not allow_extensions:
            raise ValidationError(_("Extensions are not allowed for this loan."))
        
        if days > max_days:
            raise ValidationError(_("Maximum extension days allowed: %(max_days)s.") % {'max_days': max_days})
        
        return days

    def save(self, commit=True):
        # Set the values on the loan instance
        self.loan.extension_days = self.cleaned_data['extension_days']
        self.loan.extension_reason = self.cleaned_data['extension_reason']
        self.loan.request_extension(self.cleaned_data['extension_days'], self.cleaned_data['extension_reason'])
        return self.loan


class LoanActionForm(forms.Form):
    """
    Generic form for loan actions (approve, reject, return).
    """
    
    action = forms.CharField(widget=forms.HiddenInput())
    reason = forms.CharField(
        label=_("Reason"),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Optional reason...'),
            'maxlength': 500,
        }),
        max_length=500,
    )
    
    condition_at_return = forms.CharField(
        label=_("Condition at return"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('e.g., Good condition'),
            'maxlength': 100,
        }),
        max_length=100,
    )

    def __init__(self, user, loan, *args, **kwargs):
        self.user = user
        self.loan = loan
        super().__init__(*args, **kwargs)

    def clean_action(self):
        action = self.cleaned_data['action']
        
        # Validate user can perform this action
        if action == 'approve' and self.loan.lender != self.user:
            raise ValidationError(_("Only the lender can approve loans."))
        
        if action == 'reject' and self.loan.lender != self.user:
            raise ValidationError(_("Only the lender can reject loans."))
        
        if action == 'return' and self.loan.borrower != self.user:
            raise ValidationError(_("Only the borrower can mark items as returned."))

        if action == 'confirm_return' and self.loan.lender != self.user:
            raise ValidationError(_("Only the lender can confirm returns."))

        if action == 'cancel':
            # Both lender and borrower can cancel in different scenarios
            if self.loan.status == 'requested' and self.loan.borrower != self.user:
                raise ValidationError(_("Only the borrower can cancel their own loan request."))
            elif self.loan.status in ['approved', 'active'] and self.loan.lender != self.user:
                raise ValidationError(_("Only the lender can cancel approved loans."))
            elif self.loan.status not in ['requested', 'approved', 'active']:
                raise ValidationError(_("You cannot cancel this loan in its current status."))
        
        return action

    def save(self):
        action = self.cleaned_data['action']
        reason = self.cleaned_data.get('reason', '')
        condition = self.cleaned_data.get('condition_at_return', '')
        
        if action == 'approve':
            self.loan.approve()
        elif action == 'reject':
            self.loan.reject(reason)
        elif action == 'mark_active':
            self.loan.mark_as_active()
        elif action == 'return':
            self.loan.mark_as_returned(condition)
        elif action == 'confirm_return':
            self.loan.confirm_return()
        elif action == 'cancel':
            self.loan.status = 'cancelled'
            self.loan.save()
        
        return self.loan
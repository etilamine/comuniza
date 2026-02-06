"""
Forms for Groups app with enhanced validation.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import Group
from apps.core.validators import (
    EnhancedInputSanitizer,
    validate_group_image,
    validate_enhanced_safe_text,
    validate_enhanced_safe_html
)

User = get_user_model()


class GroupCreateForm(forms.ModelForm):
    """
    Form for creating a new group.
    """

    class Meta:
        model = Group
        fields = [
            'name',
            'description',
            'privacy',
            'city',
            'state',
            'country',
            'image',
            'allow_member_invites',
            'require_approval_for_items',
            'loan_visibility',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add placeholders and help text
        self.fields['name'].widget.attrs['placeholder'] = _('e.g., Berlin Book Sharing, Autonomous Community of the Forest')
        self.fields['description'].widget.attrs['placeholder'] = _('Describe your group\'s purpose, rules, and what members can share...')
        self.fields['description'].widget.attrs['rows'] = 4
        self.fields['city'].widget.attrs['placeholder'] = _('e.g., Neo-Tokyo, New New York, Brighton-By-The-Sea')
        self.fields['state'].widget.attrs['placeholder'] = _('e.g., California, Catalonia, Ontario (optional)')
        self.fields['country'].widget.attrs['placeholder'] = _('e.g., United Brands of America, Eurasia')

        # Make required fields explicit
        self.fields['name'].required = True
        self.fields['city'].required = True
        self.fields['country'].required = True

        # Add help text for important fields
        self.fields['privacy'].help_text = _('Control who can join your group')
        self.fields['loan_visibility'].help_text = _('Control who can see loan activity within the group')
        self.fields['allow_member_invites'].help_text = _('Allow members to invite others to the group')
        self.fields['require_approval_for_items'].help_text = _('Require admin approval for new items shared in the group')

    def clean_name(self):
        """Enhanced group name validation and sanitization."""
        name = self.cleaned_data.get('name')
        if name:
            name = EnhancedInputSanitizer.sanitize_text_input(name, max_length=100)
            if Group.objects.filter(name__iexact=name).exists():
                raise forms.ValidationError(_('A group with this name already exists.'))
        return name
    
    def clean_description(self):
        """Enhanced description validation and sanitization."""
        description = self.cleaned_data.get('description')
        if description:
            # Allow basic HTML formatting in description
            description = EnhancedInputSanitizer.sanitize_text_input(
                description, 
                allow_html=True, 
                max_length=1000
            )
        return description
    
    def clean_image(self):
        """Enhanced group image validation."""
        image = self.cleaned_data.get('image')
        if image:
            validate_group_image(image)
        return image
    
    def clean_city(self):
        """Enhanced city validation and sanitization."""
        city = self.cleaned_data.get('city')
        if city:
            city = EnhancedInputSanitizer.sanitize_text_input(city, max_length=50)
        return city
    
    def clean_state(self):
        """Enhanced state validation and sanitization."""
        state = self.cleaned_data.get('state')
        if state:
            state = EnhancedInputSanitizer.sanitize_text_input(state, max_length=50)
        return state
    
    def clean_country(self):
        """Enhanced country validation and sanitization."""
        country = self.cleaned_data.get('country')
        if country:
            country = EnhancedInputSanitizer.sanitize_text_input(country, max_length=50)
        return country


class GroupInvitationForm(forms.Form):
    """
    Form for inviting users to join a group.
    Accepts both usernames and email addresses.
    """

    recipient = forms.CharField(
        label=_("Username or Email"),
        widget=forms.TextInput(attrs={
            'placeholder': _('Enter username or email address...'),
            'class': 'form-control',
            'autocomplete': 'username',
            'data-autocomplete': 'true'
        })
    )

    recipient_type = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    message = forms.CharField(
        label=_("Personal Message (optional)"),
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': _('Add a personal message to your invitation...'),
            'class': 'form-control'
        })
    )

    def __init__(self, group, *args, **kwargs):
        self.group = group
        super().__init__(*args, **kwargs)

    def clean_recipient(self):
        """Validate the recipient (username or email) and check for existing invitations."""
        recipient = self.cleaned_data['recipient'].strip()

        if not recipient:
            raise forms.ValidationError(_("Please enter a username or email address."))

        # Try to find user by username first
        try:
            user = User.objects.get(username__iexact=recipient)
            self.cleaned_data['recipient_type'] = 'user'
            self.cleaned_data['user'] = user
            self.cleaned_data['email'] = user.email

            # Check if user is already a member
            if self.group.members.filter(id=user.id).exists():
                raise forms.ValidationError(_("This user is already a member of the group."))

            # Check if there's already a pending invitation
            if self.group.invitations.filter(email=user.email, status='pending').exists():
                raise forms.ValidationError(_("This user has already been invited to the group."))

        except User.DoesNotExist:
            # Not a username, treat as email
            if '@' not in recipient:
                raise forms.ValidationError(_("Please enter a valid username or email address."))

            # Validate email format
            email_field = forms.EmailField()
            try:
                email = email_field.clean(recipient)
            except forms.ValidationError:
                raise forms.ValidationError(_("Please enter a valid email address."))

            self.cleaned_data['recipient_type'] = 'email'
            self.cleaned_data['email'] = email
            self.cleaned_data['user'] = None

            # Check if user with this email is already a member
            if self.group.members.filter(email=email).exists():
                raise forms.ValidationError(_("A user with this email is already a member of the group."))

            # Check if there's already a pending invitation
            if self.group.invitations.filter(email=email, status='pending').exists():
                raise forms.ValidationError(_("This email address has already been invited to the group."))

        return recipient

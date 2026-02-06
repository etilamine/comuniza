from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import User
from .utils.username_generator import UsernameGenerator
from apps.core.validators import (
    EnhancedInputSanitizer,
    validate_avatar_image,
    validate_enhanced_safe_text,
    validate_enhanced_email
)

class CustomUserCreationForm(UserCreationForm):
    """
    Enhanced signup form with privacy-first username generation.
    """

    username = forms.CharField(
        label="Username",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Generate one below or create your own'
        }),
        help_text="Your public identifier. We'll generate a random one if you leave this blank."
    )

    generate_username = forms.BooleanField(
        required=False,
        label="Generate random username",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        initial=True
    )

    privacy_agreement = forms.BooleanField(
        required=True,
        label="I agree to the privacy policy",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Your email and personal information will never be shared publicly."
    )

    @property
    def by_passkey(self):
        """Check if this signup is using passkey authentication."""
        return self.data.get('passkey') == 'true' or getattr(self, '_by_passkey', False)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'phone', 'password1', 'password2')
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 555-123-4567 (optional)',
                'type': 'tel'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-generate username suggestions
        self.username_suggestions = UsernameGenerator.generate_multiple_usernames(5)

        # Handle passkey authentication
        if self.by_passkey:
            # Make password fields optional when using passkeys
            self.fields['password1'].required = False
            self.fields['password2'].required = False

    def clean_username(self):
        username = self.cleaned_data.get('username')
        generate_random = self.data.get('generate_username') == 'on'

        if not username and not generate_random:
            raise ValidationError("Please provide a username or check 'Generate random username'.")

        if username and (len(username) < 5 or len(username) > 50):
            raise ValidationError("Username must be 5-50 characters.")

        if username:
            # Check uniqueness
            if User.objects.filter(username=username).exists():
                raise ValidationError("This username is already taken.")

        return username

    def clean(self):
        cleaned_data = super().clean()
        generate_random = self.data.get('generate_username') == 'on'
        username = cleaned_data.get('username')

        # If generate_random is checked and no username provided, we'll handle it in save
        if generate_random and not username:
            cleaned_data['generate_random_username'] = True

        # For passkey authentication, skip password validation
        if self.by_passkey:
            # Remove password validation errors if using passkeys
            if self.errors and 'password1' in self.errors:
                del self.errors['password1']
            if self.errors and 'password2' in self.errors:
                del self.errors['password2']
            # Clear password data
            cleaned_data['password1'] = ''
            cleaned_data['password2'] = ''

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # Handle username generation
        if self.cleaned_data.get('generate_random_username'):
            existing_usernames = list(User.objects.values_list('username', flat=True))
            user.username = UsernameGenerator.generate_username(existing_usernames)

        # For passkey authentication, set unusable password
        if self.by_passkey:
            user.set_unusable_password()

        if commit:
            user.save()
        return user

    def try_save(self, request):
        """
        Method required by allauth for signup forms.
        Returns (user, response) tuple.
        """
        user = self.save()
        # Set by_passkey attribute for allauth compatibility
        user.by_passkey = self.by_passkey
        return (user, None)

class CustomUserChangeForm(UserChangeForm):
    """
    Enhanced user change form with privacy controls.
    """

    current_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Required to change sensitive information"
    )

    new_username = forms.CharField(
        label="New Username",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new username'
        }),
        help_text="Leave blank to keep current username"
    )

    # Notification Settings (handled separately from User model)
    email_notifications = forms.BooleanField(
        label="Email notifications for loans",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Receive email notifications for loan requests, approvals, and updates"
    )

    message_notifications = forms.BooleanField(
        label="Email notifications for messages",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Receive email notifications for new private messages"
    )

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'phone',
                  'avatar', 'profile_visibility', 'email_visibility', 'activity_visibility')
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 555-123-4567',
                'type': 'tel'
            }),
            'profile_visibility': forms.Select(attrs={'class': 'form-control'}),
            'email_visibility': forms.Select(attrs={'class': 'form-control'}),
            'activity_visibility': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove password field from default form
        if 'password' in self.fields:
            del self.fields['password']

    def clean_avatar(self):
        """Enhanced avatar validation."""
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            validate_avatar_image(avatar)
        return avatar
    
    def clean_first_name(self):
        """Enhanced first name validation and sanitization."""
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            first_name = EnhancedInputSanitizer.sanitize_text_input(first_name, max_length=50)
        return first_name
    
    def clean_last_name(self):
        """Enhanced last name validation and sanitization."""
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            last_name = EnhancedInputSanitizer.sanitize_text_input(last_name, max_length=50)
        return last_name
    
    def clean_new_username(self):
        new_username = self.cleaned_data.get('new_username')
        if new_username:
            if len(new_username) < 5 or len(new_username) > 50:
                raise ValidationError("Username must be 5-50 characters.")
            if User.objects.filter(username=new_username).exclude(pk=self.instance.pk).exists():
                raise ValidationError("This username is already taken.")
        return new_username

    def clean(self):
        cleaned_data = super().clean()
        new_username = cleaned_data.get('new_username')
        current_password = cleaned_data.get('current_password')

        # If changing sensitive info, require current password
        sensitive_fields = ['email', 'phone', 'new_username']
        changing_sensitive = any(cleaned_data.get(field) != getattr(self.instance, field, None)
                                for field in sensitive_fields if field in cleaned_data)

        if changing_sensitive and not current_password:
            raise ValidationError("Current password is required to change sensitive information.")

        if changing_sensitive and not self.instance.check_password(current_password):
            raise ValidationError("Current password is incorrect.")

        # For username changes, require email confirmation
        if new_username and new_username != self.instance.username:
            cleaned_data['username_change_pending'] = True

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # Handle username change with email confirmation
        new_username = self.cleaned_data.get('new_username')
        if new_username:
            # Don't change username yet - this will be handled by the view
            # after sending confirmation email
            user._pending_username = new_username

        if commit:
            user.save()
        return user

"""
Forms for Messaging app.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Message, Conversation


class MessageForm(forms.ModelForm):
    """
    Form for sending messages.
    """

    content = forms.CharField(
        label=_("Message"),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Type your message here...'),
            'maxlength': 2000,
        }),
        max_length=2000,
        required=True,
    )

    class Meta:
        model = Message
        fields = ['content']


class ConversationForm(forms.Form):
    """
    Form for starting a new conversation.
    """

    subject = forms.CharField(
        label=_("Subject"),
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Optional conversation subject'),
        }),
    )

    initial_message = forms.CharField(
        label=_("Initial Message"),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': _('Send your first message...'),
            'maxlength': 2000,
        }),
        max_length=2000,
        required=True,
    )
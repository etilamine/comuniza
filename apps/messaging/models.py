"""
Messaging models for Comuniza.
End-to-end encrypted private messaging between users.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.encryption import ConversationE2EEManager
from apps.core.validators import sanitized_text, no_profanity


class Conversation(models.Model):
    """
    A conversation between two users.
    Messages are encrypted end-to-end using a shared conversation key.
    """

    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ConversationParticipant',
        related_name='conversations',
        verbose_name=_('participants'),
    )

    # Conversation metadata
    subject = models.CharField(
        _('subject'),
        max_length=200,
        blank=True,
        null=True,
        validators=[sanitized_text, no_profanity],
        help_text=_('Optional conversation subject')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    is_active = models.BooleanField(_('active'), default=True)

    # Encryption salt for E2EE
    encryption_salt = models.CharField(
        _('encryption salt'),
        max_length=100,
        blank=True,
        help_text=_('Salt used for end-to-end encryption key derivation')
    )

    # Context - what this conversation is about
    related_item = models.ForeignKey(
        'items.Item',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        verbose_name=_('related item'),
        help_text=_('Item this conversation is about (if applicable)')
    )
    related_loan = models.ForeignKey(
        'loans.Loan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        verbose_name=_('related loan'),
        help_text=_('Loan this conversation is about (if applicable)')
    )

    class Meta:
        db_table = 'conversations'
        verbose_name = _('conversation')
        verbose_name_plural = _('conversations')
        ordering = ['-updated_at']

    def save(self, *args, **kwargs):
        """Generate encryption salt if not already set."""
        if not self.encryption_salt:
            self.encryption_salt = ConversationE2EEManager.generate_salt()
        super().save(*args, **kwargs)

    def __str__(self):
        participants = list(self.participants.values_list('username', flat=True))
        return f"Conversation between {', '.join(participants)}"

    def get_other_participant(self, user):
        """Get the other participant in this conversation."""
        return self.participants.exclude(pk=user.pk).first()

    def get_latest_message(self):
        """Get the most recent message in this conversation."""
        return self.messages.order_by('-created_at').first()

    def mark_as_read(self, user):
        """Mark all messages as read for a user."""
        self.messages.filter(sender=user).update(is_read=True)

    def has_loan_context(self):
        """Check if this conversation has loan context."""
        return self.related_loan is not None

    def unread_count(self):
        """Get total unread messages in this conversation."""
        return self.messages.filter(is_read=False).count()


class ConversationParticipant(models.Model):
    """
    Through model for conversation participants with additional fields.
    """

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='participant_details',
        verbose_name=_('conversation'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversation_participations',
        verbose_name=_('user'),
    )

    # Participation metadata
    joined_at = models.DateTimeField(_('joined at'), auto_now_add=True)
    is_active = models.BooleanField(_('active'), default=True)
    last_read_at = models.DateTimeField(_('last read at'), null=True, blank=True)

    class Meta:
        db_table = 'conversation_participants'
        verbose_name = _('conversation participant')
        verbose_name_plural = _('conversation participants')
        unique_together = [['conversation', 'user']]
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.username} in {self.conversation}"

    def get_unread_count(self):
        """Get number of unread messages for this participant."""
        if not self.last_read_at:
            return self.conversation.messages.count()
        return self.conversation.messages.filter(created_at__gt=self.last_read_at).count()


class Message(models.Model):
    """
    An end-to-end encrypted message in a conversation.
    Both participants can decrypt all messages using the shared conversation key.
    """

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('conversation'),
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name=_('sender'),
    )

    # Encrypted content
    encrypted_content = models.TextField(_('encrypted content'))

    # Message metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    is_read = models.BooleanField(_('read'), default=False)
    read_at = models.DateTimeField(_('read at'), null=True, blank=True)

    # Message type
    MESSAGE_TYPES = [
        ('text', _('Text Message')),
        ('system', _('System Message')),
    ]
    message_type = models.CharField(
        _('message type'),
        max_length=20,
        choices=MESSAGE_TYPES,
        default='text'
    )

    class Meta:
        db_table = 'messages'
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
        ]

    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"

    def encrypt_content(self, content: str):
        """
        Encrypt message content using the conversation's E2EE key.
        Both participants in the conversation can decrypt this.
        """
        self.encrypted_content = ConversationE2EEManager.encrypt_message(
            content,
            self.conversation_id,
            self.conversation.encryption_salt
        )

    def decrypt_content(self) -> str:
        """
        Decrypt message content using the conversation's E2EE key.
        Any participant in the conversation can decrypt this.
        """
        return ConversationE2EEManager.decrypt_message(
            self.encrypted_content,
            self.conversation_id,
            self.conversation.encryption_salt
        )

    def mark_as_read(self):
        """Mark message as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = models.functions.Now()
            self.save(update_fields=['is_read', 'read_at'])

    def has_loan_context(self):
        """Check if this message's conversation has loan context."""
        return self.conversation.related_loan is not None

    def is_unread(self):
        """Check if message is unread."""
        return not self.is_read


class MessageAttachment(models.Model):
    """
    Attachments for messages (images, files).
    Note: Attachments are not encrypted - users should be cautious.
    """

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_('message'),
    )

    # File information
    file = models.FileField(_('file'), upload_to='message_attachments/')
    filename = models.CharField(_('filename'), max_length=255)
    file_size = models.PositiveIntegerField(_('file size'))
    content_type = models.CharField(_('content type'), max_length=100)

    # Metadata
    uploaded_at = models.DateTimeField(_('uploaded at'), auto_now_add=True)

    class Meta:
        db_table = 'message_attachments'
        verbose_name = _('message attachment')
        verbose_name_plural = _('message attachments')
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Attachment {self.filename} for message {self.message.id}"
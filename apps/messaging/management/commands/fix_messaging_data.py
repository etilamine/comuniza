"""
Management command to fix messaging data integrity issues.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.messaging.models import Conversation, ConversationParticipant, Message
from apps.users.models import User


class Command(BaseCommand):
    help = 'Fix messaging data integrity issues'

    def handle(self, *args, **options):
        self.stdout.write('Checking messaging data integrity...')
        
        # Fix conversations without participants
        conversations_fixed = 0
        for conversation in Conversation.objects.all():
            participants_count = conversation.participants.count()
            if participants_count == 0:
                self.stdout.write(f'Deleting conversation {conversation.id} with no participants')
                conversation.delete()
                conversations_fixed += 1
            elif participants_count == 1:
                # Conversation with only one participant - might be an error
                self.stdout.write(f'Warning: Conversation {conversation.id} has only one participant')
        
        self.stdout.write(f'Fixed {conversations_fixed} conversations')
        
        # Ensure ConversationParticipant records exist for all participants
        participants_fixed = 0
        for conversation in Conversation.objects.all():
            for user in conversation.participants.all():
                participant, created = ConversationParticipant.objects.get_or_create(
                    conversation=conversation,
                    user=user,
                    defaults={'is_active': True}
                )
                if created:
                    participants_fixed += 1
                    self.stdout.write(f'Created missing ConversationParticipant for conversation {conversation.id}, user {user.username}')
        
        self.stdout.write(f'Created {participants_fixed} missing ConversationParticipant records')
        
        # Fix conversations with missing encryption salt
        salts_fixed = 0
        import os
        import base64
        for conversation in Conversation.objects.filter(encryption_salt=''):
            salt = base64.b64encode(os.urandom(16)).decode()
            conversation.encryption_salt = salt
            conversation.save()
            salts_fixed += 1
        
        self.stdout.write(f'Fixed {salts_fixed} conversations with missing encryption salt')
        
        # Check for orphaned messages
        orphaned_messages = Message.objects.filter(
            conversation__isnull=True
        ).count()
        
        if orphaned_messages > 0:
            self.stdout.write(f'Warning: Found {orphaned_messages} orphaned messages')
        
        self.stdout.write('Messaging data integrity check complete.')

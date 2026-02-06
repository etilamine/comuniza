"""
Services for Loans app.
Handles business logic, messaging integration, and loan operations.
"""

import re

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from apps.core.encryption import UserDerivedKeyManager
from apps.messaging.models import Conversation, ConversationParticipant, Message


User = get_user_model()


class LoanService:
    """
    Service class for loan-related operations and messaging integration.
    """
    
    @staticmethod
    def create_loan_conversation(loan):
        """
        Create or get conversation for loan communication.
        """
        subject = f"Loan: {loan.item.title}"
        
        # Check if conversation already exists between borrower and lender
        existing_conversation = Conversation.objects.filter(
            participants=loan.borrower
        ).filter(
            participants=loan.lender
        ).annotate(
            num_participants=models.Count('participants')
        ).filter(num_participants=2).first()
        
        if existing_conversation:
            return existing_conversation
        
        # Create new conversation
        conversation = Conversation.objects.create(subject=subject)
        
        # Add participants
        ConversationParticipant.objects.create(conversation=conversation, user=loan.borrower)
        ConversationParticipant.objects.create(conversation=conversation, user=loan.lender)
        
        # Send initial message about loan request
        if loan.status == 'requested':
            LoanService._send_loan_system_message(
                conversation, 
                loan, 
                f"Loan requested: {loan.item.title}",
                loan.borrower
            )
        
        return conversation
    
    @staticmethod
    def send_loan_status_message(loan, status, sender=None):
        """
        Send automated message about loan status change.
        """
        if not sender:
            sender = loan.lender
        
        conversation = LoanService.create_loan_conversation(loan)
        
        status_messages = {
            'approved': f"Loan approved for {loan.item.title}",
            'rejected': f"Loan request for {loan.item.title} was rejected",
            'active': f"Loan for {loan.item.title} is now active",
            'returned': f"Loan for {loan.item.title} has been returned",
            'cancelled': f"Loan for {loan.item.title} was cancelled",
            'overdue': f"Loan for {loan.item.title} is overdue",
        }
        
        message = status_messages.get(status, f"Loan status changed to: {status}")
        
        LoanService._send_loan_system_message(
            conversation,
            loan,
            message,
            sender
        )
    
    @staticmethod
    def send_extension_request_message(loan):
        """
        Send message about extension request.
        """
        conversation = LoanService.create_loan_conversation(loan)
        
        message = f"Extension request: {loan.extension_days} additional days for {loan.item.title}. Reason: {loan.extension_reason}"
        
        LoanService._send_loan_system_message(
            conversation,
            loan,
            message,
            loan.borrower
        )
    
    @staticmethod
    def send_extension_approval_message(loan):
        """
        Send message about extension approval.
        """
        conversation = LoanService.create_loan_conversation(loan)
        
        message = f"Extension approved: Loan for {loan.item.title} extended by {loan.extension_days} days. New due date: {loan.due_date}"
        
        LoanService._send_loan_system_message(
            conversation,
            loan,
            message,
            loan.lender
        )
    
    @staticmethod
    def _send_loan_system_message(conversation, loan, content, sender):
        """
        Helper method to send system message with loan context.
        """
        # Create message with loan context
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            message_type='system'
        )
        
        # Add loan context to message content
        loan_context = {
            'loan_id': loan.id,
            'item_title': loan.item.title,
            'item_slug': loan.item.slug,
            'action_required': loan.status in ['requested', 'approved']
        }
        
        full_content = f"{content}\n\n[LOAN_CONTEXT:{loan_context}]"
        
        # Encrypt message using sender's derived key (consistent with messaging app)
        message.encrypt_content(full_content)
        message.save()
        
        return message
    
    @staticmethod
    def get_loan_conversations(user):
        """
        Get all conversations that have loan-related messages for a user.
        """
        user_conversations = user.conversations.all()
        loan_conversations = []
        
        for conversation in user_conversations:
            # Check if conversation has any loan-related messages
            messages_with_loan = conversation.messages.filter(
                message_type='system'
            ).filter(
                encrypted_content__contains='LOAN_CONTEXT:'
            ).exists()
            
            if messages_with_loan:
                loan_conversations.append(conversation)
        
        return loan_conversations
    
    @staticmethod
    def extract_loan_context(message_content):
        """
        Extract loan context from message content.
        """
        import re
        
        match = re.search(r'\[LOAN_CONTEXT:\{.*?\}\]', message_content)
        if match:
            try:
                # Simple parsing - in production, use ast.literal_eval safely
                context_str = match.group().replace('[LOAN_CONTEXT:', '').replace('}', '')
                # This is simplified - proper parsing needed in production
                return {
                    'has_loan_context': True,
                    'raw_context': context_str
                }
            except (ValueError, KeyError, AttributeError, re.error):
                pass
        
        return {'has_loan_context': False}
    
    @staticmethod
    def get_actionable_loans(user):
        """
        Get loans that require user action.
        """
        actionable_loans = []
        
        # Loans pending approval (for lenders)
        pending_approvals = Loan.objects.filter(
            lender=user,
            status='requested'
        ).select_related('item', 'borrower')
        
        # Loans that can be returned (for borrowers)
        returnable = Loan.objects.filter(
            borrower=user,
            status__in=['approved', 'active']
        ).select_related('item', 'lender')
        
        # Loans awaiting return confirmation (for lenders)
        awaiting_return = Loan.objects.filter(
            lender=user,
            status='returned'
        ).select_related('item', 'borrower')
        
        actionable_loans.extend(pending_approvals)
        actionable_loans.extend(returnable)
        actionable_loans.extend(awaiting_return)
        
        return actionable_loans


class LoanSettingsService:
    """
    Service for managing user and group loan settings.
    """
    
    @staticmethod
    def get_or_create_user_settings(user):
        """
        Get or create user loan settings.
        """
        settings, created = UserLoanSettings.objects.get_or_create(user=user)
        return settings
    
    @staticmethod
    def get_effective_settings(user, group=None):
        """
        Get effective loan settings for a user in a group context.
        """
        # Get global settings
        user_settings = LoanSettingsService.get_or_create_user_settings(user)
        
        if not group:
            return {
                'loan_days': user_settings.default_loan_days,
                'allow_extensions': user_settings.allow_extensions,
                'require_approval': user_settings.require_approval_for_extensions,
                'max_extension_days': user_settings.max_extension_days,
                'privacy': user_settings.default_loan_privacy,
            }
        
        # Check for group-specific overrides
        group_settings, created = GroupLoanSettings.objects.get_or_create(
            user=user,
            group=group
        )
        
        return {
            'loan_days': group_settings.get_effective_loan_days(),
            'allow_extensions': group_settings.get_effective_allow_extensions(),
            'require_approval': group_settings.get_effective_require_approval(),
            'max_extension_days': group_settings.get_effective_max_extension_days(),
            'privacy': group_settings.get_effective_privacy(),
        }
    
    @staticmethod
    def apply_loan_settings(loan, user, group=None):
        """
        Apply user's loan settings to a loan.
        """
        settings = LoanSettingsService.get_effective_settings(user, group)
        
        loan.privacy = settings['privacy']
        
        # For future use when we implement custom loan durations
        # loan.loan_days = settings['loan_days']
        
        return loan
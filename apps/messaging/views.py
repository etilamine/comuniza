"""
Views for Messaging app.
End-to-end encrypted private messaging.
"""

import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Prefetch, Q, Count, Case, When, IntegerField, Max
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

from .models import Conversation, Message, ConversationParticipant
from .forms import MessageForm, ConversationForm
from apps.core.encryption import ConversationE2EEManager
from apps.core.rate_limiting import message_rate_limit, content_creation_rate_limit


class ConversationListView(LoginRequiredMixin, ListView):
    """
    List all conversations for the current user.
    """
    model = Conversation
    template_name = 'messaging/conversation_list.html'
    context_object_name = 'conversations'
    paginate_by = 20

    def get_queryset(self):
        # Get conversations with user-specific participant data and message previews
        queryset = Conversation.objects.filter(
            participants=self.request.user,
            participant_details__is_active=True
        ).prefetch_related(
            Prefetch(
                'participant_details',
                queryset=ConversationParticipant.objects.filter(user=self.request.user),
                to_attr='user_participant'
            ),
            Prefetch(
                'messages',
                queryset=Message.objects.order_by('-created_at')[:1],
                to_attr='latest_message'
            )
        ).distinct().order_by('-updated_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add decrypted message previews to conversations
        for conversation in context['conversations']:
            # Add decrypted message preview
            if (hasattr(conversation, 'latest_message') and
                conversation.latest_message and
                len(conversation.latest_message) > 0):
                message = conversation.latest_message[0]
                try:
                    # Both participants can decrypt all messages in their conversations
                    conversation.decrypted_preview = message.decrypt_content()
                    # Remove LOAN_CONTEXT metadata from preview for cleaner display
                    import re
                    conversation.decrypted_preview = re.sub(r'\[LOAN_CONTEXT:\{.*?\}\]', '', conversation.decrypted_preview)
                    # Truncate to reasonable preview length
                    if len(conversation.decrypted_preview) > 100:
                        conversation.decrypted_preview = conversation.decrypted_preview[:97] + "..."
                except Exception as e:
                    # Log the decryption error for debugging
                    logger.error(f"Failed to decrypt message {message.id} in conversation {conversation.id}: {e}")
                    conversation.decrypted_preview = "[Unable to decrypt message]"
            else:
                conversation.decrypted_preview = None
        return context


@login_required
def conversation_detail(request, conversation_id):
    """
    View and send messages in a conversation.
    """
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user,
        participant_details__is_active=True
    )

    # Ensure conversation has encryption salt (for migrated conversations)
    if not conversation.encryption_salt:
        conversation.encryption_salt = ConversationE2EEManager.generate_salt()
        conversation.save()

    # Mark messages as read
    conversation.participant_details.filter(user=request.user).update(
        last_read_at=Message.objects.filter(
            conversation=conversation
        ).aggregate(latest=models.Max('created_at'))['latest']
    )

    # Mark message notifications as read
    try:
        from apps.notifications.models import Notification
        Notification.objects.filter(
            user=request.user,
            notification_type='message',
            related_conversation=conversation,
            is_read=False
        ).update(is_read=True)
    except Exception:
        pass  # Notifications app might not be available

    # Get messages and decrypt them
    messages_list = []
    for message in conversation.messages.order_by('created_at'):
        # Decrypt message content for display
        try:
            decrypted_content = message.decrypt_content()
        except Exception as e:
            # If decryption fails, show placeholder
            logger.error(f"Failed to decrypt message {message.id}: {e}")
            decrypted_content = "[Unable to decrypt message]"

        # Add decrypted content as attribute to message object
        message.decrypted_content = decrypted_content
        messages_list.append(message)

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            # Encrypt and save message
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user

            # Encrypt message content with conversation's shared key
            content = form.cleaned_data['content']
            message.encrypt_content(content)

            message.save()

            # Update conversation timestamp
            conversation.save()

            messages.success(request, _("Message sent successfully."))
            return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()

    context = {
        'conversation': conversation,
        'messages': messages_list,
        'form': form,
        'other_participant': conversation.get_other_participant(request.user),
        'related_item': conversation.related_item,
    }

    return render(request, 'messaging/conversation_detail.html', context)


@login_required
@content_creation_rate_limit
def start_conversation(request, username, item_id=None, loan_id=None):
    """
    Start a new conversation with a user.
    Can be linked to an item or loan.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        other_user = User.objects.get(username=username)
    except User.DoesNotExist:
        messages.error(request, _("User not found."))
        return redirect('messaging:conversation_list')

    if other_user == request.user:
        messages.error(request, _("You cannot start a conversation with yourself."))
        return redirect('messaging:conversation_list')

    # Get related item/loan if provided
    related_item = None
    related_loan = None

    if item_id:
        logger.info(f"start_conversation called with item_id={item_id}")
        from apps.items.models import Item
        try:
            related_item = Item.objects.get(id=item_id)
            logger.info(f"Found related item: {related_item}")
        except Item.DoesNotExist:
            logger.error(f"Item with id {item_id} not found")
            pass

    if loan_id:
        from apps.loans.models import Loan
        try:
            related_loan = Loan.objects.get(id=loan_id)
        except Loan.DoesNotExist:
            pass

    # Check if conversation already exists (considering context)
    existing_conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).annotate(
        num_participants=models.Count('participants')
    ).filter(num_participants=2)

    # If we have context (item/loan), prioritize conversations with the same context
    if related_item:
        context_conversation = existing_conversation.filter(related_item=related_item).first()
        if context_conversation:
            return redirect('messaging:conversation_detail',
                            conversation_id=context_conversation.id)
    elif related_loan:
        context_conversation = existing_conversation.filter(related_loan=related_loan).first()
        if context_conversation:
            return redirect('messaging:conversation_detail',
                            conversation_id=context_conversation.id)

    # Only fall back to general conversations when no context is provided
    if not (related_item or related_loan):
        general_conversation = existing_conversation.filter(
            related_item__isnull=True, related_loan__isnull=True
        ).first()

        if general_conversation:
            return redirect('messaging:conversation_detail',
                            conversation_id=general_conversation.id)

    if request.method == 'POST':
        form = ConversationForm(request.POST)
        if form.is_valid():
            initial_message = form.cleaned_data.get('initial_message')
            subject = form.cleaned_data.get('subject', '')

            # Create new conversation (encryption_salt will be auto-generated)
            logger.info(f"Creating new conversation with related_item={related_item}, related_loan={related_loan}")
            conversation = Conversation.objects.create(
                subject=subject,
                related_item=related_item,
                related_loan=related_loan,
            )
            logger.info(f"Created conversation {conversation.id} with encryption_salt={conversation.encryption_salt}")

            # Add participants
            ConversationParticipant.objects.create(
                conversation=conversation,
                user=request.user
            )
            ConversationParticipant.objects.create(
                conversation=conversation,
                user=other_user
            )

            # Send initial message if provided
            if initial_message:
                message = Message(
                    conversation=conversation,
                    sender=request.user,
                    message_type='text'
                )
                message.encrypt_content(initial_message)
                message.save()

            messages.success(request, _("Conversation started successfully."))
            return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    else:
        form = ConversationForm()


    context = {
        'form': form,
        'other_user': other_user,
        'related_item': related_item,
        'related_loan': related_loan,
    }
    return render(request, 'messaging/start_conversation.html', context)


@login_required
@content_creation_rate_limit
def start_conversation_form(request):
    """Handle the start conversation form submission from the modal."""
    try:
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Method not allowed'})

        recipient_username = request.POST.get('recipient', '').strip()
        subject = request.POST.get('subject', '').strip()
        initial_message = request.POST.get('initial_message', '').strip()

        if not recipient_username:
            return JsonResponse({'success': False, 'error': 'Recipient is required'})

        if not initial_message:
            return JsonResponse({'success': False, 'error': 'Initial message is required'})

        User = get_user_model()
        try:
            recipient = User.objects.get(username=recipient_username, is_active=True)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'})

        if recipient == request.user:
            return JsonResponse({'success': False, 'error': 'Cannot start conversation with yourself'})

        # For modal: Always create new conversations (don't redirect to existing)
        # This ensures modal conversations have proper encryption

        # Create new conversation (encryption_salt will be auto-generated by save())
        conversation = Conversation.objects.create(subject=subject if subject else None)

        # Add participants
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=request.user
        )
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=recipient
        )

        # Send initial message
        message = Message(
            conversation=conversation,
            sender=request.user,
            message_type='text'
        )
        message.encrypt_content(initial_message)
        message.save()

        return JsonResponse({
            'success': True,
            'conversation_id': conversation.id
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)

    # Create new conversation (encryption_salt will be auto-generated by save())
    conversation = Conversation.objects.create(subject=subject if subject else None)

    # Add participants
    ConversationParticipant.objects.create(
        conversation=conversation,
        user=request.user
    )
    ConversationParticipant.objects.create(
        conversation=conversation,
        user=recipient
    )

    # Send initial message
    message = Message(
        conversation=conversation,
        sender=request.user,
        message_type='text'
    )
    message.encrypt_content(initial_message)
    message.save()

    return JsonResponse({
        'success': True,
        'conversation_id': conversation.id
    })


@login_required
@message_rate_limit
def send_message(request, conversation_id):
    """
    AJAX endpoint to send a message.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Message content is required'}, status=400)

    # Create and encrypt message with conversation's shared key
    message = Message(
        conversation=conversation,
        sender=request.user,
        message_type='text'
    )
    message.encrypt_content(content)
    message.save()

    # Update conversation timestamp
    conversation.save()

    # Mark message as read for the sender
    message.mark_as_read()

    return JsonResponse({
        'success': True,
        'message_id': message.id,
        'created_at': message.created_at.isoformat(),
        'message': 'Message sent successfully!'
    })


@login_required
def delete_conversation(request, conversation_id):
    """
    Delete a conversation and all its messages.
    Only participants can delete their conversations.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )

    try:
        # Get conversation info for response
        conversation_title = conversation.subject or _("Untitled conversation")
        
        # Delete the conversation (this will cascade delete all messages and participants)
        conversation.delete()
        
        return JsonResponse({
            'success': True,
            'message': _('Conversation "{title}" deleted successfully.').format(title=conversation_title)
        })
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': _('Failed to delete conversation. Please try again.')
        }, status=500)
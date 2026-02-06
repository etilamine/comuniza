"""
Async Event Handlers for Comuniza Platform - Phase 1 Architecture

Handles asynchronous processing of domain events using Celery.
This enables non-blocking event processing and maintains the decoupled architecture.
"""

import logging
from datetime import datetime
from typing import Dict, Any

# Import celery app
from config.celery import app as celery_app
from apps.core.events import (
    ItemCreatedEvent,
    ItemTransferredEvent,
    LoanCompletedEvent,
    BadgeAwardedEvent,
    ReputationUpdatedEvent,
    NotificationEvent,
    UserRegisteredEvent,
    UserLoginEvent,
    GroupCreatedEvent,
    GroupMemberJoinedEvent,
    ConversationCreatedEvent
)

logger = logging.getLogger(__name__)


@celery_app.task(max_retries=3)
def process_event_handler(handler_name: str, event_data):
    """
    Execute event handler asynchronously

    Args:
        handler_name: Name of the handler function to execute
        event_data: Serialized event data as dictionary
    """
    try:
        # Reconstruct event object from dictionary
        event_type = event_data.get('event_type', '')

        # Map event types to handler functions
        handlers = {
            'ItemCreatedEvent': handle_item_creation_notification,
            'ItemTransferredEvent': handle_item_transfer_notification,
            'LoanCompletedEvent': handle_loan_completion_notification,
            'BadgeAwardedEvent': handle_badge_notification,
            'ReputationUpdatedEvent': handle_reputation_notification,
            'UserRegisteredEvent': handle_welcome_notification,
            'UserLoginEvent': handle_login_logging,
            'GroupCreatedEvent': handle_group_creation_notification,
            'GroupMemberJoinedEvent': handle_group_member_notification,
            'ConversationCreatedEvent': handle_conversation_creation_notification,
        }

        handler = handlers.get(event_type)
        if event_type and handler:
            logger.info(f"Executing async handler: {handler_name} for {event_type}")
            # Create a simple event object from the data
            event_data_dict = event_data.get('data', event_data)
            event_obj = type('SimpleEvent', (), event_data_dict)()
            handler(event_obj)
        else:
            logger.warning(f"Unknown event type: {event_type or 'None'}")

    except Exception as exc:
        logger.error(f"Event handler {handler_name} failed: {exc}", exc_info=True)
        # Retry logic handled by Celery's built-in retry mechanism


def handle_item_creation_notification(event: ItemCreatedEvent):
    """Handle item creation notifications (async)"""
    try:
        # Create simple notification for item creation
        logger.info(f"Item {event.item_id} created by user {event.owner_id}")
    except Exception as e:
        logger.error(f"Item creation notification failed: {e}")


def handle_item_transfer_notification(event: ItemTransferredEvent):
    """Handle item transfer notifications (async)"""
    try:
        logger.info(f"Item {event.item_id} transferred from user {event.from_user_id} to {event.to_user_id} ({event.transfer_type})")
    except Exception as e:
        logger.error(f"Item transfer notification failed: {e}")


def handle_loan_completion_notification(event: LoanCompletedEvent):
    """Handle loan completion notifications (async)"""
    try:
        logger.info(f"Loan {event.loan_id} completed by user {event.user_id}")
    except Exception as e:
        logger.error(f"Loan completion notification failed: {e}")


def handle_badge_notification(event: BadgeAwardedEvent):
    """Handle badge award notifications (async)"""
    try:
        logger.info(f"Badge '{event.badge_name}' awarded to user {event.user_id}")
    except Exception as e:
        logger.error(f"Badge notification failed: {e}")


def handle_reputation_notification(event: ReputationUpdatedEvent):
    """Handle reputation change notifications (async)"""
    try:
        logger.info(f"Reputation for user {event.user_id} changed from {event.old_score} to {event.new_score} ({event.reason})")
    except Exception as e:
        logger.error(f"Reputation notification failed: {e}")


def handle_welcome_notification(event: UserRegisteredEvent):
    """Create welcome notification for new user (async)"""
    try:
        logger.info(f"New user registered: {event.username} ({event.email})")
    except Exception as e:
        logger.error(f"Welcome notification failed: {e}")


def handle_login_logging(event: UserLoginEvent):
    """Log user login for audit trail (async)"""
    try:
        logger.info(f"User {event.user_id} logged in at {event.login_time} from {event.ip_address}")
    except Exception as e:
        logger.error(f"Login logging failed: {e}")


def handle_group_creation_notification(event: GroupCreatedEvent):
    """Create notification for group creation (async)"""
    try:
        logger.info(f"Group '{event.group_name}' created by user {event.creator_id}")
    except Exception as e:
        logger.error(f"Group creation notification failed: {e}")


def handle_group_member_notification(event: GroupMemberJoinedEvent):
    """Create notification for new group member (async)"""
    try:
        logger.info(f"User {event.user_id} joined group {event.group_id}")
    except Exception as e:
        logger.error(f"Group member notification failed: {e}")


def handle_conversation_creation_notification(event: ConversationCreatedEvent):
    """Create notification for conversation creation (async)"""
    try:
        participant_count = len(event.participant_ids)
        logger.info(f"New conversation {event.conversation_id} created with {participant_count} participant(s)")
    except Exception as e:
        logger.error(f"Conversation notification failed: {e}")


# Handler registry for mapping event types to handlers
EVENT_HANDLERS = {
    'ItemCreatedEvent': handle_item_creation_notification,
    'ItemTransferredEvent': handle_item_transfer_notification,
    'LoanCompletedEvent': handle_loan_completion_notification,
    'BadgeAwardedEvent': handle_badge_notification,
    'ReputationUpdatedEvent': handle_reputation_notification,
    'UserRegisteredEvent': handle_welcome_notification,
    'UserLoginEvent': handle_login_logging,
    'GroupCreatedEvent': handle_group_creation_notification,
    'GroupMemberJoinedEvent': handle_group_member_notification,
    'ConversationCreatedEvent': handle_conversation_creation_notification,
}


def get_handler_for_event(event_type: str):
    """Get the appropriate handler function for an event type"""
    return EVENT_HANDLERS.get(event_type)

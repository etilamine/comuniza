"""
Domain Events for Comuniza Platform - Phase 1 Architecture Foundation

Simplified event system that avoids dataclass field ordering issues.
Uses regular classes with proper __init__ methods.
"""

from typing import Callable, List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DomainEvent:
    """Base class for all domain events"""
    def __init__(self, aggregate_id: int):
        self.aggregate_id = aggregate_id
        self.timestamp = datetime.utcnow()
        self.event_type = self.__class__.__name__
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            'event_type': self.event_type,
            'aggregate_id': self.aggregate_id,
            'timestamp': self.timestamp.isoformat(),
            'data': self.__dict__
        }


class ItemCreatedEvent(DomainEvent):
    """Fired when a new item is created"""
    def __init__(self, item_id: int, owner_id: int, item_name: str, category: str):
        super().__init__(aggregate_id=item_id)
        self.item_id = item_id
        self.owner_id = owner_id
        self.item_name = item_name
        self.category = category


class ItemTransferredEvent(DomainEvent):
    """Fired when an item changes hands (loan, gift, exchange)"""
    def __init__(self, item_id: int, from_user_id: int, to_user_id: int, transfer_type: str):
        super().__init__(aggregate_id=item_id)
        self.item_id = item_id
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.transfer_type = transfer_type


class LoanCompletedEvent(DomainEvent):
    """Fired when a loan is completed and returned"""
    def __init__(self, loan_id: int, user_id: int, item_id: int, days_outstanding: int, condition_rating: int):
        super().__init__(aggregate_id=loan_id)
        self.loan_id = loan_id
        self.user_id = user_id
        self.item_id = item_id
        self.days_outstanding = days_outstanding
        self.condition_rating = condition_rating


class BadgeAwardedEvent(DomainEvent):
    """Fired when a user earns a badge"""
    def __init__(self, user_id: int, badge_id: int, badge_name: str, badge_type: str):
        super().__init__(aggregate_id=badge_id)
        self.user_id = user_id
        self.badge_id = badge_id
        self.badge_name = badge_name
        self.badge_type = badge_type


class ReputationUpdatedEvent(DomainEvent):
    """Fired when user reputation changes"""
    def __init__(self, user_id: int, old_score: float, new_score: float, reason: str, related_user_id: Optional[int] = None):
        super().__init__(aggregate_id=user_id)
        self.user_id = user_id
        self.old_score = old_score
        self.new_score = new_score
        self.reason = reason
        self.related_user_id = related_user_id


class NotificationEvent(DomainEvent):
    """Base class for notification-related events"""
    def __init__(self, user_id: int, notification_type: str, message: str, related_object_type: Optional[str] = None, related_object_id: Optional[int] = None):
        super().__init__(aggregate_id=user_id)
        self.user_id = user_id
        self.notification_type = notification_type
        self.message = message
        self.related_object_type = related_object_type
        self.related_object_id = related_object_id


class UserRegisteredEvent(DomainEvent):
    """Fired when a new user registers"""
    def __init__(self, user_id: int, username: str, email: str):
        super().__init__(aggregate_id=user_id)
        self.user_id = user_id
        self.username = username
        self.email = email


class UserLoginEvent(DomainEvent):
    """Fired when a user successfully logs in"""
    def __init__(self, user_id: int, login_time: Optional[datetime] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        super().__init__(aggregate_id=user_id)
        self.user_id = user_id
        self.login_time = login_time or datetime.utcnow()
        self.ip_address = ip_address
        self.user_agent = user_agent


class GroupCreatedEvent(DomainEvent):
    """Fired when a new group is created"""
    def __init__(self, group_id: int, creator_id: int, group_name: str, group_type: str = 'basic'):
        super().__init__(aggregate_id=group_id)
        self.group_id = group_id
        self.creator_id = creator_id
        self.group_name = group_name
        self.group_type = group_type


class GroupMemberJoinedEvent(DomainEvent):
    """Fired when a user joins a group"""
    def __init__(self, group_id: int, user_id: int, joined_by_user_id: Optional[int] = None):
        super().__init__(aggregate_id=group_id)
        self.group_id = group_id
        self.user_id = user_id
        self.joined_by_user_id = joined_by_user_id


class ConversationCreatedEvent(DomainEvent):
    """Fired when a new conversation is created"""
    def __init__(self, conversation_id: int, creator_id: int, participant_ids: List[int], subject: Optional[str] = None):
        super().__init__(aggregate_id=conversation_id)
        self.conversation_id = conversation_id
        self.creator_id = creator_id
        self.participant_ids = participant_ids
        self.subject = subject


class EventBus:
    """Pub/Sub event system for decoupled architecture"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[DomainEvent] = []
    
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe handler to event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed handler {handler.__name__} to {event_type}")
    
    def publish(self, event: DomainEvent):
        """Publish event to all subscribers"""
        event_type = event.event_type
        
        # Add to event history for audit/debugging
        self._event_history.append(event)
        
        logger.info(f"Publishing {event_type} event: {event}")
        
        # Call all subscribers asynchronously via Celery
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    # Execute handler asynchronously through Celery
                    from apps.core.handlers import process_event_handler
                    handler_name = handler.__name__
                    event_data = event.to_dict()
                    process_event_handler.delay(handler_name, event_data)
                except Exception as e:
                    logger.error(f"Error scheduling async handler {handler.__name__}: {e}")
        else:
            logger.warning(f"No subscribers for event type: {event_type}")
    
    def get_event_history(self, event_type: Optional[str] = None) -> List[DomainEvent]:
        """Get event history for debugging/audit"""
        if event_type:
            return [e for e in self._event_history if e.event_type == event_type]
        return self._event_history.copy()
    
    def clear_history(self):
        """Clear event history (useful for testing)"""
        self._event_history.clear()


# Global event bus instance for the application
event_bus = EventBus()
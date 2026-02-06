"""
Core app configuration for Comuniza.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Core app configuration."""

    name = 'apps.core'
    verbose_name = 'Core'


    def ready(self):
        """Initialize event system when app is ready."""
        from apps.core.events import event_bus
        from apps.core.handlers import EVENT_HANDLERS

        for event_type, handler in EVENT_HANDLERS.items():
            event_bus.subscribe(event_type, handler)

        print(f"✅ Event handlers registered for {len(EVENT_HANDLERS)} event types")

"""
Management command to run the RabbitMQ event consumer.

Usage:
    python manage.py run_event_consumer
"""

import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from api.events.bus_registry import BusRegistry
from api.events.subscriber import start_consumer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Start the RabbitMQ event consumer"

    def handle(self, *args, **options):
        # Register message bus for this process
        self._register_message_bus()

        self.stdout.write(self.style.SUCCESS("Starting event consumer..."))
        start_consumer()

    def _register_message_bus(self):
        """Register the message bus configuration for this consumer process."""
        bus_cfg = getattr(settings, "MESSAGE_BUS_CONFIG", None)
        if not bus_cfg:
            self.stdout.write(self.style.WARNING("No MESSAGE_BUS_CONFIG found in settings"))
            return

        backend = bus_cfg.get("backend")
        if not backend:
            self.stdout.write(self.style.WARNING("MESSAGE_BUS_CONFIG missing 'backend' key"))
            return

        BusRegistry.set(backend=backend, config=bus_cfg.get(backend, {}))
        self.stdout.write(self.style.SUCCESS(f"Registered message bus: {backend}"))
        logger.info(f"Registered message bus config for backend {backend} (consumer context)")

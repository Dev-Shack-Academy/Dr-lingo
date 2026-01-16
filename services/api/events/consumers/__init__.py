"""Event consumers for receiving messages from the message bus."""

from .base import BaseConsumer
from .rabbitmq import RabbitMQConsumer

__all__ = [
    "BaseConsumer",
    "RabbitMQConsumer",
]

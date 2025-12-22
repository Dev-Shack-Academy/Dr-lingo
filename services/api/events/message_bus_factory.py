"""
Message Bus Factory.

Build producer and consumer instances for the configured backend.
This class does not open network connections - it only constructs
the correct class with the given config.
"""

from typing import Any

from .consumers import RabbitMQConsumer
from .producers import RabbitMQProducer


class MessageBusFactory:
    """
    Build producer and consumer instances for the configured backend.

    This class does not open network connections.
    It only constructs the correct producer/consumer class with the given config.
    """

    def __init__(self, full_config: dict[str, Any]):
        """
        Store the full message bus configuration dictionary.

        Args:
            full_config: Configuration dict with 'backend' key and backend-specific section
        """
        self.full_config = full_config

    def build_producer(self):
        """
        Build a producer instance for the configured backend.

        The full_config is expected to contain a 'backend' key
        and a section for that backend with the concrete settings.

        Returns:
            A producer instance (RabbitMQProducer, etc.)

        Raises:
            ValueError: If backend is not supported
        """
        backend = (self.full_config.get("backend") or "").lower()

        if backend == "rabbitmq":
            cfg = self.full_config.get("rabbitmq") or {}
            return RabbitMQProducer(cfg)

        raise ValueError(f"Unsupported backend '{backend}'")

    def build_consumer(self):
        """
        Build a consumer instance for the configured backend.

        Returns:
            A consumer instance (RabbitMQConsumer, etc.)

        Raises:
            ValueError: If backend is not supported
        """
        backend = (self.full_config.get("backend") or "").lower()

        if backend == "rabbitmq":
            consumer = RabbitMQConsumer()
            consumer.configure(self.full_config.get("rabbitmq") or {})
            return consumer

        raise ValueError(f"Unsupported backend '{backend}'")

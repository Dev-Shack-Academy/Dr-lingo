from abc import ABC, abstractmethod
from typing import Any, Callable


class BaseConsumer(ABC):
    """
    Abstract base class for message bus consumers.

    Subclasses must implement configure, connect, subscribe, and run_forever.
    """

    def __init__(self):
        """Initialize the consumer."""
        self.config: dict[str, Any] = {}
        self._connected = False
        self._handlers: dict[str, list[Callable]] = {}

    @abstractmethod
    def configure(self, config: dict[str, Any]) -> None:
        """
        Configure the consumer with backend-specific settings.

        Args:
            config: Backend-specific configuration dictionary
        """
        pass

    @abstractmethod
    def connect(self) -> None:
        """Open a connection to the message bus."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection to the message bus."""
        pass

    @abstractmethod
    def subscribe(self, topic: str, handler: Callable[[dict[str, Any]], None]) -> None:
        """
        Subscribe to a topic with a handler function.

        Args:
            topic: The routing key/topic pattern to subscribe to
            handler: Function to call when a message is received
        """
        pass

    @abstractmethod
    def run_forever(self) -> None:
        """Start consuming messages. Blocks until stopped."""
        pass

    def register_handler(self, topic: str, handler: Callable[[dict[str, Any]], None]) -> None:
        """Register a handler for a topic pattern."""
        if topic not in self._handlers:
            self._handlers[topic] = []
        self._handlers[topic].append(handler)

    def get_handlers(self, topic: str) -> list[Callable]:
        """Get all handlers that match a topic."""
        handlers = []

        # Exact match
        if topic in self._handlers:
            handlers.extend(self._handlers[topic])

        # Wildcard handlers (e.g., "message.*" matches "message.created")
        for pattern, pattern_handlers in self._handlers.items():
            if pattern.endswith(".*"):
                prefix = pattern[:-2]
                if topic.startswith(prefix + "."):
                    handlers.extend(pattern_handlers)
            elif pattern == "#":
                handlers.extend(pattern_handlers)

        return handlers

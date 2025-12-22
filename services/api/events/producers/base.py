"""Base producer interface for message bus implementations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class PublishResult:
    """Result of a publish operation."""

    success: bool
    topic: str
    message_id: str | None
    receipt: str | None = None
    error: str | None = None


class BaseProducer(ABC):
    """
    Abstract base class for message bus producers.

    Subclasses must implement connect, disconnect, publish, and is_connected.
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize the producer with configuration.

        Args:
            config: Backend-specific configuration dictionary
        """
        self.config = config
        self._connected = False

    @abstractmethod
    def connect(self) -> None:
        """Open a connection to the message bus."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection to the message bus."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Return True if the producer is connected."""
        pass

    @abstractmethod
    def publish(
        self,
        topic: str,
        message: dict[str, Any] | str | bytes,
        headers: dict[str, Any] | None = None,
    ) -> PublishResult:
        """
        Publish a message to the specified topic.

        Args:
            topic: The routing key/topic for the message
            message: The message payload (dict, str, or bytes)
            headers: Optional message headers

        Returns:
            PublishResult with success status and metadata
        """
        pass

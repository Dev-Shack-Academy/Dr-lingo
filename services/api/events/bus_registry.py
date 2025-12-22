"""
Bus Registry - Process-local registry for message bus configuration.

This class stores the configured message bus backend and its settings.
It does not open any connections or perform any I/O - it simply provides
a safe place to store and retrieve configuration for the current process.
"""

from threading import RLock
from typing import Any


class BusRegistry:
    """
    A process-local registry for storing the configured message bus backend and its settings.

    This class does not open any connections or perform any I/O.
    It simply provides a safe place to store and retrieve configuration for the current process.
    """

    _backend: str | None = None
    _config: dict[str, Any] | None = None
    _lock = RLock()

    @classmethod
    def set(cls, *, backend: str, config: dict[str, Any]) -> None:
        """
        Store the backend and its configuration in the registry.

        This should be called once during process startup,
        for example from Django apps.py or a Celery init hook.
        """
        with cls._lock:
            cls._backend = backend
            cls._config = dict(config)

    @classmethod
    def get(cls) -> tuple[str, dict[str, Any]]:
        """
        Retrieve the backend and configuration from the registry.

        Raises a RuntimeError if the registry has not been populated.
        """
        if cls._backend is None or cls._config is None:
            raise RuntimeError("Message bus not registered for this process")
        return cls._backend, dict(cls._config)

    @classmethod
    def is_configured(cls) -> bool:
        """Check if the registry has been configured."""
        return cls._backend is not None and cls._config is not None

    @classmethod
    def clear(cls) -> None:
        """Clear the registry (mainly for testing)."""
        with cls._lock:
            cls._backend = None
            cls._config = None

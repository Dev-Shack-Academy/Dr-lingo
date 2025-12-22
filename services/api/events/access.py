"""
Event Bus Access.

Provides singleton access to the message bus producer and consumer.
The first call builds the instance from the BusRegistry config.
"""

import logging
from threading import Lock
from typing import Any

from .bus_registry import BusRegistry
from .message_bus_factory import MessageBusFactory

logger = logging.getLogger(__name__)

_producer_singleton: Any | None = None
_producer_lock = Lock()


def get_producer():
    """
    Return the process-local producer singleton.

    The first call builds the producer from the BusRegistry config.
    The producer will connect lazily on first publish.

    Returns:
        A producer instance or None if not configured

    Raises:
        RuntimeError: If BusRegistry is not configured
    """
    global _producer_singleton
    if _producer_singleton is not None:
        return _producer_singleton

    with _producer_lock:
        if _producer_singleton is not None:
            return _producer_singleton

        if not BusRegistry.is_configured():
            logger.warning("Message bus not configured, returning None")
            return None

        backend, backend_config = _load_registry_config()
        full_config = {"backend": backend, backend: backend_config}
        _producer_singleton = MessageBusFactory(full_config).build_producer()
        return _producer_singleton


def _load_registry_config() -> tuple[str, dict]:
    """
    Load backend and config from the BusRegistry.

    Raises if the registry was not populated at startup.
    """
    backend, full = BusRegistry.get()
    if backend in full:
        return backend, full[backend]
    return backend, full


_consumer_singleton: Any | None = None
_consumer_lock = Lock()


def get_consumer():
    """
    Return the process-local consumer singleton.

    The first call builds the consumer from the BusRegistry config.
    The caller is responsible for connect, subscribe, and run_forever.

    Returns:
        A consumer instance or None if not configured
    """
    global _consumer_singleton
    if _consumer_singleton is not None:
        return _consumer_singleton

    with _consumer_lock:
        if _consumer_singleton is not None:
            return _consumer_singleton

        if not BusRegistry.is_configured():
            logger.warning("Message bus not configured, returning None")
            return None

        backend, backend_config = _load_registry_config()
        full_config = {"backend": backend, backend: backend_config}
        _consumer_singleton = MessageBusFactory(full_config).build_consumer()
        return _consumer_singleton


def reset_singletons():
    """Reset the singletons (mainly for testing)."""
    global _producer_singleton, _consumer_singleton
    with _producer_lock:
        if _producer_singleton is not None:
            try:
                _producer_singleton.disconnect()
            except Exception:
                pass
            _producer_singleton = None

    with _consumer_lock:
        if _consumer_singleton is not None:
            try:
                _consumer_singleton.disconnect()
            except Exception:
                pass
            _consumer_singleton = None

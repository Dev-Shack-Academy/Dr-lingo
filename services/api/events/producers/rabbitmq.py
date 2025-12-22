"""
RabbitMQ Producer Implementation.

A blocking producer for RabbitMQ that uses one connection and channel per thread.
Connects on first publish in the thread. Uses publisher confirms. Retries once on failure.
"""

import json
import logging
import threading
import uuid
from typing import Any

from .base import BaseProducer, PublishResult

logger = logging.getLogger(__name__)


class RabbitMQProducer(BaseProducer):
    """
    A blocking producer for RabbitMQ.

    Uses one connection and channel per thread. Connects on first publish in the thread.
    Uses publisher confirms. Retries once on failure. No background threads.
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._exchange_name: str = self.config.get("exchange_name", "medical_translation_events")
        self._local = threading.local()

        pub = self.config.get("publish", {}) or {}
        self._default_mandatory: bool = bool(pub.get("mandatory", False))
        ct = pub.get("confirm_timeout")
        self._confirm_timeout: float | None = float(ct) if ct is not None else None

    def _thread_lock(self) -> threading.RLock:
        """Return a per-thread connect lock."""
        lock = getattr(self._local, "connect_lock", None)
        if lock is None:
            lock = threading.RLock()
            self._local.connect_lock = lock
        return lock

    @property
    def _connection(self):
        return getattr(self._local, "connection", None)

    @_connection.setter
    def _connection(self, value) -> None:
        self._local.connection = value

    @property
    def _channel(self):
        return getattr(self._local, "channel", None)

    @_channel.setter
    def _channel(self, value) -> None:
        self._local.channel = value

    def is_connected(self) -> bool:
        """Return True if the channel is open."""
        ch = self._channel
        return bool(ch and ch.is_open)

    def connect(self) -> None:
        """Open a per-thread connection and channel. Declare the exchange. Enable confirms."""
        if self.is_connected():
            self._connected = True
            return

        with self._thread_lock():
            if self.is_connected():
                self._connected = True
                return

            try:
                import pika
            except ImportError:
                logger.error("pika not installed. Run: pip install pika")
                raise

            url = self.config.get("url")
            if not url:
                raise ValueError("RabbitMQProducer requires url in config.")

            params = pika.URLParameters(url)
            tune = self.config.get("kwargs", {}) or {}
            if tune.get("heartbeat") is not None:
                params.heartbeat = int(tune["heartbeat"])
            if tune.get("blocked_connection_timeout") is not None:
                params.blocked_connection_timeout = float(tune["blocked_connection_timeout"])
            if tune.get("socket_timeout") is not None:
                params.socket_timeout = float(tune["socket_timeout"])
            if tune.get("connection_attempts") is not None:
                params.connection_attempts = int(tune["connection_attempts"])
            if tune.get("retry_delay") is not None:
                params.retry_delay = float(tune["retry_delay"])

            conn = pika.BlockingConnection(params)
            ch = conn.channel()

            if not self._exchange_name:
                conn.close()
                raise ValueError("RabbitMQProducer requires exchange_name in config.")

            ch.exchange_declare(exchange=self._exchange_name, exchange_type="topic", durable=True)
            ch.confirm_delivery()

            # Track unroutable returns for mandatory publishes
            self._local.returned = False

            def _on_return(_ch, _method, _properties, _body):
                self._local.returned = True

            ch.add_on_return_callback(_on_return)

            self._connection = conn
            self._channel = ch
            self._connected = True
            logger.info(f"RabbitMQ producer connected to exchange '{self._exchange_name}'")

    def disconnect(self) -> None:
        """Close the channel and connection for this thread."""
        ch = self._channel
        if ch and ch.is_open:
            try:
                ch.close()
            finally:
                self._channel = None

        conn = self._connection
        if conn and conn.is_open:
            try:
                conn.close()
            finally:
                self._connection = None

        self._connected = False
        logger.debug("RabbitMQ producer disconnected")

    def publish(
        self,
        topic: str,
        message: dict[str, Any] | str | bytes,
        headers: dict[str, Any] | None = None,
        mandatory: bool | None = None,
    ) -> PublishResult:
        """Publish one message. Confirm delivery. Retry once on failure."""
        if not self.is_connected():
            self.connect()

        ch = self._channel
        if ch is None:
            return PublishResult(False, topic, None, None, "Not connected")

        hdrs = dict(headers or {})
        msg_id = self._ensure_message_id(hdrs)

        try:
            body, content_type = self._to_bytes(message)
        except Exception as exc:
            return PublishResult(False, topic, msg_id, None, str(exc))

        import pika

        props = pika.BasicProperties(
            delivery_mode=2,  # Persistent
            content_type=content_type,
            message_id=msg_id,
            headers=hdrs,
        )

        use_mand = self._default_mandatory if mandatory is None else bool(mandatory)

        try:
            return self._try_publish(ch, topic, body, props, msg_id, use_mand)
        except Exception:
            try:
                return self._retry_publish(topic, body, props, msg_id, use_mand)
            except Exception as e:
                logger.error(f"Failed to publish to {topic}: {e}")
                return PublishResult(False, topic, msg_id, None, str(e))

    def _try_publish(self, ch, topic: str, body: bytes, props, msg_id: str, mandatory: bool) -> PublishResult:
        """Attempt to publish once with confirms."""
        if hasattr(self._local, "returned"):
            self._local.returned = False

        receipt = self._get_next_seq_no(ch)

        ch.basic_publish(
            exchange=self._exchange_name,
            routing_key=topic,
            body=body,
            properties=props,
            mandatory=mandatory,
        )

        if hasattr(ch, "wait_for_confirms"):
            ok = ch.wait_for_confirms(timeout=self._confirm_timeout)
            if not ok:
                return PublishResult(
                    False,
                    topic,
                    msg_id,
                    str(receipt) if receipt is not None else None,
                    "Publish not confirmed by broker",
                )

        if mandatory and getattr(self._local, "returned", False):
            self._local.returned = False
            return PublishResult(
                False,
                topic,
                msg_id,
                str(receipt) if receipt is not None else None,
                "Message was returned unroutable",
            )

        logger.debug(f"Published message to {topic}: {msg_id}")
        return PublishResult(True, topic, msg_id, str(receipt) if receipt is not None else None)

    def _retry_publish(self, topic: str, body: bytes, props, msg_id: str, mandatory: bool) -> PublishResult:
        """Retry publishing once after reconnect."""
        logger.warning(f"Retrying publish to {topic}")
        self.disconnect()
        self.connect()
        ch2 = self._channel
        if ch2 is None:
            return PublishResult(False, topic, msg_id, None, "Reconnect failed")

        if hasattr(self._local, "returned"):
            self._local.returned = False

        return self._try_publish(ch2, topic, body, props, msg_id, mandatory)

    def _ensure_message_id(self, headers: dict[str, Any] | None) -> str:
        """Return a message id. Use header if present, else create one."""
        msg_id = (headers or {}).get("message_id") if isinstance(headers, dict) else None
        if isinstance(msg_id, str) and msg_id:
            return msg_id
        msg_id = uuid.uuid4().hex
        if headers is not None:
            headers["message_id"] = msg_id
        return msg_id

    @staticmethod
    def _get_next_seq_no(ch) -> int | None:
        """Return the next publish sequence number if available."""
        get_no = getattr(ch, "get_next_publish_seq_no", None)
        if callable(get_no):
            try:
                return int(get_no())
            except Exception:
                return None
        return None

    @staticmethod
    def _to_bytes(message: dict[str, Any] | str | bytes) -> tuple[bytes, str]:
        """Convert supported payloads to json bytes with a content type."""
        content_type = "application/json; charset=utf-8"
        if isinstance(message, dict):
            return json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), content_type
        if isinstance(message, str):
            return message.encode("utf-8"), content_type
        if isinstance(message, (bytes, bytearray)):
            return bytes(message), content_type
        raise TypeError("Message must be dict, str, bytes, or bytearray.")

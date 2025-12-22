import json
import logging
from typing import Any, Callable

from .base import BaseConsumer

logger = logging.getLogger(__name__)


class RabbitMQConsumer(BaseConsumer):
    """
    A blocking consumer for RabbitMQ.

    Connects to RabbitMQ, subscribes to topics, and dispatches messages
    to registered handlers.
    """

    def __init__(self):
        super().__init__()
        self._connection = None
        self._channel = None
        self._exchange_name = "medical_translation_events"
        self._queue_name = None

    def configure(self, config: dict[str, Any]) -> None:
        """Configure the consumer with RabbitMQ settings."""
        self.config = config
        self._exchange_name = config.get("exchange_name", "medical_translation_events")

    def connect(self) -> None:
        """Open a connection to RabbitMQ."""
        if self._connected:
            return

        try:
            import pika
        except ImportError:
            logger.error("pika not installed. Run: pip install pika")
            raise

        url = self.config.get("url")
        if not url:
            raise ValueError("RabbitMQConsumer requires url in config.")

        params = pika.URLParameters(url)
        tune = self.config.get("kwargs", {}) or {}
        if tune.get("heartbeat") is not None:
            params.heartbeat = int(tune["heartbeat"])
        if tune.get("prefetch_count") is not None:
            self._prefetch_count = int(tune["prefetch_count"])
        else:
            self._prefetch_count = 1

        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()

        # Declare exchange
        self._channel.exchange_declare(
            exchange=self._exchange_name,
            exchange_type="topic",
            durable=True,
        )

        # Create exclusive queue for this consumer
        result = self._channel.queue_declare(queue="", exclusive=True)
        self._queue_name = result.method.queue

        # Set prefetch
        self._channel.basic_qos(prefetch_count=self._prefetch_count)

        self._connected = True
        logger.info(f"RabbitMQ consumer connected to exchange '{self._exchange_name}'")

    def disconnect(self) -> None:
        """Close the connection to RabbitMQ."""
        if self._channel and self._channel.is_open:
            try:
                self._channel.close()
            except Exception:
                pass
            self._channel = None

        if self._connection and self._connection.is_open:
            try:
                self._connection.close()
            except Exception:
                pass
            self._connection = None

        self._connected = False
        logger.debug("RabbitMQ consumer disconnected")

    def subscribe(self, topic: str, handler: Callable[[dict[str, Any]], None]) -> None:
        """
        Subscribe to a topic with a handler function.

        Args:
            topic: The routing key pattern (e.g., "message.created", "message.*", "#")
            handler: Function to call when a message is received
        """
        self.register_handler(topic, handler)

        if self._connected and self._channel:
            self._channel.queue_bind(
                exchange=self._exchange_name,
                queue=self._queue_name,
                routing_key=topic,
            )
            logger.debug(f"Subscribed to topic: {topic}")

    def run_forever(self) -> None:
        """Start consuming messages. Blocks until stopped."""
        if not self._connected:
            self.connect()

        # Bind all registered topics
        for topic in self._handlers.keys():
            self._channel.queue_bind(
                exchange=self._exchange_name,
                queue=self._queue_name,
                routing_key=topic,
            )

        def callback(ch, method, properties, body):
            try:
                event_data = json.loads(body)
                event_type = event_data.get("event_type", method.routing_key)
                payload = event_data.get("payload", event_data)

                logger.debug(f"Received event: {event_type}")

                # Dispatch to handlers
                handlers = self.get_handlers(event_type)
                for handler in handlers:
                    try:
                        handler(payload)
                    except Exception as e:
                        logger.error(f"Handler {handler.__name__} failed for {event_type}: {e}")

                ch.basic_ack(delivery_tag=method.delivery_tag)

            except Exception as e:
                logger.error(f"Failed to process event: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        self._channel.basic_consume(
            queue=self._queue_name,
            on_message_callback=callback,
            auto_ack=False,
        )

        logger.info("Event consumer started, waiting for events...")
        try:
            self._channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
            self._channel.stop_consuming()
        finally:
            self.disconnect()

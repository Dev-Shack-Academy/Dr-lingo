import json
import logging
import signal

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Consume events from message queue (Pub/Sub or RabbitMQ)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.should_stop = False

    def add_arguments(self, parser):
        parser.add_argument(
            "--queue",
            type=str,
            default="dr_lingo_events",
            help="Queue/subscription name to consume from (default: dr_lingo_events)",
        )

    def handle(self, *args, **options):
        queue_name = options["queue"]

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Check if we should use Pub/Sub (Cloud Run) or RabbitMQ (docker-compose)
        use_pubsub = getattr(settings, "USE_PUBSUB", False)

        if use_pubsub:
            self.stdout.write(self.style.SUCCESS("Starting Pub/Sub event consumer..."))
            self._run_pubsub_consumer()
        else:
            self.stdout.write(self.style.SUCCESS(f"Starting RabbitMQ event consumer for queue: {queue_name}"))
            self._run_rabbitmq_mode(queue_name)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.stdout.write(self.style.WARNING("\nShutting down consumer..."))
        self.should_stop = True

    def _run_pubsub_consumer(self):
        """Run the Cloud Pub/Sub consumer."""
        try:
            from google.cloud import pubsub_v1
        except ImportError:
            self.stdout.write(
                self.style.ERROR("google-cloud-pubsub not installed. Install with: poetry add google-cloud-pubsub")
            )
            self._run_mock_consumer()
            return

        from api.events.subscriber import dispatch_event

        project_id = getattr(settings, "PUBSUB_PROJECT_ID", "")
        subscription_name = getattr(settings, "PUBSUB_SUBSCRIPTION", "dr-lingo-events-sub")

        if not project_id:
            self.stdout.write(self.style.ERROR("PUBSUB_PROJECT_ID not configured"))
            self._run_mock_consumer()
            return

        subscriber = pubsub_v1.SubscriberClient()
        subscription_path = subscriber.subscription_path(project_id, subscription_name)

        def callback(message):
            try:
                data = json.loads(message.data.decode("utf-8"))
                event_type = data.get("event_type", "unknown")
                payload = data.get("payload", {})

                self.stdout.write(f"Received event: {event_type}")
                logger.info(f"Processing event: {event_type} - {payload}")

                # Dispatch to registered handlers
                dispatch_event(event_type, payload)

                # Acknowledge the message
                message.ack()

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in message: {e}")
                message.nack()
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                message.nack()

        self.stdout.write(self.style.SUCCESS(f"Connected to Pub/Sub subscription: {subscription_path}"))
        self.stdout.write("Waiting for events...")

        # Subscribe with flow control
        flow_control = pubsub_v1.types.FlowControl(max_messages=10)
        streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback, flow_control=flow_control)

        try:
            # Block until shutdown signal
            while not self.should_stop:
                streaming_pull_future.result(timeout=1)
        except Exception as e:
            streaming_pull_future.cancel()
            streaming_pull_future.result()
            self.stdout.write(self.style.WARNING(f"Pub/Sub consumer stopped: {e}"))

        self.stdout.write(self.style.SUCCESS("Pub/Sub consumer stopped."))

    def _run_rabbitmq_mode(self, queue_name: str):
        """Try RabbitMQ, fall back to mock."""
        try:
            import pika  # noqa: F401
        except ImportError:
            self.stdout.write(self.style.ERROR("pika is not installed. Install it with: poetry add pika"))
            self.stdout.write(self.style.WARNING("Running in mock mode (logging events only)..."))
            self._run_mock_consumer()
            return

        rabbitmq_url = getattr(settings, "RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

        try:
            self._run_rabbitmq_consumer(rabbitmq_url, queue_name)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to connect to RabbitMQ: {e}"))
            self.stdout.write(self.style.WARNING("Make sure RabbitMQ is running."))
            self.stdout.write(self.style.WARNING("Running in mock mode (logging events only)..."))
            self._run_mock_consumer()

    def _run_rabbitmq_consumer(self, rabbitmq_url: str, queue_name: str):
        """Run the RabbitMQ consumer."""
        import pika

        from api.events.subscriber import dispatch_event

        parameters = pika.URLParameters(rabbitmq_url)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # Declare the queue (creates if doesn't exist)
        channel.queue_declare(queue=queue_name, durable=True)

        self.stdout.write(self.style.SUCCESS("Connected to RabbitMQ. Waiting for events..."))

        def callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                event_type = message.get("event_type", "unknown")
                payload = message.get("payload", {})

                self.stdout.write(f"Received event: {event_type}")
                logger.info(f"Processing event: {event_type} - {payload}")

                # Dispatch to registered handlers
                dispatch_event(event_type, payload)

                # Acknowledge the message
                ch.basic_ack(delivery_tag=method.delivery_tag)

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        # Set up consumer
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=queue_name, on_message_callback=callback)

        try:
            while not self.should_stop:
                channel.connection.process_data_events(time_limit=1)
        except KeyboardInterrupt:
            channel.stop_consuming()
        finally:
            connection.close()
            self.stdout.write(self.style.SUCCESS("Consumer stopped."))

    def _run_mock_consumer(self):
        """Run a mock consumer that just logs (for development without message queue)."""
        import time

        self.stdout.write(self.style.WARNING("Mock consumer running. Press Ctrl+C to stop."))
        self.stdout.write("In mock mode, events are published via logging only.")
        self.stdout.write("To use a message queue, configure RabbitMQ or Pub/Sub.")

        try:
            while not self.should_stop:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

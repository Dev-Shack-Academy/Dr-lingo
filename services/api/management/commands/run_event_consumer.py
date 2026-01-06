import logging
import signal
import subprocess
import sys
import threading
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from api.events.bus_registry import BusRegistry
from api.events.subscriber import start_consumer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Start the RabbitMQ event consumer with optional WebSocket server"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.daphne_process = None
        self.shutdown_event = threading.Event()

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-websocket-bridge",
            action="store_true",
            default=True,
            help="Enable WebSocket bridge to forward events to Django Channels (default: True)",
        )
        parser.add_argument(
            "--no-websocket-bridge",
            action="store_true",
            help="Disable WebSocket bridge",
        )
        parser.add_argument(
            "--ws-host",
            type=str,
            default="127.0.0.1",
            help="WebSocket server host (default: 127.0.0.1)",
        )
        parser.add_argument(
            "--ws-port",
            type=int,
            default=8001,
            help="WebSocket server port (default: 8001)",
        )

    def handle(self, *args, **options):
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Register message bus for this process
        self._register_message_bus()

        # Check if WebSocket bridge is enabled
        enable_bridge = options.get("with_websocket_bridge", True) and not options.get("no_websocket_bridge", False)

        if enable_bridge:
            # Register Channels bridge handlers
            self._register_channels_bridge()

            # Start Daphne WebSocket server in a subprocess
            ws_host = options.get("ws_host", "127.0.0.1")
            ws_port = options.get("ws_port", 8001)
            self._start_daphne(ws_host, ws_port)

        self.stdout.write(self.style.SUCCESS("Starting event consumer..."))
        self.stdout.write("Press Ctrl+C to stop.")
        self.stdout.write("")

        try:
            # Start the RabbitMQ consumer (blocking)
            start_consumer()
        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.stdout.write(self.style.WARNING("\nShutdown signal received..."))
        self.shutdown_event.set()
        self._cleanup()
        sys.exit(0)

    def _cleanup(self):
        """Clean up resources on shutdown."""
        if self.daphne_process:
            self.stdout.write("Stopping Daphne WebSocket server...")
            self.daphne_process.terminate()
            try:
                self.daphne_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.daphne_process.kill()
            self.daphne_process = None
            self.stdout.write(self.style.SUCCESS("Daphne stopped."))

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

    def _register_channels_bridge(self):
        """Register Channels bridge handlers for WebSocket forwarding."""
        try:
            from api.events.channels_bridge import register_channels_handlers

            register_channels_handlers()
            self.stdout.write(self.style.SUCCESS("Registered Channels bridge for WebSocket forwarding"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Failed to register Channels bridge: {e}"))
            logger.warning(f"Channels bridge registration failed: {e}")

    def _start_daphne(self, host: str, port: int):
        """Start Daphne ASGI server in a subprocess."""
        self.stdout.write(f"Starting Daphne WebSocket server on {host}:{port}...")

        cmd = [
            sys.executable,
            "-m",
            "daphne",
            "-b",
            host,
            "-p",
            str(port),
            "-v1",
            "config.asgi:application",
        ]

        try:
            # Start Daphne in a subprocess
            self.daphne_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            # Start a thread to read and display Daphne output
            def read_daphne_output():
                if self.daphne_process and self.daphne_process.stdout:
                    for line in self.daphne_process.stdout:
                        if self.shutdown_event.is_set():
                            break
                        # Prefix Daphne output
                        print(f"[Daphne] {line.rstrip()}")

            output_thread = threading.Thread(target=read_daphne_output, daemon=True)
            output_thread.start()

            # Give Daphne a moment to start
            time.sleep(1)

            # Check if Daphne started successfully
            if self.daphne_process.poll() is not None:
                self.stdout.write(self.style.ERROR("Daphne failed to start"))
                return

            self.stdout.write(self.style.SUCCESS(f"Daphne WebSocket server running on ws://{host}:{port}/"))
            self.stdout.write(f"WebSocket endpoint: ws://{host}:{port}/ws/chat/{{room_id}}/")
            self.stdout.write("")

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR("Daphne not found. Install it with: pip install daphne"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to start Daphne: {e}"))
            logger.error(f"Daphne startup failed: {e}")

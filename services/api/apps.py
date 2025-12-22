import logging
import sys

from django.apps import AppConfig

logger = logging.getLogger(__name__)


def is_webserver_process() -> bool:
    """
    Return True if the current process looks like a Django webserver.
    Includes runserver, gunicorn, uwsgi.
    Excludes celery worker/beat and management commands.
    """
    argv = " ".join(sys.argv).lower()
    if "celery" in argv:
        return False
    webserver_run_commands = ["daphne", "runserver", "gunicorn", "uvicorn", "uwsgi"]
    for command in webserver_run_commands:
        if command in argv:
            return True
    return False


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        """Application setup once API app is ready.

        1. Register message bus configuration in BusRegistry for webserver processes
        """
        from django.conf import settings

        from api.events.bus_registry import BusRegistry

        # Register message bus configuration for webserver processes
        if is_webserver_process():
            bus_cfg = getattr(settings, "MESSAGE_BUS_CONFIG", None)
            if bus_cfg and bus_cfg.get("backend"):
                bus_backend = bus_cfg.get("backend")
                BusRegistry.set(backend=bus_backend, config=bus_cfg.get(bus_backend, {}))
                logger.info(f"Registered message bus config for backend {bus_backend}")
            else:
                logger.debug("No message bus configuration found")

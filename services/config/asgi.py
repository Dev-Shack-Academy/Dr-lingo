import logging
import os

# Initialize Django FIRST before importing anything that uses Django models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# This MUST be called before importing any Django app code
from django.core.asgi import get_asgi_application  # noqa: E402

django_asgi_app = get_asgi_application()

# NOW it's safe to import Django app code (routing, middleware, consumers)
import api.routing  # noqa: E402
from api.middleware import WebSocketAuthMiddleware  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from django.conf import settings  # noqa: E402

logger = logging.getLogger(__name__)


# TODO: Put all Cloud Run services under a custom domain like dr-lingo.com
# Then set SESSION_COOKIE_DOMAIN = ".dr-lingo.com" and the session cookie
# would be sent automatically to all subdomains.
# Trade-off: Requires purchasing and configuring a custom domain with Cloud Run domain mapping.
# This would eliminate the need for the ticket-based authentication workaround.


def get_allowed_origins():
    """
    Get allowed origins for WebSocket connections.
    Combines ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, and CSRF_TRUSTED_ORIGINS.
    Returns a list of allowed origin strings.
    """
    allowed = set()

    # Add ALLOWED_HOSTS (with protocol)
    for host in settings.ALLOWED_HOSTS:
        if host and host != "*":
            allowed.add(f"https://{host}")
            allowed.add(f"http://{host}")

    # Add CORS origins (already have protocol)
    if hasattr(settings, "CORS_ALLOWED_ORIGINS"):
        for origin in settings.CORS_ALLOWED_ORIGINS:
            if origin:
                allowed.add(origin)

    # Add CSRF trusted origins (already have protocol)
    if hasattr(settings, "CSRF_TRUSTED_ORIGINS"):
        for origin in settings.CSRF_TRUSTED_ORIGINS:
            if origin:
                allowed.add(origin)

    logger.info(f"WebSocket allowed origins: {allowed}")
    return list(allowed)


class PermissiveOriginValidator:
    """
    Custom origin validator middleware for WebSocket connections.

    More permissive than AllowedHostsOriginValidator - allows:
    - All .run.app domains (for Cloud Run cross-service communication)
    - Origins in ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, CSRF_TRUSTED_ORIGINS
    - Connections without Origin header (non-browser clients)
    """

    def __init__(self, application):
        self.application = application

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            # Get origin from headers
            headers = dict(scope.get("headers", []))
            origin = headers.get(b"origin", b"").decode("utf-8")

            logger.info(f"WebSocket origin validation: origin={origin}")

            if not self._is_origin_allowed(origin):
                logger.warning(f"WebSocket origin rejected: {origin}")
                # Close the connection with 403
                await send({"type": "websocket.close", "code": 4003})
                return

            logger.info(f"WebSocket origin allowed: {origin}")

        return await self.application(scope, receive, send)

    def _is_origin_allowed(self, origin: str) -> bool:
        """
        Check if the origin is allowed.

        Security: Only allows WebSocket connections from:
        1. Origins explicitly listed in ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, CSRF_TRUSTED_ORIGINS
        2. Cloud Run services matching our project prefix (configurable via CLOUD_RUN_SERVICE_PREFIX)
        3. Connections without Origin header (non-browser clients)
        """
        # No origin header - allow (could be same-origin or non-browser client)
        if not origin:
            return True

        # Check against allowed origins list first (most specific)
        allowed_origins = get_allowed_origins()
        if origin in allowed_origins:
            return True

        # SECURITY: Only allow .run.app domains that match our project prefix
        # Pattern: {prefix}-{service}-{hash}-{region}.a.run.app
        # This prevents other Cloud Run services from connecting to our WebSocket
        try:
            from urllib.parse import urlparse

            parsed = urlparse(origin)
            hostname = parsed.netloc

            if hostname.endswith(".run.app") or hostname == "run.app":
                # Get the project prefix from settings (default: dr-lingo)
                project_prefix = getattr(settings, "CLOUD_RUN_SERVICE_PREFIX", "dr-lingo")

                # Only allow our specific Cloud Run services
                if hostname.startswith(f"{project_prefix}-"):
                    logger.info(f"Origin allowed (our Cloud Run service): {origin}")
                    return True
                else:
                    logger.warning(
                        f"Origin rejected (not our Cloud Run service): {hostname} (expected prefix: {project_prefix})"
                    )
                    return False
        except Exception as e:
            logger.warning(f"Error parsing origin {origin}: {e}")

        # Check if origin host is in ALLOWED_HOSTS
        try:
            from urllib.parse import urlparse

            parsed = urlparse(origin)
            host = parsed.netloc
            if host in settings.ALLOWED_HOSTS:
                return True
        except Exception as e:
            logger.warning(f"Error parsing origin {origin}: {e}")

        return False


application = ProtocolTypeRouter(
    {
        # Django's ASGI application to handle traditional HTTP requests
        "http": django_asgi_app,
        # WebSocket handler with custom permissive origin validation
        "websocket": PermissiveOriginValidator(WebSocketAuthMiddleware(URLRouter(api.routing.websocket_urlpatterns))),
    }
)

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
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402

application = ProtocolTypeRouter(
    {
        # Django's ASGI application to handle traditional HTTP requests
        "http": django_asgi_app,
        # WebSocket chat handler
        "websocket": AllowedHostsOriginValidator(
            WebSocketAuthMiddleware(URLRouter(api.routing.websocket_urlpatterns))
        ),
    }
)

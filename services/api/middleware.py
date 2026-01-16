import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.models import Session
from django.core import signing
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

logger = logging.getLogger(__name__)

User = get_user_model()

# WebSocket ticket validity period (seconds) - should match views/auth.py
WS_TICKET_MAX_AGE = 60


class WebSocketAuthMiddleware(BaseMiddleware):
    """
    WebSocket authentication middleware for Django Channels.

    Authentication methods (in order of priority):
    1. Signed ticket from query string (?ticket=...) - for cross-origin connections
    2. Session cookie - for same-origin connections

    The signed ticket is the recommended method for cross-origin WebSocket
    connections (e.g., Cloud Run where frontend and channels run on different URLs).
    """

    async def __call__(self, scope, receive, send):
        """Process WebSocket connection and authenticate user."""
        headers = dict(scope.get("headers", []))
        origin = headers.get(b"origin", b"").decode("utf-8")
        logger.info(f"WebSocket connection attempt from origin: {origin}")

        user = None
        auth_method = None

        # Parse query string
        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)

        # 1. Try signed ticket first (preferred for cross-origin)
        ticket_list = query_params.get("ticket", [])
        if ticket_list:
            ticket = ticket_list[0]
            user = await self._get_user_from_ticket(ticket)
            if user:
                auth_method = "signed_ticket"

        # 2. Try session cookie (same-origin)
        if not user:
            cookies = self._get_cookies_from_scope(scope)
            session_key = cookies.get(settings.SESSION_COOKIE_NAME)
            if session_key:
                user = await self._get_user_from_session(session_key)
                if user:
                    auth_method = "session_cookie"

        # TODO: Use signed tickets (?ticket=) for cross-origin WebSocket connections.
        # When all services are under one domain, session cookies will work automatically.

        # Set user on scope
        if user and user.is_authenticated:
            scope["user"] = user
            scope["otp_verified"] = True  # Assume verified if authenticated
            logger.info(f"WebSocket authenticated via {auth_method}: user_id={user.pk}")
        else:
            scope["user"] = AnonymousUser()
            scope["otp_verified"] = False
            logger.warning(f"WebSocket: authentication failed for origin {origin}")

        return await super().__call__(scope, receive, send)

    def _get_cookies_from_scope(self, scope) -> dict:
        """Extract cookies from WebSocket scope headers."""
        cookies = {}
        headers = dict(scope.get("headers", []))
        cookie_header = headers.get(b"cookie", b"").decode("utf-8")

        if cookie_header:
            for cookie in cookie_header.split(";"):
                cookie = cookie.strip()
                if "=" in cookie:
                    key, value = cookie.split("=", 1)
                    cookies[key.strip()] = value.strip()

        return cookies

    @database_sync_to_async
    def _get_user_from_ticket(self, ticket: str):
        """
        Validate signed ticket and retrieve user.

        The ticket is created by `get_websocket_ticket` view using TimestampSigner.
        It contains the user ID and is valid for WS_TICKET_MAX_AGE seconds.
        """
        logger.info(f"Validating WebSocket ticket (length={len(ticket)})")
        try:
            signer = signing.TimestampSigner()
            # Unsign with max_age validation
            user_id = signer.unsign(ticket, max_age=WS_TICKET_MAX_AGE)
            logger.info(f"Ticket valid, user_id={user_id}")
            user = User.objects.get(pk=user_id)
            logger.info(f"User found: user_id={user_id}")
            return user
        except signing.SignatureExpired:
            logger.warning("WebSocket ticket expired")
        except signing.BadSignature as e:
            logger.warning(f"WebSocket ticket has invalid signature: {e}")
        except User.DoesNotExist:
            logger.warning(f"User not found for ticket user_id={user_id}")
        except Exception as e:
            logger.error(f"Error validating WebSocket ticket: {type(e).__name__}: {e}")

        return None

    @database_sync_to_async
    def _get_user_from_session(self, session_key: str):
        """Retrieve user from Django session."""
        try:
            session = Session.objects.get(session_key=session_key)

            # Validate session hasn't expired
            if session.expire_date < timezone.now():
                logger.debug(f"Session expired: {session_key[:8]}...")
                return None

            session_data = session.get_decoded()
            user_id = session_data.get("_auth_user_id")

            if user_id:
                return User.objects.get(pk=user_id)
        except Session.DoesNotExist:
            logger.debug(f"Session not found: {session_key[:8]}...")
        except User.DoesNotExist:
            logger.debug(f"User not found for session: {session_key[:8]}...")
        except Exception as e:
            logger.error(f"Error getting user from session: {e}")

        return None

    @database_sync_to_async
    def _check_otp_verified(self, session_key: str) -> bool:
        """Check if OTP verification is complete for this session."""
        try:
            session = Session.objects.get(session_key=session_key)
            session_data = session.get_decoded()

            # django-otp stores verification status in session
            # The key is 'otp_device_id' when a device is verified
            otp_device_id = session_data.get("otp_device_id")

            if otp_device_id:
                return True

            # Also check for django-two-factor-auth's verification flag
            # It may use different session keys
            if session_data.get("django_two_factor-verified"):
                return True

            # Check if user has any OTP devices configured
            # If not, they might be exempt from OTP
            user_id = session_data.get("_auth_user_id")
            if user_id:
                user = User.objects.get(pk=user_id)
                # If user has no OTP devices, consider them verified
                # (they haven't set up 2FA yet)
                from django_otp import devices_for_user

                devices = list(devices_for_user(user, confirmed=True))
                if not devices:
                    return True

            return False

        except Session.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error checking OTP status: {e}")
            return False


class RequireOTPVerificationMiddleware:
    """
    Enforces two-factor authentication for authenticated users.

    This middleware ensures that any user who has completed the first step of
    authentication (e.g., password) cannot navigate the site further until
    they have also completed the second factor (OTP verification).

    Similar to the RequireOTPVerificationMiddleware in objective_boilerplate.
    """

    def __init__(self, get_response):
        """
        Initialize the middleware, building the cache of exempt paths.
        """
        self.get_response = get_response
        self.exempt_paths = set()
        self.exempt_prefixes = tuple(getattr(settings, "OTP_EXEMPT_PATH_PREFIXES", ["/static/", "/api/"]))

        # Get setup URL
        try:
            self.setup_url = reverse("two_factor:setup")
        except NoReverseMatch:
            self.setup_url = "/account/two_factor/setup/"

        # Pre-calculate the full paths for all exempt URL names
        exempt_url_names = getattr(
            settings,
            "OTP_EXEMPT_URL_NAMES",
            [
                "two_factor:login",
                "two_factor:setup",
                "two_factor:qr",
                "two_factor:setup_complete",
                "two_factor:backup_tokens",
                "logout",
            ],
        )

        for name in exempt_url_names:
            try:
                path = reverse(name)
                self.exempt_paths.add(path)
            except NoReverseMatch:
                logger.warning(
                    "RequireOTPVerificationMiddleware: URL name '%s' could not be reversed.",
                    name,
                )

        logger.info("RequireOTPVerificationMiddleware initialized. Exempt paths: %s", self.exempt_paths)

    def __call__(self, request):
        """
        Process each request to enforce OTP verification.
        """
        # Allow anonymous users and fully authenticated/verified users
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Check if user is verified (django-otp adds is_verified method)
        if hasattr(request.user, "is_verified") and request.user.is_verified():
            return self.get_response(request)

        # User is authenticated but not verified - check exemptions
        path = request.path_info

        # Check if the exact path is exempt
        if path in self.exempt_paths:
            return self.get_response(request)

        # Check if the path starts with an exempt prefix
        if path.startswith(self.exempt_prefixes):
            return self.get_response(request)

        # Check if already on setup page
        if path == self.setup_url:
            return self.get_response(request)

        # Redirect to OTP setup
        return redirect(self.setup_url)

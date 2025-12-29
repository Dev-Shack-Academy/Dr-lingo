import logging

from django.conf import settings
from django.shortcuts import redirect
from django.urls import NoReverseMatch, reverse

logger = logging.getLogger(__name__)


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

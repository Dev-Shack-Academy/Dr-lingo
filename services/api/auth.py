from rest_framework.authentication import SessionAuthentication


class OTPSessionAuthentication(SessionAuthentication):
    def authenticate(self, request):
        """
        Authenticate the request using session.

        This performs standard session authentication. OTP verification
        status is available via user.is_verified() for views that need it.

        Args:
            request (Request): Incoming DRF request.

        Returns:
            tuple or None: (user, auth) on success, None if no session.
        """
        # Perform standard session-based authentication
        user_auth_tuple = super().authenticate(request)
        if user_auth_tuple is None:
            return None

        # Return user - OTP status can be checked by views if needed
        return user_auth_tuple

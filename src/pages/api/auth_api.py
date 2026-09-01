"""
src/pages/api/auth_api.py

API client for the /api/auth endpoints of the Geo Travel backend
(login, logout, and token refresh).

Unlike the other API page objects in this package, ``AuthAPI`` does more
than build a request and hand back the raw response: ``login()`` also
inspects the response (via ``TokenExtractor``) to pull out an auth token
- wherever the backend put it, cookies or response body - and stores it
on the shared session via ``BaseAPI.set_auth_token()`` so that any other
API client reusing this session goes out authenticated afterwards.
"""

import os
from ...core.base_api import BaseAPI
from ...utils.token_extractor import TokenExtractor

class AuthAPI(BaseAPI):
    """API client for the /api/auth resource.

    All methods hit endpoints under the ``/api/auth/*`` prefix. This is
    the one API page object in the package responsible for establishing
    and tearing down authentication for the shared ``requests.Session``
    (see ``BaseAPI.set_auth_token``); the other API clients assume a
    token has already been set via this class before they're used.
    """

    def __init__(self):
        super().__init__()
        self.token_extractor = TokenExtractor()
        self.token_source = None

    def login(self, email=None, password=None):
        """Log in and, on success, extract and store the auth token.

        POST /api/auth/login

        If a token is found in the response (cookies or response body),
        it is validated and then set on the session via
        ``self.set_auth_token()`` so subsequent requests made through
        this session are authenticated. Failures to find/validate a
        token are logged but do not raise - callers should check
        ``response.status_code`` / ``self.auth_token`` themselves.

        Args:
            email (str, optional): Login email. If omitted (along with
                ``password``), credentials are pulled from environment
                variables via ``get_api_credentials_from_env()``.
            password (str, optional): Login password. See ``email``.

        Returns:
            requests.Response: The raw response from the login request.
        """
        endpoint = "/api/auth/login"

        if email is None or password is None:
            email, password = self.get_api_credentials_from_env()

        payload = {"email": email, "password": password}
        self.logger.info(f"Attempting login with email: {email}")

        response = self.post(endpoint, json=payload)

        if response.status_code == 200:
            token, extraction_method = self.token_extractor.extract_token(response)

            if token:
                is_valid = self.token_extractor.validate_token(token)
                self.token_extractor.log_extraction_attempt(token, extraction_method, is_valid)

                if is_valid:
                    # Determine token source dynamically
                    if extraction_method == "cookies":
                        self.token_source = "cookies"
                    else:  # response_body or headers
                        self.token_source = "response_body"

                    self.set_auth_token(token, token_source=self.token_source)
                    self.logger.success(f"✅ Login successful - token set via {extraction_method}")
                else:
                    self.logger.warning(f"⚠️ Token extracted via {extraction_method} but validation failed")
            else:
                self.logger.warning("❌ Login successful (200) but no token found")

        return response

    def logout(self, refresh_token):
        """Log out by invalidating a refresh token.

        POST /api/auth/logout

        Args:
            refresh_token (str): The refresh token to invalidate.

        Returns:
            requests.Response: The raw response from the logout request.
        """
        endpoint = "/api/auth/logout"
        payload = {"refresh_token": refresh_token}
        return self.post(endpoint, json=payload)

    def get_api_credentials_from_env(self):
        """Read test login credentials from environment variables.

        Reads ``API_TEST_EMAIL`` and ``API_TEST_PASSWORD``. Used by
        ``login()`` as a fallback when no explicit credentials are
        passed in.

        Returns:
            tuple[str, str]: ``(email, password)``.

        Raises:
            ValueError: If either environment variable is missing/empty.
        """
        email = os.getenv("API_TEST_EMAIL")
        password = os.getenv("API_TEST_PASSWORD")

        if not email or not password:
            self.logger.error("API_TEST_EMAIL or API_TEST_PASSWORD not found in environment")
            raise ValueError("API credentials not configured in environment")

        self.logger.info(f"Retrieved credentials from environment for: {email}")
        return email, password

    def refresh_token(self):
        """Request a new access token using the current session's refresh cookie/token.

        POST /api/auth/refresh

        Returns:
            requests.Response: The raw response from the refresh request.
        """
        return self.post("/api/auth/refresh")

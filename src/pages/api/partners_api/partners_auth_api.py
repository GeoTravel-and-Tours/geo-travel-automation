# src/pages/api/partners_api/partners_auth_api.py

"""API client for the Partners (B2B) ``/api/auth`` endpoints.

Targets the Partners API surface (its own base URL and auth scheme via
``PartnersBaseAPI``), not the retail API. Covers partner-organization
signup, login (with dynamic bearer-token extraction), email verification,
and password reset/forgot-password.
"""

import os
from src.core.partners_base_api import PartnersBaseAPI
from src.utils.token_extractor import TokenExtractor

class PartnersAuthAPI(PartnersBaseAPI):
    """Client for the Partners ``/api/auth`` resource (and the API root).

    Endpoint paths are held in ``self.endpoints`` (built in ``__init__``),
    mostly sharing the ``/api/auth`` prefix. All methods return the raw
    ``requests.Response`` from ``PartnersBaseAPI``.
    """

    def __init__(self):
        super().__init__()
        self.token_extractor = TokenExtractor()
        self.endpoints = {
            'welcome': '/api',
            'signup': '/api/auth/signup',
            'login': '/api/auth/login',
            'verify_email': '/api/auth/verify-email',
            'resend_verification': '/api/auth/resend-verification-email',
            'forgot_password': '/api/auth/forgot-password',
            'reset_password': '/api/auth/reset-password'
        }

    def get_welcome(self):
        """Fetch the API root/welcome message.

        GET /api

        Useful as a lightweight connectivity/health check against the
        Partners API base URL.

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        return self.get(self.endpoints['welcome'])

    def signup(self, org_data):
        """Register a new partner organization.

        POST /api/auth/signup

        Args:
            org_data (dict): Organization signup payload (e.g. name,
                email, password, contact details).

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        return self.post(self.endpoints['signup'], json=org_data)

    def login(self, credentials):
        """Log a partner organization in and, on success, store the auth token.

        POST /api/auth/login

        On a 200 response, attempts to extract an auth token from the
        response (cookies, body, or headers - see ``TokenExtractor``),
        validates it, and if valid stores it via ``set_auth_token`` so
        subsequent requests on this client are authenticated. If no token
        is found, this is treated as a possible "not yet verified" account
        rather than an error, and is only logged at debug level.

        Args:
            credentials (dict): Login payload, typically email/password.

        Returns:
            requests.Response: Raw response from the Partners API,
                regardless of whether a token was successfully extracted.
        """
        response = self.post(self.endpoints['login'], json=credentials)

        if response.status_code == 200:
            # Use TokenExtractor for dynamic token extraction
            token, extraction_method = self.token_extractor.extract_token(response)

            if token:
                is_valid = self.token_extractor.validate_token(token)
                self.token_extractor.log_extraction_attempt(token, extraction_method, is_valid)

                if is_valid:
                    self.set_auth_token(token)
                    self.logger.success(f"✅ Login successful - token set via {extraction_method}")
            else:
                self.logger.debug("Login successful (200) but no token found (may not be verified user)")

        return response

    def verify_email(self, token):
        """Verify a partner account's email address.

        POST /api/auth/verify-email

        Args:
            token (str): Email verification token (e.g. from a
                verification link).

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        return self.post(self.endpoints['verify_email'], json={'token': token})

    def resend_verification(self, email):
        """Resend the email verification message.

        POST /api/auth/resend-verification-email

        Args:
            email (str): Email address to resend the verification link to.

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        return self.post(self.endpoints['resend_verification'], json={'email': email})

    def forgot_password(self, email):
        """Request a password-reset email for a partner account.

        POST /api/auth/forgot-password

        Args:
            email (str): Email address of the account.

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        return self.post(self.endpoints['forgot_password'], json={'email': email})

    def reset_password(self, token, new_password):
        """Reset a partner account's password using a reset token.

        POST /api/auth/reset-password

        Args:
            token (str): Password reset token (e.g. from a reset link).
            new_password (str): New password to set.

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        return self.post(self.endpoints['reset_password'], json={
            'token': token,
            'newPassword': new_password
        })
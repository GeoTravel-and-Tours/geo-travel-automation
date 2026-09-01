"""Superclass for the main (retail) API test clients.

Wraps a ``requests.Session`` configured for the retail API base URL
(see ``EnvironmentConfig.get_api_base_url``) and provides:

- ``set_auth_token``: attaches an auth token to outgoing requests,
  either as a ``Cookie`` header or an ``Authorization: Bearer`` header
  depending on where the token came from.
- ``get``/``post``/``put``/``patch``/``delete``: thin verb-specific
  wrappers around ``_request``, which does the actual HTTP call with
  retry logic and logging.

Subclasses (page-object-style API clients under ``src/pages/api/``)
call these methods directly; they are expected to set
``self.base_url``-relative endpoints and rely on this class for
session/header/retry plumbing rather than re-implementing it.
"""

import requests
import json
from pathlib import Path
from datetime import datetime
from src.utils.logger import GeoLogger
from src.utils.token_extractor import TokenExtractor
from configs.environment import EnvironmentConfig

class BaseAPI:
    """Base class for retail-API test clients built on ``requests``.

    Holds a shared ``requests.Session`` (``self.session``), the
    resolved API base URL (``self.base_url``), the current auth token
    (``self.auth_token``) plus which channel it was set through
    (``self.token_source``, set lazily by ``set_auth_token``), the
    default headers dict merged into every request (``self.headers``),
    a ``GeoLogger`` (``self.logger``), and a ``TokenExtractor`` helper
    (``self.token_extractor``) that subclasses use to pull tokens out
    of login responses.

    After a successful request, ``self.last_response`` holds the raw
    ``requests.Response`` for callers/tests that want to inspect it
    directly instead of relying only on the returned value.
    """

    def __init__(self):
        """Initialize the session, default headers, logger, and token extractor.

        Resolves ``self.base_url`` from ``EnvironmentConfig`` for the
        currently configured test environment (dev/qa/staging/production).
        """
        self.base_url = EnvironmentConfig.get_api_base_url()
        self.session = requests.Session()
        self.auth_token = None
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Client-Type': 'retail'
        }
        self.logger = GeoLogger(self.__class__.__name__)
        self.token_extractor = TokenExtractor()

    def set_auth_token(self, token, token_source="cookies"):
        """Attach an auth token to future requests, via header or cookie.

        The two ``token_source`` values are mutually exclusive on the
        headers dict: only one of ``Cookie``/``Authorization`` is kept
        at a time, since the previous one is popped before the new one
        is added (an app that saw both might get confused about which
        session it should honor).

        Args:
            token (str): The auth token value.
            token_source (str): Where the token came from - "cookies"
                (token was read from a ``Set-Cookie`` response header,
                so it's replayed via a ``Cookie`` request header) or
                "response_body" (token was in a JSON response body, so
                it's sent via an ``Authorization: Bearer`` header).
                Defaults to "cookies".

        Returns:
            None. Silently no-ops (after logging a warning) if
            ``token`` is falsy or not a string, rather than raising.
        """
        if not token or not isinstance(token, str):
            self.logger.warning("⚠️ Invalid token provided to set_auth_token()")
            return

        self.auth_token = token
        self.token_source = token_source  # Store where token came from

        if token_source == "cookies":
            # Token came from cookies - use Cookie header
            self.headers['Cookie'] = f'retail_access_token={token}'
            # Remove Authorization header if it exists
            self.headers.pop('Authorization', None)
            self.logger.info(f"✅ Auth token set from cookies (Cookie header)")

        elif token_source == "response_body":
            # Token came from response body - use Authorization header
            self.headers['Authorization'] = f'Bearer {token}'
            # Remove Cookie header if it exists
            self.headers.pop('Cookie', None)
            self.logger.info(f"✅ Auth token set from response body (Authorization header)")

        # Always set session cookie as backup, regardless of token_source,
        # so requests that rely on session cookies still work even when
        # the primary channel is the Authorization header.
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.base_url or '')
            domain = parsed.hostname if parsed.hostname else None
            if domain:
                self.session.cookies.set('retail_access_token', token, domain=domain, path='/')
            else:
                self.session.cookies.set('retail_access_token', token)
        except Exception as e:
            self.logger.debug(f"Could not set session cookie: {e}")

    def _request(self, method, endpoint, **kwargs):
        """Send an HTTP request against ``{base_url}{endpoint}`` with retries.

        Merges ``self.headers`` with any per-call ``headers`` kwarg
        (per-call values win), forces a 30s timeout, and retries up to
        3 times on any exception raised by ``session.request`` (e.g.
        connection errors), re-raising the last exception if all
        attempts fail. On success, stores the response on
        ``self.last_response`` in addition to returning it, so callers
        (and test fixtures) can inspect the most recent response
        without threading it through every call site.

        NOTE: the "DEBUG" log lines below log the full outgoing header
        dict (including any ``Authorization``/``Cookie`` values holding
        live auth tokens) at INFO level on every request. This is
        useful for troubleshooting but means tokens end up in plain
        text in logs/CI output - worth tightening (e.g. redact or drop
        to DEBUG level) before relying on these logs anywhere sensitive.

        FIXME: the "Authorization header snuck in" safety check below
        guards on ``self._debug_token_source``, but that attribute is
        never set anywhere in this class (``set_auth_token`` sets
        ``self.token_source``, not ``self._debug_token_source``). As
        written, ``hasattr(self, '_debug_token_source')`` is always
        False, so this check never fires even when it should.

        Args:
            method (str): HTTP method, e.g. "GET", "POST".
            endpoint (str): Path appended to ``self.base_url`` to form
                the request URL.
            **kwargs: Extra keyword arguments forwarded to
                ``requests.Session.request`` (e.g. ``json``, ``params``,
                ``headers``). A ``headers`` entry, if present, is popped
                out and merged over the default headers rather than
                passed straight through.

        Returns:
            requests.Response: The response from the final successful
            attempt.

        Raises:
            Exception: Re-raises whatever exception ``session.request``
                raised on the 3rd (final) attempt.
        """
        url = f"{self.base_url}{endpoint}"

        # DEBUG: Log what's coming in
        self.logger.info(f"🔍 _request START - Current self.headers: {self.headers}")
        self.logger.info(f"🔍 _request - kwargs headers: {kwargs.get('headers', {})}")

        headers = self.headers.copy()
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))

        # DEBUG: Log final headers
        self.logger.info(f"🔍 _request FINAL headers being sent: {headers}")

        # Check if Authorization header snuck in
        if 'Authorization' in headers and hasattr(self, '_debug_token_source') and self._debug_token_source == "cookies":
            self.logger.error(f"❌ CRITICAL: Authorization header present when token_source is cookies!")
            self.logger.error(f"❌ Headers: {headers}")
            self.logger.error(f"❌ Stack trace:", exc_info=True)

        self.logger.info(f"API Request: {method} {url}")
        kwargs['timeout'] = 30

        for attempt in range(3):
            try:
                response = self.session.request(method, url, headers=headers, **kwargs)
                self.last_response = response

                if response is None:
                    raise ValueError("API response is None")

                self.logger.info(f"API Response: {response.status_code}")
                self.logger.debug(f"Response text: {response.text}")
                return response

            except Exception as e:
                # Swallow and retry up to 2 more times; only the last
                # attempt's exception propagates to the caller.
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    self.logger.error("Max retries reached. Raising exception.")
                    raise
                self.logger.info("Retrying...")

    def get(self, endpoint, **kwargs):
        """Send a GET request. See ``_request`` for shared behavior/kwargs."""
        return self._request('GET', endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        """Send a POST request. See ``_request`` for shared behavior/kwargs."""
        return self._request('POST', endpoint, **kwargs)

    def put(self, endpoint, **kwargs):
        """Send a PUT request. See ``_request`` for shared behavior/kwargs."""
        return self._request('PUT', endpoint, **kwargs)

    def patch(self, endpoint, **kwargs):
        """Send a PATCH request. See ``_request`` for shared behavior/kwargs."""
        return self._request('PATCH', endpoint, **kwargs)

    def delete(self, endpoint, **kwargs):
        """Send a DELETE request. See ``_request`` for shared behavior/kwargs."""
        return self._request('DELETE', endpoint, **kwargs)
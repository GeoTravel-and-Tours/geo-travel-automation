"""Superclass for Partners API test clients (corporate/B2B API surface).

Parallels ``src/core/base_api.py`` (``BaseAPI``) but targets the
separate Partners API base URL (see
``EnvironmentConfig.get_partners_api_base_url``), always authenticates
via an ``Authorization: Bearer`` header (no cookie-based token
support), uses a longer default timeout, and dumps failed (4xx/5xx)
response bodies to disk under ``reports/failed_responses/`` for
troubleshooting.

NOTE: this class duplicates most of ``BaseAPI``'s structure (session
setup, headers dict, verb methods) rather than sharing a common
ancestor - the two have drifted independently (e.g. retry semantics
differ between ``BaseAPI._request`` and this class's
``_request_with_retry``). Worth consolidating if both are maintained
going forward.
"""

import requests
import time
import json
from datetime import datetime
from src.utils.logger import GeoLogger
from src.utils.token_extractor import TokenExtractor
from configs.environment import EnvironmentConfig

class PartnersBaseAPI:
    """Base class for Partners (corporate) API test clients.

    Holds a ``requests.Session`` (``self.session``), the Partners API
    base URL (``self.base_url``), the current auth token
    (``self.auth_token``), the default headers dict merged into every
    request (``self.headers``, tagged ``X-Client-Type: corporate``), a
    ``GeoLogger`` (``self.logger``), a ``TokenExtractor`` helper
    (``self.token_extractor``), and a default request timeout
    (``self.timeout``, currently unused directly by ``_request`` -
    see ``_request_with_retry``, which instead reads
    ``EnvironmentConfig.API_CONNECT_TIMEOUT``/``API_READ_TIMEOUT``).

    After each request, ``self.last_response`` holds the raw
    ``requests.Response`` so callers (including ``conftest.py``
    fixtures) can inspect it directly.
    """
    def __init__(self):
        """Initialize the session, default headers, logger, and token extractor."""
        self.base_url = EnvironmentConfig.get_partners_api_base_url()
        self.session = requests.Session()
        self.auth_token = None
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Client-Type': 'corporate'
        }
        self.logger = GeoLogger(self.__class__.__name__)
        self.token_extractor = TokenExtractor()
        # Increased from the 30s used by BaseAPI - Partners API endpoints
        # have been observed to take longer to respond.
        self.timeout = 60

    def set_auth_token(self, token):
        """Attach a Bearer auth token to future Partners API requests.

        Unlike ``BaseAPI.set_auth_token``, this always uses the
        ``Authorization: Bearer`` header - there is no cookie-based
        option for the Partners API client.

        Args:
            token (str): The auth token value.

        Returns:
            None. Silently no-ops (after logging a warning) if
            ``token`` is falsy or not a string, rather than raising.
        """
        if not token or not isinstance(token, str):
            self.logger.warning("⚠️ Invalid token provided to set_auth_token()")
            return

        self.auth_token = token
        self.headers['Authorization'] = f'Bearer {token}'
        self.logger.info(f"✅ Auth token set (length: {len(token)})")

    def _request_with_retry(self, method, endpoint, max_retries=3, **kwargs):
        """Send an HTTP request against the Partners API with retry handling.

        Merges ``self.headers`` with any per-call ``headers`` kwarg,
        applies the configured connect/read timeouts (unless the
        caller already passed one), and on 4xx/5xx responses dumps the
        response body to ``reports/failed_responses/`` for later
        troubleshooting (falling back to a plain log line if the dump
        itself fails, e.g. due to filesystem permissions).

        Retry behavior differs by failure type:
        - ``ReadTimeout``/``ConnectTimeout``: retried with exponential
          backoff (1s, 2s, 4s, ...) up to ``max_retries`` attempts,
          re-raising the last timeout once attempts are exhausted.
        - ``ConnectionError``/``ChunkedEncodingError``: retried with
          linear backoff (5s, 10s, 15s, ...). NOTE: on the final
          attempt this branch does not re-raise or return - it just
          logs and lets the loop end, so exhausting retries on one of
          these errors makes this method return ``None`` instead of
          raising. ``_request`` (below) treats a ``None`` response as
          a generic ``ValueError``, so the original exception/traceback
          is lost in that case.

        FIXME: ``ReadTimeout`` is listed in both ``except`` clauses
        above; since the first matching ``except`` wins, a
        ``ReadTimeout`` is always handled by the first branch and the
        mention of it in the second tuple is dead code.

        Args:
            method (str): HTTP method, e.g. "GET", "POST".
            endpoint (str): Path appended to ``self.base_url``.
            max_retries (int): Maximum number of attempts. Defaults to 3.
            **kwargs: Extra keyword arguments forwarded to
                ``requests.Session.request``.

        Returns:
            requests.Response | None: The response from the first
            successful attempt, or ``None`` if retries were exhausted
            on a connection/chunked-encoding error (see NOTE above).

        Raises:
            requests.exceptions.ReadTimeout: Re-raised if every attempt
                times out.
            requests.exceptions.ConnectTimeout: Re-raised if every
                attempt fails to connect in time.
        """
        url = f"{self.base_url}{endpoint}"

        # Merge headers
        headers = self.headers.copy()
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))

        # Set timeout using EnvironmentConfig
        kwargs.setdefault('timeout', (EnvironmentConfig.API_CONNECT_TIMEOUT, EnvironmentConfig.API_READ_TIMEOUT))

        self.logger.info(f"Partners API Request: {method} {url}")

        last_exception = None

        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs
                )

                # Store last response for conftest.py to access
                self.last_response = response

                self.logger.info(f"Partners API Response: {response.status_code}")

                # Log response for debugging
                if response.status_code >= 400:
                    # Save response dump for troubleshooting
                    try:
                        from pathlib import Path
                        dump_dir = Path("reports/failed_responses")
                        dump_dir.mkdir(parents=True, exist_ok=True)
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_endpoint = endpoint.strip('/').replace('/', '_') or 'root'
                        dump_file = dump_dir / f"{ts}_{response.status_code}_{safe_endpoint}.txt"
                        with open(dump_file, 'w', encoding='utf-8') as df:
                            df.write(response.text or response.content.decode('utf-8', errors='replace'))
                        self.logger.warning(f"Partners API Error: {response.status_code} - saved dump: {dump_file}")
                    except Exception:
                        self.logger.warning(f"Partners API Error: {response.status_code} - {response.text}")

                return response

            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout) as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    self.logger.warning(
                        f"⏳ Timeout on attempt {attempt + 1}/{max_retries} for {endpoint}, "
                        f"retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"❌ All {max_retries} attempts failed for {endpoint}")
                    raise last_exception

            except (requests.exceptions.ConnectionError,
        requests.exceptions.ChunkedEncodingError,
        requests.exceptions.ReadTimeout) as e:
                # Linear backoff (5s, 10s, 15s...). Note: does not raise
                # or return on the final attempt - see method docstring.
                wait_time = 5 * (attempt + 1)  # 5s, 10s, 15s
                self.logger.warning(f"Server connection issue, retry in {wait_time}s...")
                time.sleep(wait_time)
                self.logger.error(f"Partners API Request failed: {str(e)}")

    def _request(self, method, endpoint, **kwargs):
        """Send a request via ``_request_with_retry`` and guard against ``None``.

        Args:
            method (str): HTTP method, e.g. "GET", "POST".
            endpoint (str): Path appended to ``self.base_url``.
            **kwargs: Forwarded to ``_request_with_retry``.

        Returns:
            requests.Response: The response, guaranteed non-None.

        Raises:
            ValueError: If ``_request_with_retry`` returned ``None``
                (retries exhausted on a connection-level error without
                raising - see that method's docstring).
        """
        # Use retry logic
        response = self._request_with_retry(method, endpoint, max_retries=3, **kwargs)
        if response is None:
            self.logger.error("Response is None. Check the request or server.")
            raise ValueError("API response is None")
        return response

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
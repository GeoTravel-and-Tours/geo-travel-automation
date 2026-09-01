# src/pages/api/partners_api/organization_api.py

"""API client for the Partners (B2B) ``/api/org`` endpoints.

Targets the Partners API surface (its own base URL and auth scheme via
``PartnersBaseAPI``), not the retail API. Covers a partner organization's
profile, API key management, and API usage reporting (aggregate, daily,
and date-range).
"""

import os
from src.core.partners_base_api import PartnersBaseAPI

class PartnersOrganizationAPI(PartnersBaseAPI):
    """Client for the Partners ``/api/org`` resource.

    Endpoint paths are held in ``self.endpoints`` (built in ``__init__``)
    rather than being hardcoded per method, all sharing the ``/api/org``
    prefix. All methods return the raw ``requests.Response`` from
    ``PartnersBaseAPI``.
    """

    def __init__(self, auth_token=None):
        """Initialize the client and optionally set an existing auth token.

        Args:
            auth_token (str, optional): Bearer token to use immediately
                (e.g. reused from a prior ``PartnersAuthAPI.login`` call),
                bypassing the need to authenticate again. Defaults to
                ``None``, in which case no auth header is set until
                ``set_auth_token`` is called.
        """
        super().__init__()
        self.auth_token = auth_token
        if auth_token:
            self.set_auth_token(auth_token)
        self.endpoints = {
            'profile': '/api/org/profile',
            'reset_api_keys': '/api/org/reset-api-keys',
            'usage': '/api/org/usage',
            'daily_usage': '/api/org/usage/daily',
            'usage_range': '/api/org/usage/range'
        }

    def get_profile(self):
        """Fetch the partner organization's profile.

        GET /api/org/profile

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        return self.get(self.endpoints['profile'])

    def reset_api_keys(self):
        """Reset (rotate) the partner organization's API keys.

        GET /api/org/reset-api-keys

        NOTE: this issues a GET even though "reset" is a mutating,
        state-changing action (rotating keys presumably invalidates the
        old ones). If the backend endpoint is actually intended to be a
        POST, this method may be using the wrong HTTP verb.

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        return self.get(self.endpoints['reset_api_keys'])

    def get_usage(self, mode='test', limit=None, page=None):
        """Fetch aggregate API usage for the organization.

        GET /api/org/usage

        Args:
            mode (str): Usage mode to query, e.g. "test" or "live".
                Defaults to "test".
            limit (int, optional): Max number of results to return. Only
                included in the query string if truthy.
            page (int, optional): Page number for pagination. Only
                included in the query string if truthy.

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        params = {'mode': mode}
        # limit/page are only added when provided, so the API's own
        # defaults apply otherwise.
        if limit: params['limit'] = limit
        if page: params['page'] = page
        return self.get(self.endpoints['usage'], params=params)

    def get_daily_usage(self, mode='test', date=None):
        """Fetch API usage for a single day.

        GET /api/org/usage/daily

        Args:
            mode (str): Usage mode to query, e.g. "test" or "live".
                Defaults to "test".
            date (str, optional): Date to query usage for. Only included
                in the query string if provided; format is whatever the
                backend expects (not validated here).

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        params = {'mode': mode}
        if date: params['date'] = date
        return self.get(self.endpoints['daily_usage'], params=params)

    def get_usage_range(self, mode='test', start_date=None, end_date=None):
        """Fetch API usage over a date range.

        GET /api/org/usage/range

        Args:
            mode (str): Usage mode to query, e.g. "test" or "live".
                Defaults to "test".
            start_date (str, optional): Start of the range. Only included
                in the query string if provided.
            end_date (str, optional): End of the range. Only included in
                the query string if provided.

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        params = {'mode': mode}
        if start_date: params['startDate'] = start_date
        if end_date: params['endDate'] = end_date
        return self.get(self.endpoints['usage_range'], params=params)
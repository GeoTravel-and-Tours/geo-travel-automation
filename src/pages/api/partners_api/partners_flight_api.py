# src/pages/api/partners_api/partners_flight_api.py

"""API client for the Partners (B2B) ``/api/flight`` endpoints.

Targets the Partners API surface (its own base URL via
``PartnersBaseAPI``), not the retail API. Unlike the other Partners
clients, flight requests are authenticated per-call via API key/secret/
app-id headers (see ``_get_flight_headers``) rather than the bearer token
set by ``PartnersBaseAPI.set_auth_token``. Covers flight search, booking,
and listing a partner's flight bookings.
"""

import os
from datetime import datetime, timedelta
from src.core.partners_base_api import PartnersBaseAPI

class PartnersFlightAPI(PartnersBaseAPI):
    """Client for the Partners ``/api/flight`` resource.

    Endpoint paths are held in ``self.endpoints`` (built in ``__init__``),
    sharing the ``/api/flight`` prefix. Search and booking calls attach
    ``x-api-key``/``x-api-secret``/``x-app-id`` headers built by
    ``_get_flight_headers``; ``get_bookings`` does not attach these
    headers and instead relies on whatever auth ``PartnersBaseAPI``
    already has configured. All methods return the raw
    ``requests.Response``.
    """

    def __init__(self, api_key=None, api_secret=None, app_id=None):
        """Initialize the client with Partners flight API credentials.

        Args:
            api_key (str, optional): Value sent as the ``x-api-key``
                header on search/booking requests.
            api_secret (str, optional): Value sent as the ``x-api-secret``
                header on search/booking requests.
            app_id (str, optional): Value sent as the ``x-app-id`` header
                on search/booking requests.
        """
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.app_id = app_id
        self.endpoints = {
            'search': '/api/flight/search',
            'book': '/api/flight/book',
            'bookings': '/api/flight/bookings'
        }

    def _get_flight_headers(self):
        """Build the API key/secret/app-id headers used for flight requests.

        Returns:
            dict: Headers including ``Content-Type``, ``Accept``,
                ``x-api-key``, ``x-api-secret``, and ``x-app-id``.
        """
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-api-key': self.api_key,
            'x-api-secret': self.api_secret,
            'x-app-id': self.app_id
        }
        redacted = dict(headers, **{'x-api-secret': '***REDACTED***'})
        self.logger.debug(f"Flight API Headers: {redacted}")
        return headers

    def search_flights(self, search_data):
        """Search for flights.

        POST /api/flight/search

        Args:
            search_data (dict): Flight search criteria (e.g. origin,
                destination, dates, passenger count).

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        headers = self._get_flight_headers()
        return self.post(self.endpoints['search'], json=search_data,
                        headers=headers)

    def book_flight(self, booking_data):
        """Book a flight.

        POST /api/flight/book

        Args:
            booking_data (dict): Flight booking payload (e.g. selected
                flight, passenger details).

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        headers = self._get_flight_headers()
        return self.post(self.endpoints['book'], json=booking_data,
                        headers=headers)

    def get_bookings(self, limit=None, page=None):
        """List the partner's flight bookings.

        GET /api/flight/bookings

        Args:
            limit (int, optional): Max number of results to return. Only
                included in the query string if truthy.
            page (int, optional): Page number for pagination. Only
                included in the query string if truthy.

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        params = {}
        if limit: params['limit'] = limit
        if page: params['page'] = page
        return self.get(self.endpoints['bookings'], params=params)

    @staticmethod
    def get_future_date(days_ahead=1):
        """Build a future date string for use in flight search payloads.

        Args:
            days_ahead (int): Number of days from today. Defaults to 1.

        Returns:
            str: Date formatted as "YYYY-MM-DD".
        """
        future_date = datetime.now() + timedelta(days=days_ahead)
        return future_date.strftime("%Y-%m-%d")
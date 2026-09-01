# src/pages/api/partners_api/partners_package_api.py

"""API client for the Partners (B2B) ``/api/package`` endpoints.

Targets the Partners API surface (its own base URL via
``PartnersBaseAPI``), not the retail API. Like ``PartnersFlightAPI``,
every request here is authenticated per-call via API key/secret/app-id
headers (see ``_get_package_headers``) rather than the bearer token set
by ``PartnersBaseAPI.set_auth_token``. Covers package listing, booking,
country listing, and a partner's package bookings.
"""

from src.core.partners_base_api import PartnersBaseAPI

class PartnersPackageAPI(PartnersBaseAPI):
    """Client for the Partners ``/api/package`` resource.

    Endpoint paths are held in ``self.endpoints`` (built in ``__init__``),
    sharing the ``/api/package`` prefix. Every method attaches the
    ``x-api-key``/``x-api-secret``/``x-app-id`` headers built by
    ``_get_package_headers`` (note: unlike ``PartnersFlightAPI``'s
    equivalent helper, these headers omit ``Content-Type``/``Accept``,
    relying on the defaults already set on ``self.headers`` by
    ``PartnersBaseAPI``). All methods return the raw ``requests.Response``.
    """

    def __init__(self, api_key=None, api_secret=None, app_id=None):
        """Initialize the client with Partners package API credentials.

        Args:
            api_key (str, optional): Value sent as the ``x-api-key``
                header on every request.
            api_secret (str, optional): Value sent as the ``x-api-secret``
                header on every request.
            app_id (str, optional): Value sent as the ``x-app-id`` header
                on every request.
        """
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.app_id = app_id
        self.endpoints = {
            'all': '/api/package/all',
            'book': '/api/package/book',
            'countries': '/api/package/countries',
            'bookings': '/api/package/bookings'
        }

    def _get_package_headers(self):
        """Get headers required for package API requests.

        Returns:
            dict: Headers containing ``x-api-key``, ``x-api-secret``, and
                ``x-app-id``.
        """
        return {
            'x-api-key': self.api_key,
            'x-api-secret': self.api_secret,
            'x-app-id': self.app_id
        }

    def get_all_packages(self, city=None, country=None, limit=None, page=None):
        """List available packages, optionally filtered.

        GET /api/package/all

        Args:
            city (str, optional): Filter by city. Only included in the
                query string if provided.
            country (str, optional): Filter by country. Only included in
                the query string if provided.
            limit (int, optional): Max number of results to return. Only
                included if truthy.
            page (int, optional): Page number for pagination. Only
                included if truthy.

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        params = {}
        if city: params['city'] = city
        if country: params['country'] = country
        if limit: params['limit'] = limit
        if page: params['page'] = page
        return self.get(self.endpoints['all'], params=params,
                        headers=self._get_package_headers())

    def book_package(self, booking_data):
        """Book a package.

        POST /api/package/book

        Args:
            booking_data (dict): Package booking payload.

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        return self.post(self.endpoints['book'], json=booking_data,
                         headers=self._get_package_headers())

    def get_package_countries(self):
        """List countries available for packages.

        GET /api/package/countries

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        return self.get(self.endpoints['countries'],
                        headers=self._get_package_headers())

    def get_package_bookings(self, limit=None, page=None):
        """List the partner's package bookings.

        GET /api/package/bookings

        Args:
            limit (int, optional): Max number of results to return. Only
                included if truthy.
            page (int, optional): Page number for pagination. Only
                included if truthy.

        Returns:
            requests.Response: Raw response from the Partners API.
        """
        params = {}
        if limit: params['limit'] = limit
        if page: params['page'] = page
        return self.get(self.endpoints['bookings'], params=params,
                        headers=self._get_package_headers())
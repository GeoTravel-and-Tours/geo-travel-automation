"""
src/pages/api/hotels_api.py

API client for the /api/hotels endpoints of the Geo Travel backend:
searching hotels, looking up supporting reference data (cities,
ratings), booking a hotel, and fetching detailed priced offers.
"""

from ...core.base_api import BaseAPI

class HotelAPI(BaseAPI):
    """Comprehensive Hotel API client for the /api/hotels resource.

    All methods hit endpoints under the ``/api/hotels/*`` prefix.
    """

    # Earlier implementation of search_hotels(), kept commented out for
    # reference. Superseded by the version below, which adds temporary
    # debug logging around header/session state; functionally the two
    # are close to equivalent (this one additionally split "page"/"limit"
    # into query params rather than sending everything in the JSON body).
    # def search_hotels(self, **params):
    #     """POST /api/hotels/search - Search for hotels"""
    #     query_params = {}
    #     if "page" in params:
    #         query_params["page"] = params["page"]
    #     if "limit" in params:
    #         query_params["limit"] = params["limit"]

    #     # Debugging: Log headers and payload
    #     headers = self.get_headers()
    #     self.logger.info(f"Request headers: {headers}")
    #     self.logger.info(f"Request payload: {params}")

    #     return self.post("/api/hotels/search", params=query_params, json=params)

    def search_hotels(self, **kwargs):
        """Search for hotels.

        POST /api/hotels/search

        Includes verbose debug logging (current headers, whether they've
        drifted from ``self._debug_original_headers`` if that attribute
        has been set elsewhere, and the headers actually placed on the
        outgoing request) to help diagnose auth-header issues seen with
        this endpoint. To capture the latter, it temporarily monkey-patches
        ``self.session.prepare_request`` with a wrapper that logs the
        prepared request's headers, then restores the original method
        after the call.

        FIXME: the restoration of ``self.session.prepare_request`` only
        happens on the success path - if ``self.post()`` raises, the
        patched ``debug_prepare_request`` wrapper is left in place on
        the session permanently (no try/finally around the call).

        Args:
            **kwargs: Search criteria (e.g. destination, dates, guest
                counts) sent as the JSON request body.

        Returns:
            requests.Response: The raw response from the request.
        """
        # DEBUG: Check headers at method start
        self.logger.info(f"🔍 search_hotels START - Current headers: {self.headers}")

        # Check if headers changed from original
        if hasattr(self, '_debug_original_headers'):
            if self.headers != self._debug_original_headers:
                self.logger.error(f"❌ HEADERS CHANGED! Original: {self._debug_original_headers}")
                self.logger.error(f"❌ Current: {self.headers}")
                # Find what changed
                for key in set(self.headers.keys()) | set(self._debug_original_headers.keys()):
                    if self.headers.get(key) != self._debug_original_headers.get(key):
                        self.logger.error(f"❌ Header '{key}' changed from '{self._debug_original_headers.get(key)}' to '{self.headers.get(key)}'")

        # Make the request but log what's being sent
        self.logger.info(f"🔍 Making request to /api/hotels/search with headers: {self.headers}")

        # Try to capture what's actually being sent at the session level
        original_prep = self.session.prepare_request

        def debug_prepare_request(request):
            self.logger.info(f"🔍 SESSION - Prepared request headers: {request.headers}")
            return original_prep(request)

        self.session.prepare_request = debug_prepare_request

        response = self.post("/api/hotels/search", json=kwargs)

        # Restore original method
        self.session.prepare_request = original_prep

        # DEBUG: Check headers after request
        self.logger.info(f"🔍 search_hotels END - Headers after request: {self.headers}")

        return response

    def get_hotel_cities(self, **params):
        """Get the list of hotel cities.

        GET /api/hotels/cities

        Args:
            **params: Arbitrary query parameters (e.g. country filter)
                forwarded as-is to the request's query string.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.get("/api/hotels/cities", params=params)

    def get_hotel_rating(self, **params):
        """Get hotel rating data.

        GET /api/hotels/rating

        Args:
            **params: Arbitrary query parameters (e.g. hotel id)
                forwarded as-is to the request's query string.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.get("/api/hotels/rating", params=params)

    def book_hotel(self, **params):
        """Book a hotel.

        POST /api/hotels/book

        Args:
            **params: Booking payload (e.g. hotel/room/rate id,
                guest details) sent as the JSON request body.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.post("/api/hotels/book", json=params)

    def get_hotel_offers(self, **params):
        """Get detailed hotel offers with pricing.

        POST /api/hotels/offer

        Key features:
        - Returns hotel details with room offers
        - Includes currency conversion when requested currency differs
        - Adds requestedCurrencyTotalPrice and currencyConversion fields

        NOTE: this method's original docstring referenced the endpoint
        as "/api/hotels/offerReq", but the code actually posts to
        "/api/hotels/offer" - flagging in case that's a leftover typo
        from a rename rather than the intended path.

        Args:
            **params: Offer request payload (e.g. hotel id, room
                selection, requested currency) sent as the JSON request
                body.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.post("/api/hotels/offer", json=params)

    def get_headers(self):
        """Build a headers dict for API requests (not used by self.get/post).

        NOTE: this constructs its own headers dict rather than using
        ``self.headers`` (set up in ``BaseAPI.__init__``); it also uses
        the key "Client-Type" here versus "X-Client-Type" in
        ``self.headers``. ``self.get``/``self.post``/etc. (via
        ``BaseAPI._request``) always send ``self.headers``, not this
        method's output, so ``get_headers()`` appears to only be used
        by the commented-out legacy ``search_hotels`` above and by
        external debugging/tests - not by any live request path in this
        class.

        Returns:
            dict: Headers with Content-Type/Accept/Client-Type, plus
                Authorization (Bearer token) if ``self.auth_token`` is
                set.
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Client-Type": "retail"
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

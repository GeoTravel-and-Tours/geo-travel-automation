"""
src/pages/api/flight_api.py

API client for the /api/flight endpoints of the Geo Travel backend
covering the flight search/booking flow: submitting a search, polling
for results, initiating and inspecting bookings, quoting, and
validating passenger emails.

(See flight_utils_api.py for the separate airports/airlines reference
data endpoints.)
"""

from ...core.base_api import BaseAPI

class FlightAPI(BaseAPI):
    """API client for the /api/flight resource (search, booking, quotes).

    All methods hit endpoints under the ``/api/flight/*`` prefix.
    Query parameters are passed via ``params=`` to ``self.get`` (rather
    than interpolated into the endpoint string) so ``requests`` handles
    URL-encoding.
    """

    def search_request(self, search_data):
        """Submit a flight search.

        POST /api/flight/search-request

        Args:
            search_data (dict): Search criteria (e.g. origin,
                destination, dates, passenger counts) sent as the JSON
                request body.

        Returns:
            requests.Response: The raw response from the request.
        """
        endpoint = "/api/flight/search-request"
        return self.post(endpoint, json=search_data)

    def get_search_results(self, search_id):
        """Fetch results for a previously submitted flight search.

        GET /api/flight/search

        Args:
            search_id: Identifier returned by ``search_request()``,
                passed as the ``search_id`` query parameter.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.get("/api/flight/search", params={"search_id": search_id})

    def initiate_booking(self, booking_data):
        """Start a flight booking.

        POST /api/flight/initiate-booking

        Args:
            booking_data (dict): Booking payload (e.g. selected flight,
                passenger details) sent as the JSON request body.

        Returns:
            requests.Response: The raw response from the request.
        """
        endpoint = "/api/flight/initiate-booking"
        return self.post(endpoint, json=booking_data)

    def get_booked_flights(self, limit=10, page=1, category="Upcoming"):
        """List the current user's booked flights.

        GET /api/flight/user/booked-flights

        Args:
            limit (int): Max number of results per page. Defaults to 10.
            page (int): Page number to fetch. Defaults to 1.
            category (str): Booking category filter (e.g. "Upcoming").
                Defaults to "Upcoming".

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.get(
            "/api/flight/user/booked-flights",
            params={"limit": limit, "page": page, "category": category},
        )

    def create_quote(self, quote_data):
        """Create a flight quote.

        POST /api/flight/quote

        Args:
            quote_data (dict): Quote payload sent as the JSON request
                body.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.post("/api/flight/quote", json=quote_data)

    def get_quote(self, reference):
        """Fetch a previously created flight quote.

        GET /api/flight/quote

        Args:
            reference: Quote reference, passed as the ``reference``
                query parameter.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.get("/api/flight/quote", params={"reference": reference})

    def validate_passenger_email(self, passenger_data):
        """Validate a passenger's email address.

        POST /api/flight/validate-passenger-email

        Args:
            passenger_data (dict): Passenger info (at least the email
                to validate) sent as the JSON request body.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.post("/api/flight/validate-passenger-email", json=passenger_data)

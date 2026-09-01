"""
src/pages/api/flight_utils_api.py

API client for the Geo Travel backend's flight reference-data endpoints
(the static/lookup lists of airports and airlines used to populate
flight search forms), as opposed to flight_api.py which covers the
actual search/booking flow.
"""

from ...core.base_api import BaseAPI

class FlightUtilsAPI(BaseAPI):
    """API client for flight reference-data resources (airports, airlines).

    Endpoints live under ``/api/flight/airports`` and
    ``/api/flight/airlines``.
    """

    def get_all_airports(self):
        """List all airports.

        GET /api/flight/airports/all

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.get("/api/flight/airports/all")

    def get_all_airlines(self):
        """List all airlines.

        GET /api/flight/airlines/all

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.get("/api/flight/airlines/all")

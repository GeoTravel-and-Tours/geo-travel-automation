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

    def search_hotels(self, **kwargs):
        """Search for hotels.

        POST /api/hotels/search

        Args:
            **kwargs: Search criteria (e.g. destination, dates, guest
                counts) sent as the JSON request body.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.post("/api/hotels/search", json=kwargs)

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

        Args:
            **params: Offer request payload (e.g. hotel id, room
                selection, requested currency) sent as the JSON request
                body.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.post("/api/hotels/offer", json=params)

"""
src/pages/api/commercial_deals_api.py

API client for the /api/commercial endpoints of the Geo Travel backend:
browsing commercial deals, booking one, verifying its payment, and
listing existing bookings.
"""

from ...core.base_api import BaseAPI

class CommercialAPI(BaseAPI):
    """API client for the /api/commercial resource (commercial deals).

    All methods hit endpoints under the ``/api/commercial/*`` prefix.
    """

    def get_all_deals(self, **params):
        """List commercial deals.

        GET /api/commercial/all

        Args:
            **params: Arbitrary query parameters (e.g. pagination,
                filters) forwarded as-is to the request's query string.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.get("/api/commercial/all", params=params)

    def get_single_deal(self, deal_id):
        """Fetch a single commercial deal by id.

        GET /api/commercial/{id}

        Args:
            deal_id: Identifier of the deal to fetch.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.get(f"/api/commercial/{deal_id}")

    def book_commercial(self, booking_data):
        """Create a booking for a commercial deal.

        POST /api/commercial/book

        Args:
            booking_data (dict): Booking payload (e.g. deal id,
                traveller details) sent as the JSON request body.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.post("/api/commercial/book", json=booking_data)

    def verify_payment(self, invoice_id, transaction_id):
        """Verify payment for a commercial deal booking.

        GET /api/commercial/book/verify/{invoiceId}/{transaction_id}

        Args:
            invoice_id: Invoice identifier for the booking.
            transaction_id: Transaction identifier returned by the
                payment provider.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.get(f"/api/commercial/book/verify/{invoice_id}/{transaction_id}")

    def get_all_bookings(self, **params):
        """List commercial deal bookings.

        GET /api/commercial/book/all

        Args:
            **params: Arbitrary query parameters (e.g. pagination,
                filters) forwarded as-is to the request's query string.

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.get("/api/commercial/book/all", params=params)

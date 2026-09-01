# src/pages/api/price_api.py

"""API client for the retail ``/api/price/voucher`` endpoints.

Covers looking up a discount voucher by code and applying one to a
price/booking.
"""

from ...core.base_api import BaseAPI

class PriceAPI(BaseAPI):
    """Client for the ``/api/price/voucher`` resource.

    Both methods are thin wrappers around ``BaseAPI`` and return the raw
    ``requests.Response``.
    """

    def apply_voucher(self, voucher_data):
        """Apply a voucher/discount code to a booking or price.

        POST /api/price/voucher/apply

        Args:
            voucher_data (dict): Payload identifying the voucher and the
                booking/price it should be applied to.

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.post("/api/price/voucher/apply", json=voucher_data)

    def get_voucher(self, code):
        """Look up a voucher by its code.

        GET /api/price/voucher/{code}

        Args:
            code (str): Voucher code to look up.

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.get(f"/api/price/voucher/{code}")
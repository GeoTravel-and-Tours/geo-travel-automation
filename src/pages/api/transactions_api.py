# src/pages/api/transaction_api.py

"""API client for the retail ``/api/transactions`` endpoints.

Covers listing a user's transactions, fetching transaction insights, and
exporting transactions to CSV.
"""

from ...core.base_api import BaseAPI

class TransactionAPI(BaseAPI):
    """Client for the ``/api/transactions`` resource.

    All methods are GET requests scoped to the current user
    (``/api/transactions/user...``) and return the raw
    ``requests.Response``.
    """

    def get_user_transactions(self, **params):
        """List the current user's transactions.

        GET /api/transactions/user

        Args:
            **params: Optional query string parameters (e.g. filters,
                pagination) forwarded as-is.

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.get("/api/transactions/user", params=params)

    def get_transaction_insights(self):
        """Fetch summary insights for the current user's transactions.

        GET /api/transactions/user/insights

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.get("/api/transactions/user/insights")

    def export_transactions(self):
        """Export the current user's transactions as CSV.

        GET /api/transactions/user/export-to-csv

        Returns:
            requests.Response: Raw response from the API. The exported
                CSV content is expected in the response body.
        """
        return self.get("/api/transactions/user/export-to-csv")
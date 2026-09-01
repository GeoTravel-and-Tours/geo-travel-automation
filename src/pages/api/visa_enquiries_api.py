# src/pages/api/visa_enquiries_api.py

"""API client for the retail ``/api/visa`` endpoints.

Covers creating a visa enquiry, paying for it, verifying that payment,
and looking up a user's visa applications.
"""

from ...core.base_api import BaseAPI
from configs.environment import EnvironmentConfig

class VisaEnquiryAPI(BaseAPI):
    """Client for the ``/api/visa`` resource (visa enquiries/applications).

    Most methods are thin wrappers around ``BaseAPI`` and return the raw
    ``requests.Response``; ``verify_payment_link`` is the exception (see
    its docstring).
    """

    def create_visa_enquiry(self, visa_data):
        """Create a new visa enquiry.

        POST /api/visa/create

        Args:
            visa_data (dict): Visa enquiry payload (e.g. applicant and
                travel details).

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.post("/api/visa/create", json=visa_data)

    def make_payment(self, payment_data):
        """Initiate payment for a visa enquiry.

        POST /api/visa/payment

        Args:
            payment_data (dict): Payment payload (e.g. visa enquiry id,
                amount, payment method).

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.post("/api/visa/payment", json=payment_data)

    def verify_payment(self, invoice_id, transaction_id):
        """Verify a visa enquiry payment.

        GET /api/visa/verify/{invoiceId}/{transaction_id}

        Args:
            invoice_id: Invoice ID returned when the payment was created.
            transaction_id: Transaction ID returned by the payment
                provider.

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.get(f"/api/visa/verify/{invoice_id}/{transaction_id}")

    def get_user_visa_applications(self, **params):
        """List the current user's own visa applications.

        GET /api/visa/all/user

        Args:
            **params: Optional query string parameters (e.g. filters,
                pagination) forwarded as-is.

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.get("/api/visa/all/user", params=params)

    def get_visa_application_by_id(self, visa_application_id):
        """Fetch a specific visa application by ID.

        GET /api/visa

        Unlike most "by id" lookups elsewhere in this codebase, the ID is
        passed as a query parameter (``visa_application_id``) rather than
        as a path segment (e.g. ``/api/visa/{id}``).

        Args:
            visa_application_id: ID of the visa application to fetch.

        Returns:
            requests.Response: Raw response from the API.
        """
        params = {"visa_application_id": visa_application_id}
        return self.get("/api/visa", params=params)

    def verify_payment_link(self, payment_link):
        """Check that a hosted payment link is reachable and looks valid.

        Unlike the other methods on this class, this does not go through
        ``self.get``/``BaseAPI`` - it issues a plain ``requests.get`` directly
        against ``payment_link`` (an external Flutterwave checkout URL, not
        this client's ``base_url``), so no auth headers are attached.

        Args:
            payment_link (str): Fully-qualified checkout URL to verify.

        Returns:
            tuple[bool, str]: ``(True, message)`` if the link resolves
                with a 200 status and appears to be a Flutterwave/checkout
                page; ``(False, message)`` otherwise (unexpected redirect
                target, non-200 status, or a request exception).
        """
        import requests
        try:
            response = requests.get(payment_link, timeout=EnvironmentConfig.API_TIMEOUT, allow_redirects=True)

            if response.status_code == 200:
                # Check if it's a Flutterwave page
                if 'flutterwave' in response.url or 'checkout' in response.text.lower():
                    return True, "Payment link is valid and points to Flutterwave"
                else:
                    return False, f"Payment link redirected to unexpected URL: {response.url}"
            else:
                return False, f"Payment link returned status code: {response.status_code}"

        except Exception as e:
            return False, f"Error accessing payment link: {str(e)}"
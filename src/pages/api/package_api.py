# src/pages/api/package_api.py

"""API client for the retail ``/api/package`` endpoints.

Covers package listing/detail lookup, booking a package, verifying its
payment, package "deals", and a logged-in user's booked packages and
booking analytics.
"""

from ...core.base_api import BaseAPI

class PackageAPI(BaseAPI):
    """Client for the ``/api/package`` resource family.

    Methods are grouped by sub-area (management, booking, deals, user
    booked packages) matching the ``/api/package/...`` endpoint prefixes.
    All methods return the raw ``requests.Response`` from ``BaseAPI``,
    except ``verify_payment_link`` which makes its own out-of-band request
    (see its docstring).
    """

    # Package Management
    def get_all_packages(self, **params):
        """List all packages.

        GET /api/package/all

        Args:
            **params: Optional query string parameters (e.g. filters,
                pagination) forwarded as-is to the request.

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.get("/api/package/all", params=params)

    def get_package_countries(self):
        """List countries available for packages.

        GET /api/package/countries

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.get("/api/package/countries")

    def get_single_package(self, package_id):
        """Fetch a single package by ID.

        GET /api/package/{id}

        Args:
            package_id: ID of the package to fetch.

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.get(f"/api/package/{package_id}")

    # Package Booking
    def book_package(self, booking_data):
        """Book a package.

        POST /api/package/book

        NOTE: this method is defined twice in this class (see the second
        ``book_package`` further below, under "User Booked Packages"),
        with identical bodies. The second definition silently shadows
        this one at class-creation time, so it's effectively dead code
        rather than a behavior difference - but it's worth cleaning up
        since a future edit to only one copy would create a real
        divergence.

        Args:
            booking_data (dict): Package booking payload (e.g. package
                id, traveller details, price option).

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.post("/api/package/book", json=booking_data)

    def verify_payment(self, invoice_id, transaction_id):
        """Verify a package booking payment.

        GET /api/package/book/verify/{invoiceId}/{transaction_id}

        Args:
            invoice_id: Invoice ID returned when the booking was created.
            transaction_id: Transaction ID returned by the payment
                provider.

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.get(f"/api/package/book/verify/{invoice_id}/{transaction_id}")

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
            response = requests.get(payment_link, timeout=10, allow_redirects=True)

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

    # Package Deals
    def get_all_deals(self, **params):
        """List all package deals.

        GET /api/package/deal/all

        Args:
            **params: Optional query string parameters forwarded as-is.

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.get("/api/package/deal/all", params=params)

    def get_single_deal(self, deal_id):
        """Fetch a single package deal by ID.

        GET /api/package/deal/{id}

        Args:
            deal_id: ID of the deal to fetch.

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.get(f"/api/package/deal/{deal_id}")

    def book_package(self, booking_data):
        """Book a package.

        POST /api/package/book

        NOTE: duplicate of the ``book_package`` method defined earlier in
        this class under "Package Booking" - see that copy's docstring.
        This later definition is the one that actually wins, since Python
        keeps the last method assignment on the class.

        Args:
            booking_data (dict): Package booking payload (e.g. package
                id, traveller details, price option).

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.post("/api/package/book", json=booking_data)

    # User Booked Packages
    def get_user_booked_packages(self, **params):
        """List packages booked by the current user.

        GET /api/package/user/booked-packages

        Args:
            **params: Optional query string parameters (e.g. pagination)
                forwarded as-is.

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.get("/api/package/user/booked-packages", params=params)

    def get_user_booked_packages_analytics(self):
        """Fetch booking analytics for the current user's packages.

        GET /api/package/user/booked-packages-analytics

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.get("/api/package/user/booked-packages-analytics")
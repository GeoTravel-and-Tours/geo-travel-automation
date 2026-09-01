# src/pages/api/newsletter_api.py

"""API client for the retail ``/api/newsletter`` endpoint.

Wraps the single newsletter-subscription call used by tests that verify
visitors can sign up for the Geo Travel mailing list.
"""

from ...core.base_api import BaseAPI

class NewsletterAPI(BaseAPI):
    """Client for the ``/api/newsletter`` resource.

    Currently exposes only newsletter subscription; all methods are thin
    wrappers around ``BaseAPI.post`` and return the raw ``requests.Response``.
    """

    def subscribe_newsletter(self, subscribe_data):
        """Subscribe an email address to the newsletter.

        POST /api/newsletter/create

        Args:
            subscribe_data (dict): Request payload, e.g. containing the
                subscriber's email address.

        Returns:
            requests.Response: Raw response from the API.
        """
        return self.post("/api/newsletter/create", json=subscribe_data)
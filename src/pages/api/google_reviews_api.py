"""
src/pages/api/google_reviews_api.py

API client for the /api/google/reviews endpoint of the Geo Travel
backend, which surfaces Google reviews for display on the site (e.g.
a testimonials section).
"""

from ...core.base_api import BaseAPI

class GoogleAPI(BaseAPI):
    """API client for the /api/google resource (Google reviews).

    Currently exposes a single endpoint under ``/api/google/reviews``.
    """

    def get_reviews(self):
        """Fetch Google reviews.

        GET /api/google/reviews

        Returns:
            requests.Response: The raw response from the request.
        """
        return self.get("/api/google/reviews")

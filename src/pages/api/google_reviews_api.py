# src/pages/api/google_api.py

from ...core.base_api import BaseAPI

class GoogleAPI(BaseAPI):
    def get_reviews(self):
        """GET /api/google/reviews"""
        return self.get("/api/google/reviews")
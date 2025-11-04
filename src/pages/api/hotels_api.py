# src/pages/api/hotel_api.py

from ...core.base_api import BaseAPI

class HotelAPI(BaseAPI):
    def search_hotels(self, **params):
        """GET /api/hotels"""
        return self.get("/api/hotels", params=params)

    def get_hotel_cities(self, **params):
        """GET /api/hotels/cities"""
        return self.get("/api/hotels/cities", params=params)
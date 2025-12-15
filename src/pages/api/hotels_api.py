# src/pages/api/hotels_api.py

from ...core.base_api import BaseAPI

class HotelAPI(BaseAPI):
    """Comprehensive Hotel API client"""
    
    def search_hotels(self, **params):
        """POST /api/hotels/search - Search for hotels"""
        return self.post("/api/hotels/search", json=params)
    
    def get_hotel_cities(self, **params):
        """GET /api/hotels/cities - Get hotel cities"""
        return self.get("/api/hotels/cities", params=params)
    
    def get_hotel_rating(self, **params):
        """GET /api/hotels/rating - Get hotel rating"""
        return self.get("/api/hotels/rating", params=params)
    
    def book_hotel(self, **params):
        """POST /api/hotels/book - Book a hotel"""
        return self.post("/api/hotels/book", json=params)
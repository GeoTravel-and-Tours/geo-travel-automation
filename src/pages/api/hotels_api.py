# src/pages/api/hotels_api.py

from ...core.base_api import BaseAPI

class HotelAPI(BaseAPI):
    """Comprehensive Hotel API client"""
    
    # def __init__(self, base_url=None):
    #     super().__init__(base_url)
    #     # Don't set default auth - let tests decide
    #     self.auth_token = None
    
    def search_hotels(self, **params):
        """POST /api/hotels/search - Search for hotels"""
        query_params = {}
        if "page" in params:
            query_params["page"] = params["page"]
        if "limit" in params:
            query_params["limit"] = params["limit"]

        # Debugging: Log headers and payload
        headers = self.get_headers()
        self.logger.info(f"Request headers: {headers}")
        self.logger.info(f"Request payload: {params}")

        return self.post("/api/hotels/search", params=query_params, json=params)
    
    def get_hotel_cities(self, **params):
        """GET /api/hotels/cities - Get hotel cities"""
        return self.get("/api/hotels/cities", params=params)
    
    def get_hotel_rating(self, **params):
        """GET /api/hotels/rating - Get hotel rating"""
        return self.get("/api/hotels/rating", params=params)
    
    def book_hotel(self, **params):
        """POST /api/hotels/book - Book a hotel"""
        return self.post("/api/hotels/book", json=params)
    
    def get_hotel_offers(self, **params):
        """
        POST /api/hotels/offerReq - Get detailed hotel offers with pricing
        
        Key features:
        - Returns hotel details with room offers
        - Includes currency conversion when requested currency differs
        - Adds requestedCurrencyTotalPrice and currencyConversion fields
        """
        return self.post("/api/hotels/offer", json=params)
    
    def get_headers(self):
        """Retrieve headers for API requests, including Authorization if token is set"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Client-Type": "retail"
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
# src/pages/api/hotels_api.py

from ...core.base_api import BaseAPI

class HotelAPI(BaseAPI):
    """Comprehensive Hotel API client"""
    
    # def search_hotels(self, **params):
    #     """POST /api/hotels/search - Search for hotels"""
    #     query_params = {}
    #     if "page" in params:
    #         query_params["page"] = params["page"]
    #     if "limit" in params:
    #         query_params["limit"] = params["limit"]

    #     # Debugging: Log headers and payload
    #     headers = self.get_headers()
    #     self.logger.info(f"Request headers: {headers}")
    #     self.logger.info(f"Request payload: {params}")

    #     return self.post("/api/hotels/search", params=query_params, json=params)
    
    def search_hotels(self, **kwargs):
        """Search for hotels with debug logging"""
        # DEBUG: Check headers at method start
        self.logger.info(f"🔍 search_hotels START - Current headers: {self.headers}")
        
        # Check if headers changed from original
        if hasattr(self, '_debug_original_headers'):
            if self.headers != self._debug_original_headers:
                self.logger.error(f"❌ HEADERS CHANGED! Original: {self._debug_original_headers}")
                self.logger.error(f"❌ Current: {self.headers}")
                # Find what changed
                for key in set(self.headers.keys()) | set(self._debug_original_headers.keys()):
                    if self.headers.get(key) != self._debug_original_headers.get(key):
                        self.logger.error(f"❌ Header '{key}' changed from '{self._debug_original_headers.get(key)}' to '{self.headers.get(key)}'")
        
        # Make the request but log what's being sent
        self.logger.info(f"🔍 Making request to /api/hotels/search with headers: {self.headers}")
        
        # Try to capture what's actually being sent at the session level
        original_prep = self.session.prepare_request
        
        def debug_prepare_request(request):
            self.logger.info(f"🔍 SESSION - Prepared request headers: {request.headers}")
            return original_prep(request)
        
        self.session.prepare_request = debug_prepare_request
        
        response = self.post("/api/hotels/search", json=kwargs)
        
        # Restore original method
        self.session.prepare_request = original_prep
        
        # DEBUG: Check headers after request
        self.logger.info(f"🔍 search_hotels END - Headers after request: {self.headers}")
        
        return response
    
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
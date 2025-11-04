# src/pages/api/flight_api.py

from ...core.base_api import BaseAPI

class FlightAPI(BaseAPI):
    
    def search_request(self, search_data):
        """POST /api/flight/search-request"""
        endpoint = "/api/flight/search-request"
        return self.post(endpoint, json=search_data)
    
    def get_search_results(self, search_id):
        """GET /api/flight/search"""
        endpoint = f"/api/flight/search?search_id={search_id}"
        return self.get(endpoint)
    
    def initiate_booking(self, booking_data):
        """POST /api/flight/initiate-booking"""
        endpoint = "/api/flight/initiate-booking"
        return self.post(endpoint, json=booking_data)
    
    def get_booked_flights(self, limit=10, page=1, category="Upcoming"):
        """GET /api/flight/user/booked-flights"""
        endpoint = f"/api/flight/user/booked-flights?limit={limit}&page={page}&category={category}"
        return self.get(endpoint)
    
    def create_quote(self, quote_data):
        """POST /api/flight/quote"""
        return self.post("/api/flight/quote", json=quote_data)
    
    def get_quote(self, reference):
        """GET /api/flight/quote"""
        return self.get(f"/api/flight/quote?reference={reference}")
    
    def validate_passenger_email(self, passenger_data):
        """POST /api/flight/validate-passenger-email"""
        return self.post("/api/flight/validate-passenger-email", json=passenger_data)
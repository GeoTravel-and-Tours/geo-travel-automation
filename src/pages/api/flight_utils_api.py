# src/pages/api/flight_utils_api.py

from ...core.base_api import BaseAPI

class FlightUtilsAPI(BaseAPI):
    def get_all_airports(self):
        """GET /api/flight/airports/all"""
        return self.get("/api/flight/airports/all")
    
    def get_all_airlines(self):
        """GET /api/flight/airlines/all"""
        return self.get("/api/flight/airlines/all")
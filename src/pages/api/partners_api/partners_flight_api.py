# src/pages/api/Partners_api/partners_flight_api.py

import os
from datetime import datetime, timedelta
from src.core.partners_base_api import PartnersBaseAPI

class PartnersFlightAPI(PartnersBaseAPI):
    def __init__(self, api_key=None, api_secret=None, app_id=None):
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.app_id = app_id
        self.endpoints = {
            'search': '/api/flight/search',
            'book': '/api/flight/book',
            'bookings': '/api/flight/bookings'
        }
    
    def _get_flight_headers(self):
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-api-key': self.api_key,
            'x-api-secret': self.api_secret,
            'x-app-id': self.app_id
        }
        self.logger.info(f"Flight API Headers: {headers}")  # Debug logging
        return headers
    
    def search_flights(self, search_data):
        headers=self._get_flight_headers()
        self.logger.info(f"🔍 SENDING THESE HEADERS: {headers}")
        return self.post(self.endpoints['search'], json=search_data, 
                        headers=headers)

    def book_flight(self, booking_data):
        headers = self._get_flight_headers()
        self.logger.info(f"🔍 SENDING THESE HEADERS: {headers}")
        return self.post(self.endpoints['book'], json=booking_data,
                        headers=headers)
    
    def get_bookings(self, limit=None, page=None):
        params = {}
        if limit: params['limit'] = limit
        if page: params['page'] = page
        return self.get(self.endpoints['bookings'], params=params)
    
    @staticmethod
    def get_future_date(days_ahead=1):
        """Get a future date string in YYYY-MM-DD format"""
        future_date = datetime.now() + timedelta(days=days_ahead)
        return future_date.strftime("%Y-%m-%d")
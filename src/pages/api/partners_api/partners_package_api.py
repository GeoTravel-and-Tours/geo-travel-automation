# src/pages/api/Partners_api/partners_package_api.py

import os
from wsgiref import headers
from src.core.partners_base_api import PartnersBaseAPI

class PartnersPackageAPI(PartnersBaseAPI):
    def __init__(self, api_key=None, api_secret=None, app_id=None):
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.app_id = app_id
        self.endpoints = {
            'all': '/api/package/all',
            'book': '/api/package/book',
            'countries': '/api/package/countries',
            'bookings': '/api/package/bookings'
        }
    
    def _get_package_headers(self):
        return {
            'x-api-key': self.api_key,
            'x-api-secret': self.api_secret,
            'x-app-id': self.app_id
        }
        self.logger.info(f"Package API Headers: {headers}")  # Debug logging
        return headers
    
    def get_all_packages(self, city=None, country=None, limit=None, page=None):
        params = {}
        if city: params['city'] = city
        if country: params['country'] = country
        if limit: params['limit'] = limit
        if page: params['page'] = page
        return self.get(self.endpoints['all'], params=params,
                        headers=self._get_package_headers())
    
    def book_package(self, booking_data):
        return self.post(self.endpoints['book'], json=booking_data,
                         headers=self._get_package_headers())

    def get_package_countries(self):
        return self.get(self.endpoints['countries'],
                        headers=self._get_package_headers())

    def get_package_bookings(self, limit=None, page=None):
        params = {}
        if limit: params['limit'] = limit
        if page: params['page'] = page
        return self.get(self.endpoints['bookings'], params=params,
                        headers=self._get_package_headers())
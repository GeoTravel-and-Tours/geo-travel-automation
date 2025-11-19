# src/core/base_api.py

import requests
import json
from datetime import datetime
from src.utils.logger import GeoLogger
from configs.environment import EnvironmentConfig

class BaseAPI:
    def __init__(self):
        self.base_url = EnvironmentConfig.get_api_base_url()
        self.session = requests.Session()
        self.auth_token = None
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self.logger = GeoLogger(self.__class__.__name__)  # Initialize your logger
    
    def set_auth_token(self, token):
        """Set authentication token for API requests"""
        self.auth_token = token
        self.headers['Authorization'] = f'Bearer {token}'
        self.logger.info("Auth token set for API requests")
    
    def _request(self, method, endpoint, **kwargs):
        """Base request method with logging and error handling"""
        url = f"{self.base_url}{endpoint}"
        kwargs['timeout'] = 30
        
        # Merge headers
        headers = self.headers.copy()
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        
        self.logger.info(f"API Request: {method} {url}")
        
        try:
            kwargs['timeout'] = 30
            response = self.session.request(method, url, headers=headers, **kwargs)
            self.logger.info(f"API Response: {response.status_code}")
            
            # Log response for debugging (be careful with sensitive data)
            if response.status_code >= 400:
                self.logger.warning(f"API Error Response: {response.text}")
            
            return response
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API Request failed: {str(e)}")
            raise
    
    def get(self, endpoint, **kwargs):
        return self._request('GET', endpoint, **kwargs)
    
    def post(self, endpoint, **kwargs):
        return self._request('POST', endpoint, **kwargs)
    
    def put(self, endpoint, **kwargs):
        return self._request('PUT', endpoint, **kwargs)
    
    def patch(self, endpoint, **kwargs):
        return self._request('PATCH', endpoint, **kwargs)
    
    def delete(self, endpoint, **kwargs):
        return self._request('DELETE', endpoint, **kwargs)
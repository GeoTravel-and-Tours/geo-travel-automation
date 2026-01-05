# src/core/base_api.py

import requests
import json
from pathlib import Path
from datetime import datetime
from src.utils.logger import GeoLogger
from src.utils.token_extractor import TokenExtractor
from configs.environment import EnvironmentConfig

class BaseAPI:
    def __init__(self):
        self.base_url = EnvironmentConfig.get_api_base_url()
        self.session = requests.Session()
        self.auth_token = None
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Client-Type': 'retail'
        }
        self.logger = GeoLogger(self.__class__.__name__)
        self.token_extractor = TokenExtractor()
    
    def set_auth_token(self, token, token_source="cookies"):
        """
        Set authentication token dynamically based on source
        
        Args:
            token: The auth token
            token_source: Where token came from - "cookies" or "response_body"
                        "cookies": token was from Set-Cookie header -> use Cookie header
                        "response_body": token was in JSON response -> use Authorization header
        """
        if not token or not isinstance(token, str):
            self.logger.warning("⚠️ Invalid token provided to set_auth_token()")
            return
        
        self.auth_token = token
        self.token_source = token_source  # Store where token came from
        
        if token_source == "cookies":
            # Token came from cookies - use Cookie header
            self.headers['Cookie'] = f'retail_access_token={token}'
            # Remove Authorization header if it exists
            self.headers.pop('Authorization', None)
            self.logger.info(f"✅ Auth token set from cookies (Cookie header)")
            
        elif token_source == "response_body":
            # Token came from response body - use Authorization header
            self.headers['Authorization'] = f'Bearer {token}'
            # Remove Cookie header if it exists
            self.headers.pop('Cookie', None)
            self.logger.info(f"✅ Auth token set from response body (Authorization header)")
        
        # Always set session cookie as backup
        try:
            from urllib.parse import urlparse
            parsed = urlparse(self.base_url or '')
            domain = parsed.hostname if parsed.hostname else None
            if domain:
                self.session.cookies.set('retail_access_token', token, domain=domain, path='/')
            else:
                self.session.cookies.set('retail_access_token', token)
        except Exception as e:
            self.logger.debug(f"Could not set session cookie: {e}")
    
    def _request(self, method, endpoint, **kwargs):
        """Base request method with logging, retry logic, and error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))

        self.logger.info(f"API Request: {method} {url}")
        kwargs['timeout'] = 30

        for attempt in range(3):
            try:
                response = self.session.request(method, url, headers=headers, **kwargs)
                if response is None:
                    raise ValueError("API response is None")

                self.logger.info(f"API Response: {response.status_code}")
                self.logger.debug(f"Response text: {response.text}")
                return response

            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    self.logger.error("Max retries reached. Raising exception.")
                    raise
                self.logger.info("Retrying...")
    
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
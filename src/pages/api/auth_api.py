# src/pages/api/auth_api.py

import os
from ...core.base_api import BaseAPI

class AuthAPI(BaseAPI):
    
    def login(self, email=None, password=None):
        """POST /api/auth/login"""
        endpoint = "/api/auth/login"

        # If no credentials provided, get from environment
        if email is None or password is None:
            email, password = self.get_api_credentials_from_env()

        payload = {"email": email, "password": password}
        self.logger.info(f"Attempting login with email: {email}")

        response = self.post(endpoint, json=payload)

        if response.status_code == 200:
            response_data = response.json()
            if 'data' in response_data and 'access_token' in response_data['data']:
                token = response_data['data']['access_token']
                self.set_auth_token(token)
                self.logger.info("Login successful - auth token set")
            else:
                self.logger.warning("Login successful but no access token found in response data")
        else:
            self.logger.warning(f"Login failed with status: {response.status_code}")

        return response
    
    def logout(self, refresh_token):
        """POST /api/auth/logout"""
        endpoint = "/api/auth/logout"
        payload = {"refresh_token": refresh_token}
        return self.post(endpoint, json=payload)
    
    def get_api_credentials_from_env(self):
        """Get test credentials from environment variables"""
        email = os.getenv("API_TEST_EMAIL")
        password = os.getenv("API_TEST_PASSWORD")

        if not email or not password:
            self.logger.error("API_TEST_EMAIL or API_TEST_PASSWORD not found in environment")
            raise ValueError("API credentials not configured in environment")

        self.logger.info(f"Retrieved credentials from environment for: {email}")
        return email, password
    
    def refresh_token(self):
        """"POST /api/auth/refresh"""
        return self.post("/api/auth/refresh")
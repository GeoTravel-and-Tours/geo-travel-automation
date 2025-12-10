# src/pages/api/auth_api.py

import os
from ...core.base_api import BaseAPI
from ...utils.token_extractor import TokenExtractor

class AuthAPI(BaseAPI):
    
    def __init__(self):
        super().__init__()
        self.token_extractor = TokenExtractor()
    
    def login(self, email=None, password=None):
        """POST /api/auth/login - Dynamic token extraction from response or cookies"""
        endpoint = "/api/auth/login"

        # If no credentials provided, get from environment
        if email is None or password is None:
            email, password = self.get_api_credentials_from_env()

        payload = {"email": email, "password": password}
        self.logger.info(f"Attempting login with email: {email}")

        response = self.post(endpoint, json=payload)

        if response.status_code == 200:
            # Use TokenExtractor for dynamic token extraction
            token, extraction_method = self.token_extractor.extract_token(response)
            
            if token:
                is_valid = self.token_extractor.validate_token(token)
                self.token_extractor.log_extraction_attempt(token, extraction_method, is_valid)
                
                if is_valid:
                    self.set_auth_token(token)
                    self.logger.success(f"✅ Login successful - token set via {extraction_method}")
                else:
                    self.logger.warning(f"⚠️ Token extracted via {extraction_method} but validation failed")
            else:
                self.logger.warning("❌ Login successful (200) but no token found in response, cookies, or headers")
        else:
            self.logger.warning(f"❌ Login failed with status: {response.status_code}")

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
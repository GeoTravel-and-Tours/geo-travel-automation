# src/pages/api/partners_api/partners_auth_api.py

import os
from src.core.partners_base_api import PartnersBaseAPI
from src.utils.token_extractor import TokenExtractor

class PartnersAuthAPI(PartnersBaseAPI):
    def __init__(self):
        super().__init__()
        self.token_extractor = TokenExtractor()
        self.endpoints = {
            'welcome': '/api',
            'signup': '/api/auth/signup',
            'login': '/api/auth/login',
            'verify_email': '/api/auth/verify-email',
            'resend_verification': '/api/auth/resend-verification-email',
            'forgot_password': '/api/auth/forgot-password',
            'reset_password': '/api/auth/reset-password'
        }
    
    def get_welcome(self):
        """GET /api - Welcome message"""
        return self.get(self.endpoints['welcome'])
    
    def signup(self, org_data):
        """POST /api/auth/signup - Organization registration"""
        return self.post(self.endpoints['signup'], json=org_data)
    
    def login(self, credentials):
        """POST /api/auth/login - Organization login with dynamic token extraction"""
        response = self.post(self.endpoints['login'], json=credentials)
        
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
                self.logger.debug("Login successful (200) but no token found (may not be verified user)")
        
        return response
    
    def verify_email(self, token):
        """POST /api/auth/verify-email - Verify email address"""
        return self.post(self.endpoints['verify_email'], json={'token': token})
    
    def resend_verification(self, email):
        """POST /api/auth/resend-verification-email - Resend verification email"""
        return self.post(self.endpoints['resend_verification'], json={'email': email})
    
    def forgot_password(self, email):
        """POST /api/auth/forgot-password - Forgot password"""
        return self.post(self.endpoints['forgot_password'], json={'email': email})
    
    def reset_password(self, token, new_password):
        """POST /api/auth/reset-password - Reset password"""
        return self.post(self.endpoints['reset_password'], json={
            'token': token,
            'newPassword': new_password
        })
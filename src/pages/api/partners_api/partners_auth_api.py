# src/pages/api/Partners_api/partners_auth_api.py

import os
from src.core.partners_base_api import PartnersBaseAPI

class PartnersAuthAPI(PartnersBaseAPI):
    def __init__(self):
        super().__init__()
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
        """POST /api/auth/login - Organization login"""
        return self.post(self.endpoints['login'], json=credentials)
    
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
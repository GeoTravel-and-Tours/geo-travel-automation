# src/tests/partners_api_tests/test_partners_auth_api.py

import os
import pytest
import random
from src.pages.api.partners_api.partners_auth_api import PartnersAuthAPI
from src.utils.verified_partners_helper import VerifiedUserHelper
from src.utils.token_extractor import TokenExtractor
from src.utils.logger import GeoLogger

class TestPartnersAuth:
    def setup_method(self):
        self.auth_api = PartnersAuthAPI()
        self.verified_helper = VerifiedUserHelper()
        
        # Use ONE consistent email for ALL tests
        self.test_email = f"geobot{random.randint(10000,99999)}@yopmail.com"
        self.test_password = "StrongPass123!"
        self.test_org_data = {
            "orgName": f"GEO Bot Ltd {random.randint(1000,9999)}",
            "orgEmail": self.test_email,
            "address": "123 Test St, Test City",
            "password": self.test_password,
            "contactPerson": {
                "firstName": "GEO",
                "lastName": "Bot",
                "phoneNumber": "+1234567890"
            }
        }
        self.logger = GeoLogger(self.__class__.__name__)
        self.logger.info(f"🎯 TEST SETUP - Using email: {self.test_email}")
        self.logger.info(f"🎯 TEST SETUP - Using orgName: {self.test_org_data['orgName']}")
    
    @pytest.mark.partners_api
    def test_welcome_message(self):
        """Test GET /api welcome message"""
        response = self.auth_api.get_welcome()
        assert response.status_code == 200
        assert 'Welcome to GeoTravel API Gateway' in response.json().get('message', '')
        self.logger.success("Welcome message received successfully")
    
    @pytest.mark.partners_api
    def test_organization_signup_success(self):
        """Test successful organization registration - CREATES THE USER"""
        self.logger.info(f"🔵 TEST START - Signup with: {self.test_email}")
        
        response = self.auth_api.signup(self.test_org_data)
        
        self.logger.info(f"🟢 SIGNUP RESPONSE - Status: {response.status_code}")
        if response.status_code == 201:
            self.logger.success(f"✅ ORGANIZATION CREATED - Email: {self.test_email}")
        else:
            self.logger.error(f"❌ SIGNUP FAILED - Email: {self.test_email}, Response: {response.text}")
        
        assert response.status_code == 201
        assert "registered successfully" in response.json().get('message', '')
        self.logger.success(f"✅ ORGANIZATION SIGNUP SUCCESS - Email: {self.test_email}")
    
    @pytest.mark.partners_api
    def test_organization_login_unverified_returns_no_token(self):
        """Test that THE SAME unverified user cannot get access token"""
        # First create the user
        signup_response = self.auth_api.signup(self.test_org_data)
        assert signup_response.status_code == 201
        
        # Then try to login as THE SAME user - should fail with no token
        credentials = {
            "orgEmail": self.test_email,
            "password": self.test_password
        }
        self.logger.info(f"🔵 TEST START - Login with SAME user: {self.test_email}")
        response = self.auth_api.login(credentials)
        
        # STRONG ASSERTIONS - THE SAME unverified user should NOT get access
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == "Email not verified"
        assert data['data']['isEmailVerified'] is False
        assert data['data']['accessToken'] is None
        
        self.logger.success("THE SAME unverified user correctly denied access token")
    
    @pytest.mark.partners_api
    def test_verified_user_login_returns_token(self):
        """TEST: Verified users get access token on login"""
        token = self.verified_helper.get_verified_access_token()
        assert token is not None, "Verified user should get access token"
        assert len(token) > 10, "Token should be valid JWT"
        self.logger.success("✅ Verified user login returns valid access token")
    
    @pytest.mark.partners_api
    def test_verified_user_login_response_structure(self):
        """TEST: Verified user login has correct response structure"""
        login_response = self.auth_api.login({
            "orgEmail": os.getenv("PARTNERS_VERIFIED_EMAIL"),
            "password": os.getenv("PARTNERS_VERIFIED_PASSWORD")
        })
        
        assert login_response.status_code == 200
        data = login_response.json()
        
        # Verified users should get different response than unverified
        assert data['message'] == "Login successful"
        assert data['data']['isEmailVerified'] is True
        assert data['data']['accessToken'] is not None
        self.logger.success("✅ Verified user login has correct response structure")
    
    @pytest.mark.partners_api
    def test_partners_dynamic_token_extraction(self):
        """TEST: Partners API uses dynamic token extraction"""
        self.logger.info("=== Testing Partners API Dynamic Token Extraction ===")
        login_response = self.auth_api.login({
            "orgEmail": os.getenv("PARTNERS_VERIFIED_EMAIL"),
            "password": os.getenv("PARTNERS_VERIFIED_PASSWORD")
        })
        
        assert login_response.status_code == 200
        
        # Test the token extractor directly
        token_extractor = TokenExtractor()
        token, extraction_method = token_extractor.extract_token(login_response)
        
        # Token should be found
        assert token is not None, "Token extraction failed for Partners API"
        assert extraction_method is not None, "Extraction method should be identified"
        
        # Token should be valid
        is_valid = token_extractor.validate_token(token)
        assert is_valid, f"Token validation failed for {extraction_method} extracted token"
        
        self.logger.success(f"✅ Partners API dynamic token extraction successful via '{extraction_method}'")
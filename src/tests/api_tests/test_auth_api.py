# src/tests/api_tests/test_auth_api.py

import pytest
from src.pages.api.auth_api import AuthAPI
from src.utils.logger import GeoLogger

class TestAuthAPI:
    
    def setup_method(self):
        """Setup before each test method"""
        self.logger = GeoLogger(self.__class__.__name__)
    
    @pytest.fixture
    def auth_api(self):
        return AuthAPI()
    
    @pytest.mark.api
    def test_login_success(self, auth_api):
        """Test successful login with valid credentials from environment"""
        response = auth_api.login()
        
        # Check if login was successful
        assert response.status_code == 200
        
        response_data = response.json()
        # Access token is nested under 'data'
        assert 'data' in response_data
        assert 'access_token' in response_data['data']
        assert 'refresh_token' in response_data['data']
        assert auth_api.auth_token is not None
        
        self.logger.info("Login successful with valid credentials")
        self.logger.info(f"Access token received: {auth_api.auth_token[:50]}...")
    
    @pytest.mark.api
    def test_login_invalid_credentials(self, auth_api):
        """Test login with invalid credentials"""
        response = auth_api.login("invalid@example.com", "wrongpassword123")
        
        self.logger.info(f"Invalid credentials response: {response.status_code} - {response.text}")
        
        # Should get an error response for invalid credentials
        assert response.status_code in [400, 401]
        
        response_data = response.json()
        assert 'status' in response_data or 'message' in response_data or 'error' in response_data
        
        self.logger.info("Invalid credentials test passed")
    
    @pytest.mark.api
    def test_login_empty_credentials(self, auth_api):
        """Test login with empty credentials"""
        response = auth_api.login("", "")
        
        self.logger.info(f"Empty credentials response: {response.status_code} - {response.text}")
        
        # Should get an error response
        assert response.status_code in [400, 422]
        
        response_data = response.json()
        assert 'status' in response_data or 'message' in response_data or 'error' in response_data
        
        self.logger.info("Empty credentials test passed")
    
    @pytest.mark.api
    def test_login_missing_password(self, auth_api):
        """Test login with missing password"""
        response = auth_api.login("test@example.com", "")
        
        self.logger.info(f"Missing password response: {response.status_code} - {response.text}")
        
        # Should get an error response
        assert response.status_code in [400, 422]
        
        response_data = response.json()
        assert 'status' in response_data or 'message' in response_data or 'error' in response_data
        
        self.logger.info("Missing password test passed")

    @pytest.mark.api
    def test_auth_token_set_after_successful_login(self, auth_api):
        """Test that auth token is set after successful login"""
        response = auth_api.login()
        
        # Check if login was successful
        assert response.status_code == 200
        
        response_data = response.json()
        # Token is nested under 'data'
        if 'data' in response_data and 'access_token' in response_data['data']:
            # Auth token should be set
            assert auth_api.auth_token is not None
            assert isinstance(auth_api.auth_token, str)
            assert len(auth_api.auth_token) > 0
            
            # Check that Authorization header is set
            assert 'Authorization' in auth_api.headers
            assert f'Bearer {auth_api.auth_token}' == auth_api.headers['Authorization']
            
            self.logger.info("Auth token successfully set after login")
            self.logger.info(f"Authorization header: {auth_api.headers['Authorization'][:50]}...")
        else:
            pytest.skip("No access token in response - cannot test token setting")
# src/tests/api_tests/test_auth_api.py

import pytest
from src.pages.api.auth_api import AuthAPI
from src.utils.logger import GeoLogger
from src.utils.token_extractor import TokenExtractor

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
        self.logger.info("=== Testing Login Success ===")
        response = auth_api.login()
        
        # Check if login was successful
        assert response.status_code == 200
        
        response_data = response.json()
        # New API returns success with token in cookie 'retail_access_token'
        assert response_data.get('status') == 'success'
        assert 'data' in response_data

        # Token is extracted from cookie (retail_access_token), not response body
        assert auth_api.auth_token is not None, "Auth token should be extracted from cookie"
        assert isinstance(auth_api.auth_token, str)
        assert len(auth_api.auth_token) > 0

        self.logger.info("Login successful with valid credentials")
        self.logger.info(f"Access token received: {auth_api.auth_token[:50]}...")
    
    @pytest.mark.api
    def test_login_invalid_credentials(self, auth_api):
        """Test login with invalid credentials"""
        self.logger.info("=== Testing Login with Invalid Credentials ===")
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
        self.logger.info("=== Testing Login with Empty Credentials ===")
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
        self.logger.info("=== Testing Login with Missing Password ===")
        response = auth_api.login("test@example.com", "")
        
        self.logger.info(f"Missing password response: {response.status_code} - {response.text}")
        
        # Should get an error response
        assert response.status_code in [400, 422]
        
        response_data = response.json()
        assert 'status' in response_data or 'message' in response_data or 'error' in response_data
        
        self.logger.info("Missing password test passed")

    @pytest.mark.api
    def test_auth_token_set_after_successful_login(self, auth_api):
        """Test that auth token is set after successful login (works for both environments)"""
        self.logger.info("=== Testing Auth Token Set After Successful Login ===")
        
        response = auth_api.login()
        
        # Verify login was successful
        assert response.status_code == 200
        
        # auth_api.login() handles token extraction from both cookies and response body
        assert auth_api.auth_token is not None, "Auth token must be set after successful login"
        assert isinstance(auth_api.auth_token, str), "Auth token must be a string"
        assert len(auth_api.auth_token) > 0, "Auth token cannot be empty"
        
        # Verify Authorization header is properly set
        if auth_api.token_source == "response_body":
            assert 'Authorization' in auth_api.headers, "Authorization header must be set"
            assert auth_api.headers['Authorization'].startswith('Bearer '), "Authorization header must start with 'Bearer '"
            assert auth_api.auth_token in auth_api.headers['Authorization'], "Auth token must be in Authorization header"
            self.logger.info(f"Authorization header: {auth_api.headers['Authorization'][:50]}...")
        else:
            assert 'Cookie' in auth_api.headers, "Cookie header must be set"
            assert f'retail_access_token={auth_api.auth_token}' in auth_api.headers['Cookie'], "Auth token must be in Cookie header"
            self.logger.info(f"Cookie header: {auth_api.headers['Cookie'][:50]}...")
        
        self.logger.info(f"✅ Auth token successfully set (length: {len(auth_api.auth_token)})")
    
    @pytest.mark.api
    def test_dynamic_token_extraction(self, auth_api):
        """Test that token extraction works dynamically"""
        self.logger.info("=== Testing Dynamic Token Extraction ===")
        response = auth_api.login()
        
        assert response.status_code == 200
        
        # Test the token extractor directly
        token_extractor = TokenExtractor()
        token, extraction_method = token_extractor.extract_token(response)
        
        # Token should be found via some method
        assert token is not None, "Token extraction failed"
        assert extraction_method is not None, "Extraction method should be identified"
        assert extraction_method in ['response_body', 'cookies', 'header'], f"Invalid extraction method: {extraction_method}"
        
        # Token should be valid
        is_valid = token_extractor.validate_token(token)
        assert is_valid, f"Token validation failed for {extraction_method} extracted token"
        
        self.logger.success(f"✅ Dynamic token extraction successful via '{extraction_method}'")
    
    @pytest.mark.api
    def test_token_validation(self, auth_api):
        """Test that token validation works correctly"""
        self.logger.info("=== Testing Token Validation ===")
        response = auth_api.login()
        
        assert response.status_code == 200
        
        token_extractor = TokenExtractor()
        token, _ = token_extractor.extract_token(response)
        
        assert token is not None, "No token extracted"
        
        # Test validation
        is_valid = token_extractor.validate_token(token)
        assert is_valid, "Token validation failed"
        
        # Test invalid token scenarios
        assert not token_extractor.validate_token(None)
        assert not token_extractor.validate_token("")
        assert not token_extractor.validate_token("invalid")
        
        self.logger.success("✅ Token validation working correctly")
            
            
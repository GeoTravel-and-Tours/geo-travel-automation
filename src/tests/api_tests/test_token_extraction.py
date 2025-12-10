# src/tests/api_tests/test_token_extraction.py

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.utils.token_extractor import TokenExtractor
from src.utils.logger import GeoLogger


class TestTokenExtraction:
    """Comprehensive tests for dynamic token extraction"""
    
    def setup_method(self):
        """Setup before each test"""
        self.logger = GeoLogger(self.__class__.__name__)
        self.token_extractor = TokenExtractor()
    
    # ==================== Response Body Tests ====================
    
    @pytest.mark.api
    def test_extract_token_from_response_body_access_token(self):
        """Test extraction of access_token from response body"""
        self.logger.info("=== Testing Token Extraction: access_token ===")
        
        # Mock response with access_token in data
        response = Mock()
        response.json.return_value = {
            "data": {
                "access_token": "test_token_12345"
            }
        }
        response.cookies = {}
        response.headers = {}
        
        token, method = self.token_extractor.extract_token(response)
        
        assert token == "test_token_12345", "Token extraction failed"
        assert method == "response_body", "Wrong extraction method"
        self.logger.success("✅ Token extracted from response['data']['access_token']")
    
    @pytest.mark.api
    def test_extract_token_from_response_body_accessToken(self):
        """Test extraction of accessToken (camelCase) from response body"""
        self.logger.info("=== Testing Token Extraction: accessToken ===")
        
        response = Mock()
        response.json.return_value = {
            "data": {
                "accessToken": "test_token_camelcase"
            }
        }
        response.cookies = {}
        response.headers = {}
        
        token, method = self.token_extractor.extract_token(response)
        
        assert token == "test_token_camelcase", "Token extraction failed"
        assert method == "response_body", "Wrong extraction method"
        self.logger.success("✅ Token extracted from response['data']['accessToken']")
    
    @pytest.mark.api
    def test_extract_token_from_response_top_level(self):
        """Test extraction of token from top-level response (not nested)"""
        self.logger.info("=== Testing Token Extraction: Top-level ===")
        
        response = Mock()
        response.json.return_value = {
            "token": "test_token_toplevel"
        }
        response.cookies = {}
        response.headers = {}
        
        token, method = self.token_extractor.extract_token(response)
        
        assert token == "test_token_toplevel", "Token extraction failed"
        assert method == "response_body", "Wrong extraction method"
        self.logger.success("✅ Token extracted from response['token']")
    
    @pytest.mark.api
    def test_extract_token_respects_field_priority(self):
        """Test that token extraction respects field priority order"""
        self.logger.info("=== Testing Field Priority ===")
        
        # Response has multiple token fields - should pick access_token first
        response = Mock()
        response.json.return_value = {
            "data": {
                "access_token": "correct_token",
                "token": "wrong_token",
                "accessToken": "also_wrong"
            }
        }
        response.cookies = {}
        response.headers = {}
        
        token, method = self.token_extractor.extract_token(response)
        
        assert token == "correct_token", "Token priority not respected"
        self.logger.success("✅ Token field priority working correctly")
    
    # ==================== Cookie Tests ====================
    
    @pytest.mark.api
    def test_extract_token_from_cookies(self):
        """Test extraction of token from cookies when not in response body"""
        self.logger.info("=== Testing Token Extraction from Cookies ===")
        
        response = Mock()
        response.json.return_value = {}  # No token in response body
        response.cookies = {"auth_token": "cookie_token_12345"}
        response.headers = {}
        
        token, method = self.token_extractor.extract_token(response)
        
        assert token == "cookie_token_12345", "Cookie token extraction failed"
        assert method == "cookies", "Wrong extraction method"
        self.logger.success("✅ Token extracted from cookies")
    
    @pytest.mark.api
    def test_extract_token_prefers_response_body_over_cookies(self):
        """Test that response body is checked before cookies"""
        self.logger.info("=== Testing Response Body vs Cookies Priority ===")
        
        response = Mock()
        response.json.return_value = {
            "data": {
                "access_token": "response_token"
            }
        }
        response.cookies = {"auth_token": "cookie_token"}
        response.headers = {}
        
        token, method = self.token_extractor.extract_token(response)
        
        assert token == "response_token", "Response body not preferred"
        assert method == "response_body", "Should use response body method"
        self.logger.success("✅ Response body correctly prioritized over cookies")
    
    @pytest.mark.api
    def test_extract_token_from_header(self):
        """Test extraction of token from Authorization header"""
        self.logger.info("=== Testing Token Extraction from Header ===")
        
        response = Mock()
        response.json.return_value = {}
        response.cookies = {}
        response.headers = {"Authorization": "Bearer header_token_12345"}
        
        token, method = self.token_extractor.extract_token(response)
        
        assert token == "header_token_12345", "Header token extraction failed"
        assert method == "header", "Wrong extraction method"
        self.logger.success("✅ Token extracted from Authorization header")
    
    # ==================== Token Validation Tests ====================
    
    @pytest.mark.api
    def test_validate_jwt_token(self):
        """Test JWT token validation"""
        self.logger.info("=== Testing JWT Token Validation ===")
        
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        
        is_valid = self.token_extractor.validate_token(jwt_token)
        assert is_valid, "JWT token validation failed"
        self.logger.success("✅ JWT token validated correctly")
    
    @pytest.mark.api
    def test_validate_non_jwt_token(self):
        """Test validation of non-JWT tokens (still valid if long enough)"""
        self.logger.info("=== Testing Non-JWT Token Validation ===")
        
        token = "this_is_a_valid_long_token_that_is_at_least_20_chars"
        
        is_valid = self.token_extractor.validate_token(token)
        assert is_valid, "Non-JWT token validation failed"
        self.logger.success("✅ Non-JWT token validated correctly")
    
    @pytest.mark.api
    def test_reject_invalid_tokens(self):
        """Test that invalid tokens are rejected"""
        self.logger.info("=== Testing Invalid Token Rejection ===")
        
        assert not self.token_extractor.validate_token(None), "None should be invalid"
        assert not self.token_extractor.validate_token(""), "Empty string should be invalid"
        assert not self.token_extractor.validate_token("short"), "Short token should be invalid"
        
        self.logger.success("✅ Invalid tokens correctly rejected")
    
    # ==================== No Token Tests ====================
    
    @pytest.mark.api
    def test_extract_token_returns_none_when_not_found(self):
        """Test that extraction returns None when token not found anywhere"""
        self.logger.info("=== Testing Missing Token Handling ===")
        
        response = Mock()
        response.json.return_value = {}  # No token
        response.cookies = {}  # No cookies
        response.headers = {}  # No auth header
        
        token, method = self.token_extractor.extract_token(response)
        
        assert token is None, "Should return None when token not found"
        assert method is None, "Should return None for method when token not found"
        self.logger.success("✅ Missing token handled correctly")
    
    # ==================== Error Handling Tests ====================
    
    @pytest.mark.api
    def test_extract_token_handles_invalid_json(self):
        """Test that extractor handles non-JSON responses gracefully"""
        self.logger.info("=== Testing Invalid JSON Handling ===")
        
        response = Mock()
        response.json.side_effect = ValueError("Not JSON")
        response.cookies = {}
        response.headers = {}
        
        # Should not raise, just return None
        token, method = self.token_extractor.extract_token(response)
        
        assert token is None, "Should return None for non-JSON response"
        self.logger.success("✅ Invalid JSON handled gracefully")
    
    @pytest.mark.api
    def test_extract_token_handles_missing_cookies_gracefully(self):
        """Test that extractor handles missing cookies gracefully"""
        self.logger.info("=== Testing Missing Cookies Handling ===")
        
        response = Mock()
        response.json.return_value = {}
        response.cookies = None  # No cookies attribute
        response.headers = {}
        
        # Should not raise, just return None
        token, method = self.token_extractor.extract_token(response)
        
        assert token is None, "Should handle missing cookies"
        self.logger.success("✅ Missing cookies handled gracefully")
    
    # ==================== Environment Config Tests ====================
    
    @pytest.mark.api
    def test_token_extractor_loads_environment_config(self):
        """Test that TokenExtractor loads environment-specific config"""
        self.logger.info("=== Testing Environment Config Loading ===")
        
        # Create extractor for staging environment
        staging_extractor = TokenExtractor(environment='staging')
        
        assert staging_extractor.environment == 'staging'
        assert staging_extractor.config is not None
        assert 'response_fields' in staging_extractor.config
        assert 'cookie_names' in staging_extractor.config
        
        self.logger.success("✅ Environment config loaded correctly")
    
    @pytest.mark.api
    def test_different_environments_have_configs(self):
        """Test that all environments have token extraction configs"""
        self.logger.info("=== Testing All Environment Configs ===")
        
        for env in ['dev', 'qa', 'staging', 'production']:
            extractor = TokenExtractor(environment=env)
            assert extractor.config is not None, f"No config for {env}"
            assert 'response_fields' in extractor.config
            self.logger.debug(f"✓ Config found for {env}")
        
        self.logger.success("✅ All environments have configs")
    
    # ==================== Response Data Tests ====================
    
    @pytest.mark.api
    def test_extract_token_from_response_data_dict(self):
        """Test extracting token from parsed response data dict"""
        self.logger.info("=== Testing Direct Response Data Extraction ===")
        
        response_data = {
            "data": {
                "access_token": "direct_token"
            }
        }
        
        token, method = self.token_extractor.extract_token_from_response_data(response_data)
        
        assert token == "direct_token"
        assert method == "response_body"
        self.logger.success("✅ Token extracted from response data dict")
    
    @pytest.mark.api
    def test_extract_token_handles_custom_nested_path(self):
        """Test token extraction with custom nested path"""
        self.logger.info("=== Testing Custom Nested Path ===")
        
        response_data = {
            "payload": {
                "token": "custom_nested_token"
            }
        }
        
        token, method = self.token_extractor.extract_token_from_response_data(
            response_data,
            nested_path='payload',
            response_fields=['token']
        )
        
        assert token == "custom_nested_token"
        self.logger.success("✅ Custom nested path extraction working")


class TestTokenExtractionIntegration:
    """Integration tests combining multiple extraction strategies"""
    
    def setup_method(self):
        """Setup before each test"""
        self.logger = GeoLogger(self.__class__.__name__)
    
    @pytest.mark.api
    def test_fallback_chain_response_to_cookies(self):
        """Test fallback from response body to cookies"""
        self.logger.info("=== Testing Fallback: Response Body → Cookies ===")
        
        response = Mock()
        response.json.return_value = {}  # No token in response
        response.cookies = {"auth_token": "fallback_token"}
        response.headers = {}
        
        extractor = TokenExtractor()
        token, method = extractor.extract_token(response)
        
        assert token == "fallback_token"
        assert method == "cookies"
        self.logger.success("✅ Correctly fell back from response to cookies")
    
    @pytest.mark.api
    def test_fallback_chain_all_sources(self):
        """Test complete fallback chain through all sources"""
        self.logger.info("=== Testing Complete Fallback Chain ===")
        
        response = Mock()
        response.json.return_value = {}  # No token in response body
        response.cookies = {}  # No cookies
        response.headers = {"Authorization": "Bearer final_token"}  # Token in header
        
        extractor = TokenExtractor()
        token, method = extractor.extract_token(response)
        
        assert token == "final_token"
        assert method == "header"
        self.logger.success("✅ Fallback chain worked through all sources")

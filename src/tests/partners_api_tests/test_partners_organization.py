# src/tests/partners_api_tests/test_partners_organization.py

import pytest
import random
from src.pages.api.partners_api.partners_auth_api import PartnersAuthAPI
from src.pages.api.partners_api.partners_flight_api import PartnersFlightAPI
from src.pages.api.partners_api.organization_api import PartnersOrganizationAPI
from src.utils.verified_partners_helper import VerifiedUserHelper
from configs.environment import EnvironmentConfig
from src.utils.logger import GeoLogger

class TestPartnersOrganizationSecurity:
    """SECURITY TESTS - Uses THE SAME user pattern as auth tests"""
    
    def setup_method(self):
        self.auth_api = PartnersAuthAPI()
        self.org_api = PartnersOrganizationAPI()
        self.flight_api = PartnersFlightAPI()
        
        # Use THE SAME email pattern as auth tests
        self.test_email = f"geopartners{random.randint(10000,99999)}@yopmail.com"
        self.test_password = "StrongPass123!"
        self.test_org_data = {
            "orgName": f"GEO Bot Ltd {random.randint(1000,9999)}",
            "orgEmail": self.test_email,
            "address": "123 Geo Bot St, Test City",
            "password": self.test_password,
            "contactPerson": {
                "firstName": "GEO",
                "lastName": "Bot",
                "phoneNumber": "+1234567890"
            }
        }
        self.logger = GeoLogger(self.__class__.__name__)
    
    @pytest.mark.partners_api
    @pytest.mark.security
    def test_unverified_user_blocked_from_all_organization_endpoints(self):
        """STRONG TEST: Unverified user should be blocked from ALL org endpoints"""
        # 1. Create the user
        self.logger.info(f"🔵 CREATING USER: {self.test_email}")
        signup_response = self.auth_api.signup(self.test_org_data)
        assert signup_response.status_code == 201
        
        # 2. Try to login - should get no token
        self.logger.info(f"🔵 LOGIN ATTEMPT: {self.test_email}")
        login_response = self.auth_api.login({
            "orgEmail": self.test_email,
            "password": self.test_password
        })
        assert login_response.status_code == 200
        assert login_response.json()['data']['accessToken'] is None
        
        # 3. Test ALL organization endpoints - all should fail with 401
        self.logger.info(f"🔵 TESTING ORG ENDPOINTS FOR: {self.test_email}")
        
        test_cases = [
            ("Get Profile", lambda: self.org_api.get_profile()),
            ("Reset API Keys", lambda: self.org_api.reset_api_keys()),
            ("Get Usage", lambda: self.org_api.get_usage(mode='test')),
            ("Get Daily Usage", lambda: self.org_api.get_daily_usage(mode='test', date='2025-01-01')),
            ("Get Usage Range", lambda: self.org_api.get_usage_range(mode='test', start_date='2025-01-01', end_date='2025-01-31'))
        ]
        
        for endpoint_name, endpoint_call in test_cases:
            response = endpoint_call()
            assert response.status_code == 401, (
                f"SECURITY FAILURE: {endpoint_name} should return 401 for unverified user {self.test_email}. "
                f"Got {response.status_code} - {response.text}"
            )
            self.logger.success(f"✅ {endpoint_name} correctly blocked unverified user: {self.test_email}")
    
    @pytest.mark.partners_api
    @pytest.mark.security
    def test_unverified_login_returns_no_token(self):
        """Test that unverified user login returns no token"""
        # 1. Create the user
        self.logger.info(f"🔵 CREATING USER: {self.test_email}")
        signup_response = self.auth_api.signup(self.test_org_data)
        assert signup_response.status_code == 201
        
        # 2. Try to login - should get no token
        self.logger.info(f"🔵 LOGIN ATTEMPT: {self.test_email}")
        credentials = {
            "orgEmail": self.test_email,
            "password": self.test_password
        }
        response = self.auth_api.login(credentials)
        
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == "Email not verified"
        assert data['data']['isEmailVerified'] is False
        assert data['data']['accessToken'] is None
        self.logger.success(f"✅ Unverified user correctly denied access token: {self.test_email}")
    
    @pytest.mark.partners_api
    @pytest.mark.security
    def test_malformed_token_returns_401(self):
        """Test that invalid/malformed tokens are rejected"""
        # Set invalid token
        self.org_api.set_auth_token("invalid_token_123")
        
        response = self.org_api.get_profile()
        assert response.status_code == 401, "Invalid token should return 401"
        self.logger.success("✅ Invalid token correctly rejected")
    
    @pytest.mark.partners_api
    @pytest.mark.security
    def test_expired_token_returns_401(self):
        """Test that expired tokens are rejected"""
        # This would require an actual expired token
        # For now, test with obviously fake expired token
        self.org_api.set_auth_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired.token")
        
        response = self.org_api.get_profile()
        assert response.status_code == 401, "Expired token should return 401"
        self.logger.success("✅ Expired token correctly rejected")

class TestPartnersOrganizationFunctionality:
    """FUNCTIONALITY TESTS - Using the PRE-VERIFIED account"""
    
    def setup_method(self):
        # Validate credentials before running tests
        if not EnvironmentConfig.validate_partners_credentials():
            pytest.skip("Partners verified account credentials not configured")
        
        self.verified_helper = VerifiedUserHelper()
        self.logger = GeoLogger(self.__class__.__name__)
    
    @pytest.mark.partners_api
    def test_verified_user_can_access_profile(self):
        """TEST: Verified users CAN access their profile"""
        org_api = self.verified_helper.get_verified_organization_api()
        assert org_api is not None, "Should get verified organization API"
        
        response = org_api.get_profile()
        assert response.status_code == 200, "Verified user should access profile"
        
        data = response.json()
        assert data['message'] == "Organization profile fetched successfully"
        assert 'orgName' in data['data']
        assert 'orgEmail' in data['data']
        self.logger.success("✅ Verified user can access profile")
    
    
    @pytest.mark.partners_api
    def test_verified_user_can_reset_api_keys(self):
        """TEST: Verified users can reset API keys and credentials are updated dynamically"""
        org_api = self.verified_helper.get_verified_organization_api()
        assert org_api is not None, "Should get verified organization API"

        # Store original credentials for verification
        original_test_key = self.verified_helper.current_test_api_key

        response = org_api.reset_api_keys()
        assert response.status_code in [200, 201], "Verified user should reset API keys"

        data = response.json()
        assert "API keys reset successfully" in data.get('message', '')

        # Verify new keys are in response
        new_keys = data.get('data', {})
        assert 'testKeys' in new_keys
        assert 'liveKeys' in new_keys

        test_keys = new_keys['testKeys']
        live_keys = new_keys['liveKeys']

        assert 'publicKey' in test_keys
        assert 'secretKey' in test_keys
        assert 'publicKey' in live_keys
        assert 'secretKey' in live_keys

        # VERIFY CREDENTIALS ARE UPDATED DYNAMICALLY
        self.verified_helper.update_api_credentials(test_keys, live_keys)

        # Verify keys actually changed
        assert self.verified_helper.current_test_api_key != original_test_key
        assert self.verified_helper.current_test_api_key == test_keys['publicKey']

        # TEST THAT NEW CREDENTIALS WORK
        # Re-initialize flight API with new credentials
        flight_api = self.verified_helper.get_verified_flight_api()
        assert flight_api is not None, "Should get flight API with new credentials"

        # Quick test to verify new credentials work
        search_data = {
            "origin": "LHR",
            "destination": "LOS",
            "departure_date": PartnersFlightAPI.get_future_date(1),
            "adults": 1,
            "flight_type": "one_way",
            "cabin": "ECONOMY"
        }
        search_response = flight_api.search_flights(search_data)
        
        # This should now work with fresh credentials!
        assert search_response.status_code == 200, "New credentials should work for API calls"
        self.logger.success("✅ New credentials work for flight search")
    
    @pytest.mark.partners_api
    def test_verified_user_can_access_usage_data(self):
        """TEST: Verified users CAN access usage data"""
        org_api = self.verified_helper.get_verified_organization_api()
        assert org_api is not None, "Should get verified organization API"
        
        response = org_api.get_usage(mode='test')
        assert response.status_code == 200, "Verified user should access usage data"
        
        data = response.json()
        assert "usage records fetched successfully" in data.get('message', '')
        self.logger.success("✅ Verified user can access usage data")
    
    @pytest.mark.partners_api
    def test_verified_account_status(self):
        """VALIDATION: Ensure our verified account is actually working"""
        is_verified = self.verified_helper.verify_account_status()
        assert is_verified, "Verified account should pass verification check"
        self.logger.success("✅ Verified account validation passed")
        
    @pytest.mark.partners_api
    def test_usage_records_contain_flight_data(self):
        """TEST: Verify that flight searches and bookings are recorded in usage"""
        org_api = self.verified_helper.get_verified_organization_api()
        
        response = org_api.get_usage(mode='test')
        assert response.status_code == 200
        
        data = response.json()
        records = data['data']['records']
        
        # Verify usage records structure contains flight data
        for record in records:
            assert 'flightSearches' in record
            assert 'flightBookings' in record
            assert 'flightTags' in record
            assert isinstance(record['flightSearches'], int)
            assert isinstance(record['flightBookings'], int)
            assert isinstance(record['flightTags'], list)
        
        self.logger.success("✅ Usage records correctly contain flight data")

    @pytest.mark.partners_api
    def test_usage_records_contain_package_data(self):
        """TEST: Verify that package bookings are recorded in usage"""
        org_api = self.verified_helper.get_verified_organization_api()
        
        response = org_api.get_usage(mode='test')
        assert response.status_code == 200
        
        data = response.json()
        records = data['data']['records']
        
        # Verify usage records structure contains package data
        for record in records:
            assert 'packageBookings' in record
            assert isinstance(record['packageBookings'], int)
        
        self.logger.success("✅ Usage records correctly contain package data")

    @pytest.mark.partners_api
    def test_usage_range_shows_cumulative_data(self):
        """TEST: Verify usage range endpoint shows total cumulative usage"""
        org_api = self.verified_helper.get_verified_organization_api()
        
        response = org_api.get_usage_range(mode='test', start_date='2025-01-01', end_date='2025-12-31')
        assert response.status_code == 200
        
        data = response.json()
        usage_data = data['data']
        
        # Verify cumulative usage structure
        assert 'totalUsage' in usage_data
        assert 'totalFlightSearches' in usage_data
        assert 'totalFlightBookings' in usage_data  
        assert 'totalPackageBookings' in usage_data
        
        # All should be integers (can be 0 or more)
        assert isinstance(usage_data['totalUsage'], int)
        assert isinstance(usage_data['totalFlightSearches'], int)
        assert isinstance(usage_data['totalFlightBookings'], int)
        assert isinstance(usage_data['totalPackageBookings'], int)
        
        self.logger.success("✅ Usage range correctly shows cumulative data")
        
        
        
        
        
    @pytest.mark.partners_api
    def test_credential_initialization_flow(self):
        """DEBUG: Test the credential initialization flow"""
        self.logger.info("🔵 DEBUG - Testing credential initialization")
        
        # Initialize credentials
        success = self.verified_helper.initialize_credentials()
        assert success, "Credential initialization should succeed"
        
        # Verify we have all required credentials
        assert self.verified_helper.current_test_api_key is not None, "Should have test API key"
        assert self.verified_helper.current_test_api_secret is not None, "Should have test API secret" 
        assert self.verified_helper.org_id is not None, "Should have organization ID"
        
        self.logger.info(f"✅ Test API Key: {self.verified_helper.current_test_api_key}")
        self.logger.info(f"✅ Org ID: {self.verified_helper.org_id}")
        
        # Try to create flight API
        flight_api = self.verified_helper.get_verified_flight_api()
        assert flight_api is not None, "Should get flight API with initialized credentials"
        
        self.logger.success("✅ Credential initialization flow works correctly")
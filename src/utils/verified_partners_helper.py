# src/utils/verified_partners_helper.py

from src.pages.api.partners_api.partners_auth_api import PartnersAuthAPI
from src.pages.api.partners_api.organization_api import PartnersOrganizationAPI
from src.pages.api.partners_api.partners_flight_api import PartnersFlightAPI
from src.pages.api.partners_api.partners_package_api import PartnersPackageAPI
from src.utils.token_extractor import TokenExtractor
from configs.environment import EnvironmentConfig
from src.utils.logger import GeoLogger
import os
import json

class VerifiedUserHelper:
    """Professional helper for verified user testing"""
    
    def __init__(self):
        self.auth_api = PartnersAuthAPI()
        self.logger = GeoLogger("VerifiedUserHelper")
        
        if not EnvironmentConfig.validate_partners_credentials():
            self.logger.error("Partners verified account credentials are invalid or missing")
            raise ValueError("Partners verified account credentials not properly configured")
        
        self.verified_account = EnvironmentConfig.get_verified_partners_account()
        self.current_test_api_key = os.getenv("PARTNERS_TEST_API_KEY")
        self.current_test_api_secret = os.getenv("PARTNERS_TEST_API_SECRET") 
        self.current_live_api_key = os.getenv("PARTNERS_LIVE_API_KEY")
        self.current_live_api_secret = os.getenv("PARTNERS_LIVE_API_SECRET")
        self.org_id = None
        self.verified_org_api = None
        
        self.logger.info("VerifiedUserHelper initialized")
        
    def initialize_credentials(self):
        """Initialize API credentials from verified organization."""
        self.logger.info("Initializing API credentials...")
        
        org_api = self.get_verified_organization_api()
        if not org_api:
            self.logger.error("Cannot initialize credentials - cannot get organization API")
            return False
        
        profile_response = org_api.get_profile()
        if profile_response.status_code != 200:
            self.logger.error(f"Cannot get organization profile: {profile_response.status_code}")
            return False
        
        profile_data = profile_response.json()
        self.org_id = profile_data['data']['id']
        self.logger.debug(f"Organization ID: {self.org_id}")
        
        reset_response = org_api.reset_api_keys()
        if reset_response.status_code not in [200, 201]:
            self.logger.error(f"Cannot reset API keys: {reset_response.status_code}")
            return False
        
        reset_data = reset_response.json()
        new_keys = reset_data.get('data', {})
        test_keys = new_keys.get('testKeys', {})
        
        self.update_api_credentials(test_keys, {})
        
        self.logger.info("API credentials initialized successfully")
        return True
    
    def get_verified_package_api(self, environment='test'):
        """Get package API with current credentials, initializing if needed."""
        if not self.current_test_api_key or not self.org_id:
            self.logger.warning("Credentials not initialized, initializing now...")
            if not self.initialize_credentials():
                self.logger.error("Failed to initialize credentials for package API")
                return None
        
        if environment == 'test':
            api_key = self.current_test_api_key
            api_secret = self.current_test_api_secret
        else:
            api_key = self.current_live_api_key
            api_secret = self.current_live_api_secret
            
        if api_key and api_secret:
            self.logger.info(f"Creating package API with {environment} credentials")
            return PartnersPackageAPI(
                api_key=api_key,
                api_secret=api_secret,
                app_id=self.org_id
            )
        else:
            self.logger.error(f"No {environment} API credentials available")
            return None
    
    def get_verified_access_token(self):
        """Get access token from verified account using dynamic token extraction."""
        self.logger.info("Obtaining access token from verified account")
        
        login_response = self.auth_api.login({
            "orgEmail": self.verified_account["email"],
            "password": self.verified_account["password"]
        })
        
        if login_response.status_code == 200:
            token_extractor = TokenExtractor()
            token, extraction_method = token_extractor.extract_token(login_response)
            
            if token:
                is_valid = token_extractor.validate_token(token)
                if is_valid:
                    self.logger.info(f"Access token obtained successfully via {extraction_method}")
                    return token
                else:
                    self.logger.warning("Token extracted but validation failed")
                    return None
            else:
                self.logger.warning("Verified account login returned no token")
                return None
        else:
            self.logger.error(f"Verified account login failed: {login_response.status_code}")
            return None
    
    def get_verified_organization_api(self):
        """Get Organization API instance with verified user token."""
        token = self.get_verified_access_token()
        if token:
            org_api = PartnersOrganizationAPI(auth_token=token)
            return org_api
        return None
    
    def verify_account_status(self):
        """Verify that the account is actually verified."""
        token = self.get_verified_access_token()
        if not token:
            return False
            
        org_api = PartnersOrganizationAPI(auth_token=token)
        response = org_api.get_profile()
        
        if response.status_code == 200:
            self.logger.info("Verified account can access protected endpoints")
            return True
        else:
            self.logger.error(f"Verified account cannot access endpoints: {response.status_code}")
            return False
        
    def get_verified_flight_api(self, environment='test'):
        """Get flight API with current credentials, initializing if needed."""
        # Check if credentials are initialized
        if not self.current_test_api_key or not self.current_test_api_secret or not self.org_id:
            self.logger.debug("Credentials missing, initializing now...")
            if not self.initialize_credentials():
                self.logger.error("Failed to initialize credentials for flight API")
                return None
        
        api_key = self.current_test_api_key if environment == 'test' else self.current_live_api_key
        api_secret = self.current_test_api_secret if environment == 'test' else self.current_live_api_secret
            
        if api_key and api_secret and self.org_id:
            self.logger.info(f"Creating flight API with {environment} credentials")
            return PartnersFlightAPI(
                api_key=api_key,
                api_secret=api_secret,
                app_id=self.org_id
            )
        else:
            self.logger.error("Missing credentials after initialization")
            return None
    
    def update_api_credentials(self, new_test_keys=None, new_live_keys=None):
        """Update current API credentials after reset."""
        if new_test_keys:
            self.current_test_api_key = new_test_keys.get('publicKey')
            self.current_test_api_secret = new_test_keys.get('secretKey')
            self.logger.info("TEST API credentials updated")
    
    def reset_api_keys_and_update(self):
        """Reset API keys and automatically update credentials."""
        org_api = self.get_verified_organization_api()
        if not org_api:
            self.logger.error("Cannot reset API keys - no verified organization API")
            return False
            
        self.logger.info("Resetting API keys...")
        response = org_api.reset_api_keys()
        
        if response.status_code in [200, 201]:
            data = response.json()
            new_keys = data.get('data', {})
            test_keys = new_keys.get('testKeys', {})
            live_keys = new_keys.get('liveKeys', {})
            
            self.update_api_credentials(test_keys, live_keys)
            self.logger.info("API keys reset and credentials updated successfully")
            return True
        else:
            self.logger.error(f"Failed to reset API keys: {response.status_code}")
            return False
# src/utils/verified_partners_helper.py

from src.pages.api.partners_api.partners_auth_api import PartnersAuthAPI
from src.pages.api.partners_api.organization_api import PartnersOrganizationAPI
from src.pages.api.partners_api.partners_flight_api import PartnersFlightAPI
from src.pages.api.partners_api.partners_package_api import PartnersPackageAPI
from configs.environment import EnvironmentConfig
from src.utils.logger import GeoLogger
import os
import json

class VerifiedUserHelper:
    """Professional helper for verified user testing"""
    
    def __init__(self):
        self.auth_api = PartnersAuthAPI()
        self.logger = GeoLogger("VerifiedUserHelper")
        
        # Validate credentials on initialization
        if not EnvironmentConfig.validate_partners_credentials():
            self.logger.error("❌ Partners verified account credentials are invalid or missing")
            raise ValueError("Partners verified account credentials not properly configured")
        
        self.verified_account = EnvironmentConfig.get_verified_partners_account()
        
        # Initialize API credentials from environment
        self.current_test_api_key = os.getenv("PARTNERS_TEST_API_KEY")
        self.current_test_api_secret = os.getenv("PARTNERS_TEST_API_SECRET") 
        self.current_live_api_key = os.getenv("PARTNERS_LIVE_API_KEY")
        self.current_live_api_secret = os.getenv("PARTNERS_LIVE_API_SECRET")
        self.org_id = None
        
        self.verified_org_api = None
        
        self.logger.info("✅ VerifiedUserHelper initialized")
        
    def initialize_credentials(self):
        self.logger.info("🔄 Initializing API credentials...")
        
        # 1. Get organization API with auth token
        org_api = self.get_verified_organization_api()
        if not org_api:
            self.logger.error("❌ Cannot initialize credentials - cannot get organization API")
            return False
        
        # 2. Get organization profile to extract org ID
        profile_response = org_api.get_profile()
        if profile_response.status_code != 200:
            self.logger.error(f"❌ Cannot get organization profile: {profile_response.status_code}")
            return False
        
        profile_data = profile_response.json()
        self.org_id = profile_data['data']['id']
        self.logger.info(f"📋 Organization ID: {self.org_id}")
        
        # 3. Reset API keys to get fresh credentials
        reset_response = org_api.reset_api_keys()
        if reset_response.status_code not in [200, 201]:
            self.logger.error(f"❌ Cannot reset API keys: {reset_response.status_code}")
            return False
        
        reset_data = reset_response.json()
        
        # 5. Extract the REAL keys
        new_keys = reset_data.get('data', {})
        test_keys = new_keys.get('testKeys', {})
        
        self.logger.info(f"🔍 REAL TEST PUBLIC KEY: {test_keys.get('publicKey')}")
        self.logger.info(f"🔍 REAL TEST SECRET KEY: {test_keys.get('secretKey')}")
        
        # 6. Update credentials with REAL keys
        self.update_api_credentials(test_keys, {})
        
        self.logger.success("✅ API credentials initialized successfully")
        return True
    
    def get_verified_flight_api(self, environment='test'):
        """Get flight API with current credentials - ensures credentials are initialized"""
        # Ensure credentials are initialized
        if not self.current_test_api_key or not self.org_id:
            self.logger.warning("🔄 Credentials not initialized, initializing now...")
            if not self.initialize_credentials():
                self.logger.error("❌ Failed to initialize credentials for flight API")
                return None
        
        if environment == 'test':
            api_key = self.current_test_api_key
            api_secret = self.current_test_api_secret
        else:
            api_key = self.current_live_api_key
            api_secret = self.current_live_api_secret
            
        if api_key and api_secret:
            self.logger.info(f"Creating flight API with {environment} credentials")
            return PartnersFlightAPI(
                api_key=api_key,
                api_secret=api_secret,
                app_id=self.org_id  # Use org ID as app_id
            )
        else:
            self.logger.error(f"❌ No {environment} API credentials available")
            return None

    def get_verified_package_api(self, environment='test'):
        """Get package API with current credentials - ensures credentials are initialized"""
        # Ensure credentials are initialized
        if not self.current_test_api_key or not self.org_id:
            self.logger.warning("🔄 Credentials not initialized, initializing now...")
            if not self.initialize_credentials():
                self.logger.error("❌ Failed to initialize credentials for package API")
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
                app_id=self.org_id  # Use org ID as app_id
            )
        else:
            self.logger.error(f"❌ No {environment} API credentials available")
            return None
    
    def get_verified_access_token(self):
        """Get access token from verified account"""
        self.logger.info("Getting access token from verified account")
        
        login_response = self.auth_api.login({
            "orgEmail": self.verified_account["email"],
            "password": self.verified_account["password"]
        })
        
        if login_response.status_code == 200:
            data = login_response.json()
            if data.get('data', {}).get('accessToken'):
                token = data['data']['accessToken']
                self.logger.success("Successfully obtained verified user access token")
                return token
            else:
                self.logger.error("Verified account login returned no access token")
                return None
        else:
            self.logger.error(f"Verified account login failed: {login_response.status_code}")
            return None
    
    def get_verified_organization_api(self):
        """Get Organization API instance with verified user token"""
        token = self.get_verified_access_token()
        if token:
            org_api = PartnersOrganizationAPI(auth_token=token)
            return org_api
        return None
    
    def verify_account_status(self):
        """Verify that the account is actually verified"""
        token = self.get_verified_access_token()
        if not token:
            return False
            
        # Test access to protected endpoint
        org_api = PartnersOrganizationAPI(auth_token=token)
        response = org_api.get_profile()
        
        if response.status_code == 200:
            self.logger.success("Verified account can access protected endpoints")
            return True
        else:
            self.logger.error(f"Verified account cannot access endpoints: {response.status_code}")
            return False
        
    def get_verified_flight_api(self, environment='test'):
        """Get flight API with current credentials - FIX THIS METHOD!"""
        # Check if we have ALL required credentials
        if not self.current_test_api_key or not self.current_test_api_secret or not self.org_id:
            self.logger.warning("🔄 Credentials not initialized, initializing now...")
            if not self.initialize_credentials():  # ← THIS MUST BE CALLED!
                self.logger.error("❌ Failed to initialize credentials for flight API")
                return None
        
        if environment == 'test':
            api_key = self.current_test_api_key
            api_secret = self.current_test_api_secret
        else:
            api_key = self.current_live_api_key
            api_secret = self.current_live_api_secret
            
        if api_key and api_secret and self.org_id:
            self.logger.info(f"Creating flight API with {environment} credentials")
            return PartnersFlightAPI(
                api_key=api_key,
                api_secret=api_secret,
                app_id=self.org_id
            )
        else:
            self.logger.error(f"❌ Missing credentials after initialization!")
            return None

    def get_verified_flight_api(self, environment='test'):
        """Get flight API with current credentials"""
        self.logger.info(f"🔍 get_verified_flight_api() called - checking credentials...")
        self.logger.info(f"🔍 Current test key: {self.current_test_api_key}")
        self.logger.info(f"🔍 Current org_id: {self.org_id}")
        
        # Check if we have ALL required credentials
        if not self.current_test_api_key or not self.current_test_api_secret or not self.org_id:
            self.logger.info(f"🔍 Credentials missing, calling initialize_credentials()...")
            if not self.initialize_credentials():
                self.logger.error("❌ Failed to initialize credentials for flight API")
                return None
        else:
            self.logger.info(f"🔍 Credentials already initialized")
        
        if environment == 'test':
            api_key = self.current_test_api_key
            api_secret = self.current_test_api_secret
        else:
            api_key = self.current_live_api_key
            api_secret = self.current_live_api_secret
            
        self.logger.info(f"🔍 Final credentials check:")
        self.logger.info(f"   API Key: {api_key}")
        self.logger.info(f"   API Secret: {api_secret}") 
        self.logger.info(f"   Org ID: {self.org_id}")
        
        if api_key and api_secret and self.org_id:
            self.logger.info(f"✅ All credentials present, creating Flight API")
            self.logger.info(f"Creating flight API with {environment} credentials")
            return PartnersFlightAPI(
                api_key=api_key,
                api_secret=api_secret,
                app_id=self.org_id
            )
        else:
            self.logger.info(f"❌ Missing credentials after initialization!")
            self.logger.info(f"   Key present: {api_key is not None}")
            self.logger.info(f"   Secret present: {api_secret is not None}")
            self.logger.info(f"   Org ID present: {self.org_id is not None}")
            return None
    
    def update_api_credentials(self, new_test_keys=None, new_live_keys=None):
        """Update current API credentials after reset"""
        if new_test_keys:
            self.current_test_api_key = new_test_keys.get('publicKey')
            self.current_test_api_secret = new_test_keys.get('secretKey')
            
            # DEBUG: Verify we're setting REAL values
            self.logger.info(f"🔍 SETTING REAL VALUES:")
            self.logger.info(f"   Public Key: {self.current_test_api_key}")
            self.logger.info(f"   Secret Key: {self.current_test_api_secret}")
            
            self.logger.info("🔄 Updated TEST API credentials")
    
    def reset_api_keys_and_update(self):
        """Reset API keys and automatically update credentials"""
        org_api = self.get_verified_organization_api()
        if not org_api:
            self.logger.error("❌ Cannot reset API keys - no verified organization API")
            return False
            
        self.logger.info("🔄 Resetting API keys...")
        response = org_api.reset_api_keys()
        
        if response.status_code in [200, 201]:
            data = response.json()
            new_keys = data.get('data', {})
            
            # Extract new keys from response
            test_keys = new_keys.get('testKeys', {})
            live_keys = new_keys.get('liveKeys', {})
            
            # Update our current credentials
            self.update_api_credentials(test_keys, live_keys)
            
            self.logger.success("✅ API keys reset and credentials updated dynamically")
            return True
        else:
            self.logger.error(f"❌ Failed to reset API keys: {response.status_code}")
            return False
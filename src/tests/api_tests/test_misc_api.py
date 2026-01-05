# src/tests/api_tests/test_misc_apis.py

import pytest
from src.pages.api.google_reviews_api import GoogleAPI
from src.pages.api.commercial_deals_api import CommercialAPI
from src.pages.api.events_api import EventAPI
from src.pages.api.hotels_api import HotelAPI
from src.pages.api.flight_utils_api import FlightUtilsAPI
from src.pages.api.blogs_api import BlogAPI
from src.pages.api.auth_api import AuthAPI
from src.pages.api.users_api import UserAPI
from src.pages.api.transactions_api import TransactionAPI
from src.pages.api.notification_api import NotificationAPI
from src.pages.api.newsletter_api import NewsletterAPI
from src.pages.api.price_api import PriceAPI
from src.utils.logger import GeoLogger

class TestMiscAPIs:
    
    def setup_method(self):
        self.logger = GeoLogger(self.__class__.__name__)
    
    @pytest.fixture
    def authenticated_api(self):
        """Fixture that logs in and returns auth_api with proper token source"""
        auth_api = AuthAPI()
        response = auth_api.login()
        
        if response.status_code != 200:
            self.logger.error(f"❌ Login failed with status {response.status_code}")
            pytest.skip(f"Login failed with status {response.status_code}")
        
        self.logger.success(f"✅ Authenticated successfully (token length: {len(auth_api.auth_token)})")
        return auth_api
    
    # Helper method to set auth token correctly on any API instance
    def _set_auth_on_api(self, api_instance, auth_api):
        """Set authentication on API instance with proper token source"""
        if hasattr(auth_api, 'token_source') and auth_api.token_source:
            api_instance.set_auth_token(auth_api.auth_token, token_source=auth_api.token_source)
        else:
            api_instance.set_auth_token(auth_api.auth_token)
    
    # Google Reviews Tests
    @pytest.mark.api
    def test_get_google_reviews(self, authenticated_api):
        self.logger.info("=== Testing Get Google Reviews ===")
        api = GoogleAPI()
        self._set_auth_on_api(api, authenticated_api)
        response = api.get_reviews()
        if response is None:
            self.logger.error("Response is None. Skipping test.")
            pytest.skip("Response is None. Skipping test.")
        elif hasattr(response, 'status_code') and response.status_code >= 400:
            self.logger.error(f"API Error: {response.status_code} - {response.text}")
            pytest.fail(f"API Error: {response.status_code}")
        self.logger.info(f"Google Reviews: {response.status_code}")
        assert response.status_code == 200
    
    # Commercial Deals Tests
    @pytest.mark.api
    def test_get_commercial_deals(self, authenticated_api):
        self.logger.info("=== Testing Get Commercial Deals ===")
        api = CommercialAPI()
        self._set_auth_on_api(api, authenticated_api)
        response = api.get_all_deals(limit=5)
        if response is None:
            self.logger.error("Response is None. Skipping test.")
            pytest.skip("Response is None. Skipping test.")
        elif hasattr(response, 'status_code') and response.status_code >= 400:
            self.logger.error(f"API Error: {response.status_code} - {response.text}")
            pytest.fail(f"API Error: {response.status_code}")
        self.logger.info(f"Commercial Deals: {response.status_code}")
        assert response.status_code == 200
    
    @pytest.mark.api
    def test_get_single_commercial_deal(self, authenticated_api):
        self.logger.info("=== Testing Get Single Commercial Deal ===")
        api = CommercialAPI()
        self._set_auth_on_api(api, authenticated_api)
        all_deals = api.get_all_deals(limit=1)
        if all_deals.status_code == 200 and all_deals.json():
            data = all_deals.json()
            items = data.get('data', data) if isinstance(data, dict) else data
            if items and len(items) > 0:
                deal_id = items[0].get('id', 1)
                response = api.get_single_deal(deal_id)
                if response is None:
                    self.logger.error("Response is None. Skipping test.")
                    pytest.skip("Response is None. Skipping test.")
                elif hasattr(response, 'status_code') and response.status_code >= 400:
                    self.logger.error(f"API Error: {response.status_code} - {response.text}")
                    pytest.fail(f"API Error: {response.status_code}")
                self.logger.info(f"Single Commercial Deal: {response.status_code}")
                assert response.status_code in [200, 404]
    
    # Events Tests
    @pytest.mark.api
    def test_get_all_events(self, authenticated_api):
        self.logger.info("=== Testing Get All Events ===")
        api = EventAPI()
        self._set_auth_on_api(api, authenticated_api)
        response = api.get_all_events(limit=5)
        if response is None:
            self.logger.error("Response is None. Skipping test.")
            pytest.skip("Response is None. Skipping test.")
        elif hasattr(response, 'status_code') and response.status_code >= 400:
            self.logger.error(f"API Error: {response.status_code} - {response.text}")
            pytest.fail(f"API Error: {response.status_code}")
        self.logger.info(f"All Events: {response.status_code}")
        assert response.status_code == 200
    
    # Flight Utilities Tests
    @pytest.mark.api
    def test_get_airports(self, authenticated_api):
        self.logger.info("=== Testing Get Airports ===")
        api = FlightUtilsAPI()
        self._set_auth_on_api(api, authenticated_api)
    
    # Blog Tests
    @pytest.mark.api
    def test_get_all_blogs(self, authenticated_api):
        self.logger.info("=== Testing Get All Blogs ===")
        api = BlogAPI()
        self._set_auth_on_api(api, authenticated_api)
        response = api.get_all_blogs(limit=5)
        if response is None:
            self.logger.error("Response is None. Skipping test.")
            pytest.skip("Response is None. Skipping test.")
        elif hasattr(response, 'status_code') and response.status_code >= 400:
            self.logger.error(f"API Error: {response.status_code} - {response.text}")
            pytest.fail(f"API Error: {response.status_code}")
        self.logger.info(f"All Blogs: {response.status_code}")
        assert response.status_code == 200
    
    @pytest.mark.api
    def test_get_single_blog(self, authenticated_api):
        self.logger.info("=== Testing Get Single Blog ===")
        api = BlogAPI()
        self._set_auth_on_api(api, authenticated_api)
        all_blogs = api.get_all_blogs(limit=1)
        if all_blogs.status_code == 200:
            data = all_blogs.json()
            # Handle blog response structure: data -> data
            if isinstance(data, dict) and 'data' in data:
                items = data['data']
            else:
                items = data if isinstance(data, list) else []

            if items and len(items) > 0:
                blog_id = items[0].get('id')
                if blog_id:
                    response = api.get_single_blog(blog_id)
                    if response is None:
                        self.logger.error("Response is None. Skipping test.")
                        pytest.skip("Response is None. Skipping test.")
                    elif hasattr(response, 'status_code') and response.status_code >= 400:
                        self.logger.error(f"API Error: {response.status_code} - {response.text}")
                        pytest.fail(f"API Error: {response.status_code}")
                    self.logger.info(f"Single Blog: {response.status_code}")
                    assert response.status_code in [200, 404]
    
    @pytest.mark.api
    def test_get_blog_comments(self, authenticated_api):
        self.logger.info("=== Testing Get Blog Comments ===")
        api = BlogAPI()
        self._set_auth_on_api(api, authenticated_api)
        all_blogs = api.get_all_blogs(limit=1)
        if all_blogs.status_code == 200:
            data = all_blogs.json()
            # Handle blog response structure: data -> data
            if isinstance(data, dict) and 'data' in data:
                items = data['data']
            else:
                items = data if isinstance(data, list) else []

            if items and len(items) > 0:
                blog_id = items[0].get('id')
                if blog_id:
                    response = api.get_blog_comments(blog_id)
                    if response is None:
                        self.logger.error("Response is None. Skipping test.")
                        pytest.skip("Response is None. Skipping test.")
                    elif hasattr(response, 'status_code') and response.status_code >= 400:
                        self.logger.error(f"API Error: {response.status_code} - {response.text}")
                        pytest.fail(f"API Error: {response.status_code}")
                    self.logger.info(f"Blog Comments: {response.status_code}")
                    assert response.status_code in [200, 404]
    
    # User Authentication Tests                    
    @pytest.mark.api
    def test_refresh_token(self, authenticated_api):
        self.logger.info("=== Testing Refresh Token ===")
        api = AuthAPI()
        self._set_auth_on_api(api, authenticated_api)
        response = api.refresh_token()
        self.logger.info(f"Refresh Token: {response.status_code}")
        assert response.status_code in [200, 400, 401]

    # User Tests  
    @pytest.mark.api
    def test_get_user_profile(self, authenticated_api):
        self.logger.info("=== Testing Get User Profile ===")
        api = UserAPI()
        self._set_auth_on_api(api, authenticated_api)
        response = api.get_user_profile()
        self.logger.info(f"User Profile: {response.status_code}")
        assert response.status_code == 200

    # Transactions Tests
    @pytest.mark.api
    def test_get_user_transactions(self, authenticated_api):
        self.logger.info("=== Testing Get User Transactions ===")
        api = TransactionAPI()
        self._set_auth_on_api(api, authenticated_api)
        response = api.get_user_transactions(limit=5)
        self.logger.info(f"User Transactions: {response.status_code}")
        assert response.status_code == 200

    # Notifications Tests
    @pytest.mark.api
    def test_get_notifications(self, authenticated_api):
        self.logger.info("=== Testing Get Notifications ===")
        api = NotificationAPI()
        self._set_auth_on_api(api, authenticated_api)
        response = api.get_notifications()
        print(response)
        self.logger.info(f"Notifications: {response.status_code}")
        assert response.status_code == 200

    # Newsletter Tests
    @pytest.mark.api
    def test_subscribe_newsletter(self, authenticated_api):
        self.logger.info("=== Testing Subscribe Newsletter ===")
        api = NewsletterAPI()
        self._set_auth_on_api(api, authenticated_api)
        subscribe_data = {
            "email": "geo.qa.bot@gmail.com"
        }
        response = api.subscribe_newsletter(subscribe_data)
        self.logger.info(f"Newsletter Subscribe: {response.status_code}")
        assert response.status_code in [200, 201, 400]

    # Voucher Tests
    @pytest.mark.api
    def test_apply_voucher(self, authenticated_api):
        self.logger.info("=== Testing Apply Voucher ===")
        api = PriceAPI()
        self._set_auth_on_api(api, authenticated_api)
        voucher_data = {
            "code": "TEST10"
        }
        response = api.apply_voucher(voucher_data)
        self.logger.info(f"Apply Voucher: {response.status_code}")
        assert response.status_code in [200, 400, 404]
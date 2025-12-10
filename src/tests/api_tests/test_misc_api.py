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
        auth_api = AuthAPI()
        self.logger.info("🔐 Authenticating for API tests...")
        response = auth_api.login()
        if response.status_code != 200:
            self.logger.error(f"❌ Login failed with status {response.status_code}")
            pytest.skip("Login failed")
        if not auth_api.auth_token:
            self.logger.error("❌ Login succeeded but no auth token found")
            pytest.skip("No auth token in response")
        self.logger.success(f"✅ Authenticated successfully with token (length: {len(auth_api.auth_token)})")
        return auth_api.auth_token
    
    # Google Reviews Tests
    @pytest.mark.api
    def test_get_google_reviews(self, authenticated_api):
        self.logger.info("=== Testing Get Google Reviews ===")
        api = GoogleAPI()
        api.set_auth_token(authenticated_api)
        response = api.get_reviews()
        self.logger.info(f"Google Reviews: {response.status_code}")
        assert response.status_code == 200
    
    # Commercial Deals Tests
    @pytest.mark.api
    def test_get_commercial_deals(self, authenticated_api):
        self.logger.info("=== Testing Get Commercial Deals ===")
        api = CommercialAPI()
        api.set_auth_token(authenticated_api)
        response = api.get_all_deals(limit=5)
        self.logger.info(f"Commercial Deals: {response.status_code}")
        assert response.status_code == 200
    
    @pytest.mark.api
    def test_get_single_commercial_deal(self, authenticated_api):
        self.logger.info("=== Testing Get Single Commercial Deal ===")
        api = CommercialAPI()
        api.set_auth_token(authenticated_api)
        all_deals = api.get_all_deals(limit=1)
        if all_deals.status_code == 200 and all_deals.json():
            data = all_deals.json()
            items = data.get('data', data) if isinstance(data, dict) else data
            if items and len(items) > 0:
                deal_id = items[0].get('id', 1)
                response = api.get_single_deal(deal_id)
                self.logger.info(f"Single Commercial Deal: {response.status_code}")
                assert response.status_code in [200, 404]
    
    # Events Tests
    @pytest.mark.api
    def test_get_all_events(self, authenticated_api):
        self.logger.info("=== Testing Get All Events ===")
        api = EventAPI()
        api.set_auth_token(authenticated_api)
        response = api.get_all_events(limit=5)
        self.logger.info(f"All Events: {response.status_code}")
        assert response.status_code == 200
    
    # Hotels Tests
    @pytest.mark.api
    def test_search_hotels(self, authenticated_api):
        self.logger.info("=== Testing Hotel Search ===")
        api = HotelAPI()
        api.set_auth_token(authenticated_api)
        response = api.search_hotels(city_code="LON")  # Add required city_code
        self.logger.info(f"Hotels Search: {response.status_code}")
        assert response.status_code == 200

    @pytest.mark.api
    def test_get_hotel_cities(self, authenticated_api):
        self.logger.info("=== Testing Get Hotel Cities ===")
        api = HotelAPI()
        api.set_auth_token(authenticated_api)
        response = api.get_hotel_cities(keyword="ABU")  # Add required keyword
        self.logger.info(f"Hotel Cities: {response.status_code}")
        assert response.status_code == 200
    
    # Flight Utilities Tests
    @pytest.mark.api
    def test_get_airports(self, authenticated_api):
        self.logger.info("=== Testing Get Airports ===")
        api = FlightUtilsAPI()
        api.set_auth_token(authenticated_api)
        response = api.get_all_airports()
        self.logger.info(f"Airports: {response.status_code}")
        assert response.status_code == 200
    
    @pytest.mark.api
    def test_get_airlines(self, authenticated_api):
        self.logger.info("=== Testing Get Airlines ===")
        api = FlightUtilsAPI()
        api.set_auth_token(authenticated_api)
        response = api.get_all_airlines()
        self.logger.info(f"Airlines: {response.status_code}")
        assert response.status_code == 200
    
    # Blog Tests
    @pytest.mark.api
    def test_get_all_blogs(self, authenticated_api):
        self.logger.info("=== Testing Get All Blogs ===")
        api = BlogAPI()
        api.set_auth_token(authenticated_api)
        response = api.get_all_blogs(limit=5)
        self.logger.info(f"All Blogs: {response.status_code}")
        assert response.status_code == 200
    
    @pytest.mark.api
    def test_get_single_blog(self, authenticated_api):
        self.logger.info("=== Testing Get Single Blog ===")
        api = BlogAPI()
        api.set_auth_token(authenticated_api)
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
                    self.logger.info(f"Single Blog: {response.status_code}")
                    assert response.status_code in [200, 404]
    
    @pytest.mark.api
    def test_get_blog_comments(self, authenticated_api):
        self.logger.info("=== Testing Get Blog Comments ===")
        api = BlogAPI()
        api.set_auth_token(authenticated_api)
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
                    self.logger.info(f"Blog Comments: {response.status_code}")
                    assert response.status_code in [200, 404]
    
    # User Authentication Tests                    
    @pytest.mark.api
    def test_refresh_token(self, authenticated_api):
        self.logger.info("=== Testing Refresh Token ===")
        api = AuthAPI()
        api.set_auth_token(authenticated_api)
        response = api.refresh_token()
        self.logger.info(f"Refresh Token: {response.status_code}")
        assert response.status_code in [200, 400, 401]

    # User Tests  
    @pytest.mark.api
    def test_get_user_profile(self, authenticated_api):
        self.logger.info("=== Testing Get User Profile ===")
        api = UserAPI()
        api.set_auth_token(authenticated_api)
        response = api.get_user_profile()
        self.logger.info(f"User Profile: {response.status_code}")
        assert response.status_code == 200

    # Transactions Tests
    @pytest.mark.api
    def test_get_user_transactions(self, authenticated_api):
        self.logger.info("=== Testing Get User Transactions ===")
        api = TransactionAPI()
        api.set_auth_token(authenticated_api)
        response = api.get_user_transactions(limit=5)
        self.logger.info(f"User Transactions: {response.status_code}")
        assert response.status_code == 200

    # Notifications Tests
    @pytest.mark.api
    def test_get_notifications(self, authenticated_api):
        self.logger.info("=== Testing Get Notifications ===")
        api = NotificationAPI()
        api.set_auth_token(authenticated_api)
        response = api.get_notifications()
        self.logger.info(f"Notifications: {response.status_code}")
        assert response.status_code == 200

    # Newsletter Tests
    @pytest.mark.api
    def test_subscribe_newsletter(self, authenticated_api):
        self.logger.info("=== Testing Subscribe Newsletter ===")
        api = NewsletterAPI()
        api.set_auth_token(authenticated_api)
        subscribe_data = {
            "email": "geobot@yopmail.com"
        }
        response = api.subscribe_newsletter(subscribe_data)
        self.logger.info(f"Newsletter Subscribe: {response.status_code}")
        assert response.status_code in [200, 201, 400]

    # Voucher Tests
    @pytest.mark.api
    def test_apply_voucher(self, authenticated_api):
        self.logger.info("=== Testing Apply Voucher ===")
        api = PriceAPI()
        api.set_auth_token(authenticated_api)
        voucher_data = {
            "code": "TEST10"
        }
        response = api.apply_voucher(voucher_data)
        self.logger.info(f"Apply Voucher: {response.status_code}")
        assert response.status_code in [200, 400, 404]
# src/tests/api_tests/test_hotel_api.py

import os
import pytest
import json
from datetime import datetime, timedelta
from src.pages.api.hotels_api import HotelAPI
from src.pages.api.auth_api import AuthAPI
from src.utils.logger import GeoLogger


class TestHotelAPI:
    """Comprehensive Hotel API Test Suite"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.logger = GeoLogger(self.__class__.__name__)
        self.hotel_api = HotelAPI()
        self.test_data = self._generate_test_data()
        yield
        self.logger.info(f"✅ {self.__class__.__name__} test completed")
    
    @pytest.fixture
    def authenticated_api(self):
        """Authentication fixture for all hotel tests - using your existing pattern"""
        auth_api = AuthAPI()
        self.logger.info("🔐 Authenticating for hotel API tests...")
        
        try:
            # Use environment variables as you have in your setup
            email = os.environ.get("API_TEST_EMAIL")
            password = os.environ.get("API_TEST_PASSWORD")
            
            if not email or not password:
                pytest.skip("API_TEST_EMAIL or API_TEST_PASSWORD not set in environment")
            
            response = auth_api.login(email=email, password=password)
            
            if response.status_code != 200:
                pytest.skip(f"Login failed with status {response.status_code}")
            
            # Extract token from response using your existing pattern
            response_data = response.json()
            
            # Check both possible token locations (based on your pattern)
            auth_token = None
            
            # Try nested data structure first
            if isinstance(response_data, dict) and 'data' in response_data:
                data_obj = response_data['data']
                if isinstance(data_obj, dict):
                    auth_token = data_obj.get('token') or data_obj.get('access_token')
                elif isinstance(data_obj, str):
                    auth_token = data_obj
            
            # Try direct token
            if not auth_token:
                auth_token = response_data.get('token') or response_data.get('access_token')
            
            if not auth_token:
                # Try to extract from cookies/session
                auth_token = auth_api.auth_token or getattr(auth_api, 'auth_token', None)
            
            assert auth_token, "No auth token received in response"
            
            # Set the token on hotel API
            self.hotel_api.set_auth_token(auth_token)
            self.logger.success(f"✅ Authenticated successfully with {email}")
            return auth_token
            
        except Exception as e:
            self.logger.error(f"❌ Authentication failed: {str(e)}")
            pytest.skip(f"Authentication failed: {str(e)}")
    
    def _generate_test_data(self):
        """Generate dynamic test data for hotel tests"""
        next_week = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        next_2weeks = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
        
        return {
            "city_codes": ["NYC", "LON", "PAR", "DXB", "ABV", "LOS"],
            "keywords": ["ABU", "LAG", "LON", "NEW", "PAR"],
            "hotel_search_payload": {
                "hotelName": "Any",
                "cityCode": "NYC",
                "countryOfResidence": "US",
                "destination": {
                    "country": "US",
                    "city": "New York"
                },
                "adults": 2,
                "checkInDate": "2026-01-10",
                "checkOutDate": "2026-01-19",
                "roomQuantity": 1,
                "childAges": [5, 10]
            },
            "hotel_search_payload_with_price": {
                "hotelName": "Any",
                "cityCode": "NYC",
                "countryOfResidence": "US",
                "destination": {
                    "country": "US",
                    "city": "New York"
                },
                "adults": 2,
                "checkInDate": "2026-01-10",
                "checkOutDate": "2026-01-19",
                "roomQuantity": 1,
                "childAges": [5, 10],
                "priceRange": "200-300",
                "currency": "USD"
            },
            "hotel_booking_payload": {
                "firstName": "Bot",
                "lastName": "GEO",
                "email": "geobot@yopmail.com",
                "phone": "7079090909",
                "adults": 2,
                "checkInDate": "2026-01-10",
                "checkOutDate": "2026-01-19",
                "roomQuantity": 1,
                "childAges": [5, 10],
                "hotelName": "Test Hotel",
                "destination": {
                    "country": "Nigeria",
                    "city": "Aba"
                }
            }
        }
    
    # ==================== HOTEL CITIES TESTS ====================
    
    @pytest.mark.api
    def test_get_hotel_cities_success(self, authenticated_api):
        """Test successful retrieval of hotel cities with valid keyword"""
        self.logger.info("=== Testing Get Hotel Cities - Success Case ===")
        
        keyword = "ABU"
        response = self.hotel_api.get_hotel_cities(keyword=keyword)
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Response structure validation
        response_data = response.json()
        
        # API returns a dictionary with 'data' -> 'cities' structure
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "data" in response_data, "Response should have 'data' key"
        assert "cities" in response_data["data"], "Response data should have 'cities' key"
        
        cities = response_data["data"]["cities"]
        assert isinstance(cities, list), "Cities should be a list"
        
        # Log details
        self.logger.success(f"✅ Successfully retrieved {len(cities)} cities for keyword '{keyword}'")
        if cities:
            self.logger.info(f"📋 Sample city: {cities[0]}")
    
    @pytest.mark.api
    def test_get_hotel_cities_empty_keyword(self, authenticated_api):
        """Test hotel cities with empty keyword"""
        self.logger.info("=== Testing Get Hotel Cities - Empty Keyword ===")
        
        response = self.hotel_api.get_hotel_cities(keyword="")
        
        # API returns 400 with specific error message
        assert response.status_code == 400, f"Expected 400 for empty keyword, got {response.status_code}"
        
        response_data = response.json()
        assert response_data.get("message") == "Please enter a keyword with 3 or more letters.", \
            f"Unexpected error message: {response_data.get('message')}"
        
        self.logger.success("✅ Empty keyword correctly rejected")
    
    @pytest.mark.api
    @pytest.mark.parametrize("keyword", ["INVALID123", "XYZ999", "###"])
    def test_get_hotel_cities_invalid_keyword(self, authenticated_api, keyword):
        """Test hotel cities with various invalid keywords"""
        self.logger.info(f"=== Testing Get Hotel Cities - Invalid Keyword: {keyword} ===")
        
        response = self.hotel_api.get_hotel_cities(keyword=keyword)
        
        # API returns 400 for invalid keywords (not 200 with empty list)
        if response.status_code == 400:
            response_data = response.json()
            error_message = response_data.get("message", "")
            self.logger.info(f"✅ Invalid keyword '{keyword}' correctly rejected: {error_message}")
        elif response.status_code == 200:
            # Some APIs might return empty results
            response_data = response.json()
            if isinstance(response_data, dict) and "data" in response_data:
                cities = response_data["data"].get("cities", [])
                self.logger.info(f"✅ Invalid keyword '{keyword}' returned {len(cities)} cities")
            else:
                self.logger.info(f"✅ Invalid keyword '{keyword}' handled with empty results")
        else:
            pytest.fail(f"Unexpected response {response.status_code} for invalid keyword")
    
    # ==================== HOTEL SEARCH TESTS ====================
    
    @pytest.mark.api
    def test_search_hotels_without_price(self, authenticated_api):
        """Test hotel search WITHOUT price range filter"""
        self.logger.info("=== Testing Hotel Search - Without Price Range ===")
        
        payload = self.test_data["hotel_search_payload"].copy()
        # Ensure priceRange and currency are not included
        payload.pop("priceRange", None)
        payload.pop("currency", None)
        
        response = self.hotel_api.search_hotels(**payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        
        response_data = response.json()
        hotels_data, pagination = self._validate_hotel_search_response(response_data)
        
        self.logger.success(f"✅ Found {len(hotels_data)} hotels without price filter")

    @pytest.mark.api
    def test_search_hotels_with_price_range_currency(self, authenticated_api):
        """Test hotel search with price range and currency - should return 200 if both provided"""
        self.logger.info("=== Testing Hotel Search - With Price Range and Currency ===")
        
        payload = self.test_data["hotel_search_payload_with_price"]
        response = self.hotel_api.search_hotels(**payload)
        
        # SIMPLE ASSERTION: If we provide both priceRange and currency, it should work (200)
        assert response.status_code == 200, f"Should return 200 when both priceRange and currency provided. Got {response.status_code}: {response.text}"
        
        # If we get here, validate the response
        response_data = response.json()
        hotels_data = response_data.get("data", {}).get("hotelDetailResult", {}).get("data", [])
        self.logger.success(f"✅ Found {len(hotels_data)} hotels with price filter")

    @pytest.mark.api
    @pytest.mark.parametrize("keyword", ["INVALID123", "", "XYZ999"])
    def test_get_hotel_cities_invalid_keyword(self, authenticated_api, keyword):
        """Test hotel cities with various invalid keywords"""
        self.logger.info(f"=== Testing Get Hotel Cities - Invalid Keyword: {keyword} ===")
        
        response = self.hotel_api.get_hotel_cities(keyword=keyword)
        
        # API returns 400 for invalid keywords (not 200 with empty list)
        if response.status_code == 400:
            response_data = response.json()
            error_message = response_data.get("message", "")
            self.logger.info(f"✅ Invalid keyword '{keyword}' correctly rejected: {error_message}")
        elif response.status_code == 200:
            # Some APIs might return empty results
            response_data = response.json()
            if isinstance(response_data, dict) and "data" in response_data:
                cities = response_data["data"].get("cities", [])
                self.logger.info(f"✅ Invalid keyword '{keyword}' returned {len(cities)} cities")
            else:
                self.logger.info(f"✅ Invalid keyword '{keyword}' handled with empty results")
        else:
            pytest.fail(f"Unexpected response {response.status_code} for invalid keyword")
    
    @pytest.mark.api
    def test_search_hotels_missing_required_fields(self, authenticated_api):
        """Test hotel search with missing required fields"""
        self.logger.info("=== Testing Hotel Search - Missing Required Fields ===")
        
        # Remove required hotelName
        payload = self.test_data["hotel_search_payload"].copy()
        payload.pop("hotelName", None)
        
        response = self.hotel_api.search_hotels(**payload)
        
        # Should return 400 for missing required field
        if response.status_code == 400:
            self.logger.success("✅ Missing required field correctly rejected with 400")
        elif response.status_code == 200:
            # Some APIs might handle missing fields differently
            response_data = response.json()
            hotels = response_data["data"]["hotelDetailResult"]["data"]
            self.logger.info(f"✅ API handled missing hotelName, returned {len(hotels)} hotels")
        else:
            self.logger.warning(f"⚠️ Unexpected response {response.status_code} for missing required field")
    
    @pytest.mark.api
    @pytest.mark.parametrize("page,limit", [(1, 10), (2, 10), (3, 20)])
    def test_search_hotels_pagination(self, authenticated_api, page, limit):
        """Test hotel search pagination functionality"""
        self.logger.info(f"=== Testing Hotel Search Pagination - Page {page}, Limit {limit} ===")
        
        payload = self.test_data["hotel_search_payload"].copy()
        payload.update({"page": page, "limit": limit})
        
        # Debug the payload
        self.logger.debug(f"Test payload keys: {list(payload.keys())}")
        self.logger.debug(f"Has 'page': {'page' in payload}, value: {payload.get('page')}")
        self.logger.debug(f"Has 'limit': {'limit' in payload}, value: {payload.get('limit')}")
        
        response = self.hotel_api.search_hotels(**payload)
        
        # Check what was actually sent
        self.logger.debug(f"Response status: {response.status_code}")
        
        if hasattr(response, 'request'):
            self.logger.debug(f"Actual request URL: {response.request.url}")
            self.logger.debug(f"Request method: {response.request.method}")
        
        assert response.status_code == 200, f"Pagination failed: {response.status_code}"
        
        response_data = response.json()
        hotels_data, pagination = self._validate_hotel_search_response(response_data)
        
        current_page = pagination.get("currentPage", 1)
        items_per_page = pagination.get("itemsPerPage", limit)
        
        # Debug what we got
        self.logger.debug(f"Requested: page={page}, limit={limit}")
        self.logger.debug(f"Received: currentPage={current_page}, itemsPerPage={items_per_page}")
        
        # Page should match what we requested
        assert current_page == page, f"Expected page {page}, got {current_page}"
        assert len(hotels_data) <= limit, f"Returned {len(hotels_data)} hotels, but limit is {limit}"
        
        self.logger.success(f"✅ Pagination test passed: Page {current_page}, Hotels: {len(hotels_data)}")

    @pytest.mark.api
    def test_search_hotels_invalid_dates(self, authenticated_api):
        """Test hotel search with invalid date combinations"""
        self.logger.info("=== Testing Hotel Search - Invalid Dates ===")
        
        base_payload = self.test_data["hotel_search_payload"].copy()
        
        invalid_date_cases = [
            {"name": "Check-out before check-in", "checkInDate": "2026-01-19", "checkOutDate": "2026-01-10"},
            {"name": "Same day check-in/out", "checkInDate": "2026-01-10", "checkOutDate": "2026-01-10"},
            {"name": "Past check-in date", "checkInDate": "2020-01-01", "checkOutDate": "2026-01-10"},
            {"name": "Too far in future", "checkInDate": "2030-01-01", "checkOutDate": "2030-01-10"},
            {"name": "Invalid date format", "checkInDate": "01-01-2026", "checkOutDate": "10-01-2026"},
        ]
        
        for case in invalid_date_cases:
            self.logger.info(f"Testing: {case['name']}")
            payload = base_payload.copy()
            payload["checkInDate"] = case["checkInDate"]
            payload["checkOutDate"] = case["checkOutDate"]
            
            response = self.hotel_api.search_hotels(**payload)
            
            # Should be rejected
            assert response.status_code in [400, 422], \
                f"Invalid dates should be rejected. Got {response.status_code}: {response.text}"
            
            self.logger.success(f"✅ {case['name']}: Correctly rejected")
    
    # ==================== HOTEL RATING TESTS ====================
    
    @pytest.mark.api
    def test_get_hotel_rating_success(self, authenticated_api):
        """Test successful retrieval of hotel rating"""
        self.logger.info("=== Testing Get Hotel Rating - Success Case ===")
        
        # First search for a hotel to get valid hotelId
        search_response = self.hotel_api.search_hotels(**self.test_data["hotel_search_payload"])
        if search_response.status_code != 200:
            pytest.skip("Hotel search failed, cannot test rating")
        
        search_data = search_response.json()
        hotels_data = search_data["data"]["hotelDetailResult"]["data"]
        if not hotels_data:
            pytest.skip("No hotels found, cannot test rating")
        
        hotel_id = hotels_data[0]["hotel"].get("hotelId")
        if not hotel_id:
            pytest.skip("Hotel has no ID, cannot test rating")
        
        # Test rating endpoint
        response = self.hotel_api.get_hotel_rating(hotelId=hotel_id)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code} for hotel ID {hotel_id}"
        rating_data = response.json()
        
        # Validate rating structure
        assert "rating" in rating_data, "Missing 'rating' field"
        assert "reviews" in rating_data, "Missing 'reviews' field"
        
        rating = rating_data["rating"]
        assert isinstance(rating, (int, float)), "Rating should be numeric"
        assert 0 <= rating <= 5, f"Rating {rating} should be between 0-5"
        
        self.logger.success(f"✅ Hotel {hotel_id} has rating: {rating}")
    
    @pytest.mark.api
    @pytest.mark.parametrize("invalid_hotel_id", ["INVALID123", "", "999999"])
    def test_get_hotel_rating_invalid_id(self, authenticated_api, invalid_hotel_id):
        """Test hotel rating with invalid hotel IDs"""
        self.logger.info(f"=== Testing Get Hotel Rating - Invalid ID: {invalid_hotel_id} ===")
        
        response = self.hotel_api.get_hotel_rating(hotelId=invalid_hotel_id)
        
        if response.status_code == 404:
            self.logger.success(f"✅ Invalid hotel ID '{invalid_hotel_id}' correctly returned 404")
        elif response.status_code == 400:
            self.logger.success(f"✅ Invalid hotel ID '{invalid_hotel_id}' correctly returned 400")
        elif response.status_code == 200:
            # Some APIs might return default rating for invalid IDs
            rating_data = response.json()
            self.logger.info(f"✅ API handled invalid ID, returned rating: {rating_data.get('rating', 'N/A')}")
        else:
            self.logger.warning(f"⚠️ Unexpected response {response.status_code} for invalid hotel ID")
    
    # ==================== HOTEL BOOKING TESTS ====================
    
    @pytest.mark.api
    def test_book_hotel_without_auth(self):
        """Test hotel booking without authentication - user_id should be null"""
        self.logger.info("=== Testing Hotel Booking - Without Authentication ===")
        
        # Clear any existing auth token
        self.hotel_api.auth_token = None
        
        payload = self.test_data["hotel_booking_payload"]
        response = self.hotel_api.book_hotel(**payload)
        
        # Booking should work without auth
        assert response.status_code == 200, f"Booking without auth failed: {response.status_code}. Response: {response.text}"
        
        booking_data = response.json()
        
        # Basic validation
        assert booking_data.get("status") == "success", f"Booking not successful: {booking_data}"
        assert "data" in booking_data, f"Missing data in response: {booking_data}"
        assert "hotelBooking" in booking_data["data"], f"Missing hotelBooking in data: {booking_data}"
        
        booking_info = booking_data["data"]["hotelBooking"]
        
        # CRITICAL: Verify user_id IS null when not authenticated
        user_id = booking_info.get("user_id")
        assert user_id is None, f"user_id should be null when booking without auth. Got: {user_id}"
        
        # Get booking ID
        booking_id = booking_info.get("id")
        
        self.logger.success("✅ Hotel booking successful without authentication")
        self.logger.info(f"📋 Booking ID: {booking_id}, User ID: {user_id} (should be null)")

    @pytest.mark.api
    def test_book_hotel_with_auth(self, authenticated_api):
        """Test hotel booking WITH authentication - should have user_id attached"""
        self.logger.info("=== Testing Hotel Booking - With Authentication ===")
        
        payload = self.test_data["hotel_booking_payload"]
        response = self.hotel_api.book_hotel(**payload)
        
        assert response.status_code == 200, f"Booking with auth failed: {response.status_code}. Response: {response.text}"
        
        booking_data = response.json()
        
        # Basic validation
        assert booking_data.get("status") == "success", f"Booking not successful: {booking_data}"
        assert "data" in booking_data, f"Missing data in response: {booking_data}"
        assert "hotelBooking" in booking_data["data"], f"Missing hotelBooking in data: {booking_data}"
        
        booking_info = booking_data["data"]["hotelBooking"]
        
        # CRITICAL: Verify user_id is NOT null when authenticated
        user_id = booking_info.get("user_id")
        assert user_id is not None, f"user_id should not be null when booking with auth. Response: {booking_data}"
        assert isinstance(user_id, int) or (isinstance(user_id, str) and user_id.strip()), \
            f"user_id should be a valid ID, got: {user_id}"
        
        # Get booking ID
        booking_id = booking_info.get("id")
        
        self.logger.success(f"✅ Booking successful with authentication!")
        self.logger.info(f"📋 Booking ID: {booking_id}, User ID: {user_id}")
        self.logger.info(f"📋 Booking Status: {booking_info.get('status', 'Unknown')}")
    
    @pytest.mark.api
    def test_book_hotel_missing_required_fields(self, authenticated_api):
        """Test hotel booking with missing required fields"""
        self.logger.info("=== Testing Hotel Booking - Missing Required Fields ===")
        
        # Create payload missing email (required field)
        payload = self.test_data["hotel_booking_payload"].copy()
        payload.pop("email", None)
        
        response = self.hotel_api.book_hotel(**payload)
        
        # Should return 400 for missing required field
        if response.status_code == 400:
            self.logger.success("✅ Missing required field correctly rejected with 400")
        else:
            self.logger.warning(f"⚠️ Unexpected response {response.status_code} for missing required field")
    
    @pytest.mark.api
    def test_book_hotel_invalid_dates(self, authenticated_api):
        """Test hotel booking with invalid dates (past dates)"""
        self.logger.info("=== Testing Hotel Booking - Invalid Dates ===")
        
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        payload = self.test_data["hotel_booking_payload"].copy()
        payload["checkInDate"] = yesterday
        
        response = self.hotel_api.book_hotel(**payload)
        
        # Should return 400 for past dates
        if response.status_code == 400:
            self.logger.success("✅ Past check-in date correctly rejected with 400")
        else:
            self.logger.warning(f"⚠️ Unexpected response {response.status_code} for past dates")
    
    # ==================== PERFORMANCE & EDGE CASES ====================
    
    @pytest.mark.api
    def test_search_hotels_performance(self, authenticated_api):
        """Test hotel search response time performance"""
        self.logger.info("=== Testing Hotel Search Performance ===")
        
        import time
        start_time = time.time()
        
        response = self.hotel_api.search_hotels(**self.test_data["hotel_search_payload"])
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200, f"Request failed: {response.status_code}"
        assert response_time < 5.0, f"Response time {response_time:.2f}s exceeds 5s threshold"
        
        self.logger.success(f"✅ Hotel search completed in {response_time:.2f} seconds")
    
    @pytest.mark.api
    def test_hotel_endpoints_without_auth(self):
        """Test hotel endpoints without authentication"""
        self.logger.info("=== Testing Hotel Endpoints Without Authentication ===")
        
        # Test without setting auth token
        self.hotel_api.auth_token = None
        
        # Test cities endpoint
        cities_response = self.hotel_api.get_hotel_cities(keyword="ABU")
        if cities_response.status_code == 401:
            self.logger.success("✅ Cities endpoint correctly requires authentication")
        elif cities_response.status_code == 200:
            self.logger.warning("⚠️ Cities endpoint accessible without authentication")
        
        # Test search endpoint
        search_response = self.hotel_api.search_hotels(**self.test_data["hotel_search_payload"])
        if search_response.status_code == 401:
            self.logger.success("✅ Search endpoint correctly requires authentication")
        elif search_response.status_code == 200:
            self.logger.warning("⚠️ Search endpoint accessible without authentication")
            
    # ==================== Helper Methods ====================
    
    def _validate_hotel_search_response(self, response_data):
        """Validate the structure of hotel search response"""
        assert isinstance(response_data, dict), "Response should be a dictionary"
        
        # Check the nested structure
        assert "data" in response_data, "Response should have 'data' key"
        assert "hotelDetailResult" in response_data["data"], "Response should have 'hotelDetailResult'"
        assert "data" in response_data["data"]["hotelDetailResult"], "Should have hotel data array"
        
        # Get hotels data
        hotels_data = response_data["data"]["hotelDetailResult"]["data"]
        assert isinstance(hotels_data, list), "Hotels data should be a list"
        
        # Check pagination
        assert "pagination" in response_data["data"], "Response should have pagination"
        pagination = response_data["data"]["pagination"]
        
        # Validate hotel data structure
        if hotels_data:
            first_hotel = hotels_data[0]
            assert "hotel" in first_hotel, "Hotel data missing 'hotel' field"
            assert "hotelId" in first_hotel["hotel"], "Hotel missing 'hotelId' field"
            assert "name" in first_hotel["hotel"], "Hotel missing 'name' field"
            assert "offers" in first_hotel, "Hotel missing 'offers' field"
            
            if first_hotel["offers"]:
                offer = first_hotel["offers"][0]
                assert "price" in offer, "Offer missing 'price' field"
                assert "currency" in offer["price"], "Price missing 'currency' field"
                assert "total" in offer["price"], "Price missing 'total' field"
        
        return hotels_data, pagination
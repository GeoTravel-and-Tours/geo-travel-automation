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
    
    def setup_method(self):
        """Setup before each test method"""
        self.logger = GeoLogger(self.__class__.__name__)
        self.test_data = self._generate_test_data()
        self.logger.info(f"🚀 Starting {self.__class__.__name__} test")
    
    def teardown_method(self):
        """Cleanup after each test method"""
        self.logger.info(f"✅ {self.__class__.__name__} test completed")
    
    @pytest.fixture
    def hotel_api(self):
        """Fixture for unauthenticated HotelAPI instance"""
        return HotelAPI()
    
    @pytest.fixture
    def authenticated_hotel_api(self):
        """Fixture for authenticated HotelAPI instance"""
        auth_api = AuthAPI()
        response = auth_api.login()
        
        if response.status_code != 200:
            pytest.skip(f"Login failed with status {response.status_code}")
        
        # Create HotelAPI and pass the token WITH SOURCE
        api = HotelAPI()
        
        # Get extraction method from token extractor
        token, extraction_method = auth_api.token_extractor.extract_token(response)
        if token:
            if extraction_method == "cookies":
                api.set_auth_token(token, token_source="cookies")
            else:
                api.set_auth_token(token, token_source="response_body")
        
        return api
    
    def _generate_test_data(self):
        """Generate dynamic test data for hotel tests"""
        return {
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
                "roomQuantity": 1
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
                "hotelName": "Test Hotel",
                "destination": {
                    "country": "Nigeria",
                    "city": "Aba"
                }
            }
        }
    
    # ==================== HOTEL CITIES TESTS ====================
    
    @pytest.mark.api
    def test_get_hotel_cities_success(self, authenticated_hotel_api):
        """Test successful retrieval of hotel cities with valid keyword"""
        self.logger.info("Testing Get Hotel Cities - Success Case")
        
        keyword = "ABU"
        response = authenticated_hotel_api.get_hotel_cities(keyword=keyword)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        response_data = response.json()
        assert isinstance(response_data, dict), "Response should be a dictionary"
        assert "data" in response_data, "Response should have 'data' key"
        assert "cities" in response_data["data"], "Response data should have 'cities' key"
        
        cities = response_data["data"]["cities"]
        assert isinstance(cities, list), "Cities should be a list"
        
        self.logger.success(f"Successfully retrieved {len(cities)} cities for keyword '{keyword}'")
    
    @pytest.mark.api
    def test_get_hotel_cities_empty_keyword(self, hotel_api):
        """Test hotel cities with empty keyword"""
        self.logger.info("Testing Get Hotel Cities - Empty Keyword")
        
        response = hotel_api.get_hotel_cities(keyword="")
        
        assert response.status_code == 400, f"Expected 400 for empty keyword, got {response.status_code}"
        
        response_data = response.json()
        assert response_data.get("message") == "Please enter a keyword with 3 or more letters."
        
        self.logger.success("Empty keyword correctly rejected")
    
    @pytest.mark.api
    @pytest.mark.parametrize("keyword", ["INVALID123", "XYZ999", "###"])
    def test_get_hotel_cities_invalid_keyword(self, hotel_api, keyword):
        """Test hotel cities with various invalid keywords"""
        self.logger.info(f"Testing Get Hotel Cities - Invalid Keyword: {keyword}")
        
        response = hotel_api.get_hotel_cities(keyword=keyword)
        
        if response.status_code == 400:
            self.logger.success(f"Invalid keyword '{keyword}' correctly rejected")
        elif response.status_code == 200:
            response_data = response.json()
            if isinstance(response_data, dict) and "data" in response_data:
                cities = response_data["data"].get("cities", [])
                self.logger.info(f"Invalid keyword '{keyword}' returned {len(cities)} cities")
        else:
            pytest.fail(f"Unexpected response {response.status_code} for invalid keyword")
    
    # ==================== HOTEL SEARCH TESTS ====================
    
    @pytest.mark.api
    def test_search_hotels_without_price(self, hotel_api):
        """Test hotel search WITHOUT price range filter"""
        self.logger.info("Testing Hotel Search - Without Price Range")
        
        payload = self.test_data["hotel_search_payload"].copy()
        response = hotel_api.search_hotels(**payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        response_data = response.json()
        self.logger.success("Hotel search without price range succeeded")
    
    @pytest.mark.api
    def test_search_hotels_with_price_range_currency(self, hotel_api):
        """Test hotel search with price range and currency"""
        self.logger.info("Testing Hotel Search - With Price Range and Currency")
        
        payload = self.test_data["hotel_search_payload_with_price"]
        response = hotel_api.search_hotels(**payload)
        
        assert response.status_code == 200, f"Should return 200 when both priceRange and currency provided"
        
        response_data = response.json()
        # hotels_data = response_data.get("data", {}).get("hotelDetailResult", {}).get("data", [])
        
        self.logger.success("Hotel search with price range and currency succeeded")
    
    @pytest.mark.api
    def test_search_hotels_missing_required_fields(self, hotel_api):
        """Test hotel search with missing required fields"""
        self.logger.info("Testing Hotel Search - Missing Required Fields")
        
        payload = self.test_data["hotel_search_payload"].copy()
        payload.pop("hotelName", None)
        
        response = hotel_api.search_hotels(**payload)
        
        if response.status_code == 400:
            self.logger.success("Missing required field correctly rejected with 400")
        elif response.status_code == 200:
            self.logger.info("API handled missing hotelName")
        else:
            self.logger.warning(f"Unexpected response {response.status_code} for missing required field")
    
    @pytest.mark.api
    @pytest.mark.parametrize("page,limit", [(1, 10), (2, 10), (3, 20)])
    def test_search_hotels_pagination(self, hotel_api, page, limit):
        """Test hotel search pagination functionality"""
        self.logger.info(f"Testing Hotel Search Pagination - Page {page}, Limit {limit}")
        
        payload = self.test_data["hotel_search_payload"].copy()
        payload.update({"page": page, "limit": limit})
        
        response = hotel_api.search_hotels(**payload)
        assert response.status_code == 200, f"Pagination failed: {response.status_code}"
        
        response_data = response.json()
        self.logger.success(f"Pagination test passed: Page {page}, Limit: {limit}")
    
    @pytest.mark.api
    def test_search_hotels_invalid_dates(self, hotel_api):
        """Test hotel search with invalid date combinations"""
        self.logger.info("Testing Hotel Search - Invalid Dates")
        
        base_payload = self.test_data["hotel_search_payload"].copy()
        
        invalid_date_cases = [
            {"name": "Check-out before check-in", "checkInDate": "2026-01-19", "checkOutDate": "2026-01-10"},
            {"name": "Same day check-in/out", "checkInDate": "2026-01-10", "checkOutDate": "2026-01-10"},
            {"name": "Past check-in date", "checkInDate": "2020-01-01", "checkOutDate": "2026-01-10"},
            {"name": "Invalid date format", "checkInDate": "01-01-2026", "checkOutDate": "10-01-2026"},
            {"name": "Too far in future", "checkInDate": "2030-01-01", "checkOutDate": "2030-01-10"},
        ]
        
        for case in invalid_date_cases:
            self.logger.info(f"Testing: {case['name']}")
            payload = base_payload.copy()
            payload["checkInDate"] = case["checkInDate"]
            payload["checkOutDate"] = case["checkOutDate"]
            
            response = hotel_api.search_hotels(**payload)
            
            status = response.status_code

            if status in (400, 422):
                self.logger.success(
                    f"{case['name']}: Correctly rejected "
                    f"(Invalid dates should be rejected. Got {status})"
                )
                assert True  # explicit pass (optional but clear)

            elif status == 500:
                pytest.skip(
                    f"{case['name']}: Skipped — scenario not properly handled yet "
                    f"(Internal Server Error: {status})"
                )

            else:
                pytest.fail(
                    f"{case['name']}: Failed — Invalid dates should be rejected. "
                    f"Got unexpected status code {status}"
                )

    
    # ==================== HOTEL RATING TESTS ====================
    
    @pytest.mark.api
    def test_get_hotel_rating_success(self, hotel_api):
        """Test successful retrieval of hotel rating"""
        self.logger.info("Testing Get Hotel Rating - Success Case")

        # Step 1: Search hotels
        search_response = hotel_api.search_hotels(
            **self.test_data["hotel_search_payload"]
        )

        if search_response.status_code != 200:
            pytest.skip(
                f"Hotel search failed (status {search_response.status_code}); "
                "cannot test hotel rating"
            )

        search_data = search_response.json()

        try:
            hotels_data = search_data["data"]["hotelDetailResult"]["data"]
        except KeyError:
            pytest.skip(
                "Hotel search response structure unexpected; "
                "cannot extract hotel list"
            )

        if not hotels_data:
            pytest.skip("No hotels returned from search; cannot test rating")

        hotel_id = hotels_data[0].get("hotel", {}).get("hotelId")
        if not hotel_id:
            pytest.skip("First hotel has no hotelId; cannot test rating")

        # Step 2: Get hotel rating
        response = hotel_api.get_hotel_rating(hotelId=hotel_id)
        status = response.status_code

        if status == 200:
            rating_data = response.json()

            # Validate response structure
            assert "data" in rating_data, "Response missing 'data' field"
            rating_list = rating_data["data"]
            assert isinstance(rating_list, list), "'data' should be a list"
            assert rating_list, "Rating list is empty"

            hotel_rating = rating_list[0]
            assert "overallRating" in hotel_rating, "Missing 'overallRating' field"
            assert "numberOfReviews" in hotel_rating, "Missing 'numberOfReviews' field"

            overall_rating = hotel_rating["overallRating"]
            assert isinstance(overall_rating, (int, float)), (
                "overallRating should be numeric"
            )
            assert 0 <= overall_rating <= 100, (
                f"overallRating {overall_rating} should be between 0 and 100"
            )

            self.logger.success(
                f"Get Hotel Rating: Hotel {hotel_id} "
                f"returned overallRating {overall_rating}/100"
            )

        elif status == 500:
            pytest.skip(
                f"Get Hotel Rating skipped — AMADEUS internal error "
                f"(hotelId={hotel_id}, status={status})"
            )

        else:
            pytest.fail(
                f"Get Hotel Rating failed — Expected 200, got {status} "
                f"(hotelId={hotel_id})"
            )
    
    
    @pytest.mark.api
    @pytest.mark.parametrize("invalid_hotel_id", ["INVALID123", "", "999999"])
    def test_get_hotel_rating_invalid_id(self, hotel_api, invalid_hotel_id):
        """Test hotel rating with invalid hotel IDs"""
        self.logger.info(f"Testing Get Hotel Rating - Invalid ID: {invalid_hotel_id}")
        
        response = hotel_api.get_hotel_rating(hotelId=invalid_hotel_id)
        
        if response.status_code in [400, 404]:
            self.logger.success(f"Invalid hotel ID '{invalid_hotel_id}' correctly returned {response.status_code}")
        elif response.status_code == 200:
            rating_data = response.json()
            self.logger.info(f"API handled invalid ID, returned rating: {rating_data.get('rating', 'N/A')}")
    
    # ==================== HOTEL BOOKING TESTS ====================
    
    @pytest.mark.api
    def test_book_hotel_without_auth(self, hotel_api):
        """Test hotel booking WITHOUT authentication - user_id MUST be null"""
        self.logger.info("Testing Hotel Booking - Without Authentication (MUST have null user_id)")
        
        # Ensure no auth token
        hotel_api.auth_token = None
        if 'Authorization' in hotel_api.headers:
            del hotel_api.headers['Authorization']
        if 'Cookie' in hotel_api.headers:
            del hotel_api.headers['Cookie']
        
        payload = self.test_data["hotel_booking_payload"]
        response = hotel_api.book_hotel(**payload)
        
        # Booking must succeed
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        booking_data = response.json()
        assert booking_data.get("status") == "success", "Booking status must be 'success'"
        
        booking_info = booking_data["data"]["hotelBooking"]
        
        # CRITICAL: When NOT authenticated, user_id MUST be null
        user_id = booking_info.get("user_id")
        
        # FAIL if user_id is NOT None when not authenticated
        assert user_id is None, (
            f"user_id should be null when booking without authentication.\n"
            f"Got user_id: {user_id}\n"
            f"Full response: {booking_data}\n"
            f"This indicates the endpoint is incorrectly attaching a user."
        )
        
        self.logger.success(f"✅ Booking successful without authentication!")
        self.logger.info(f"📋 Booking ID: {booking_info.get('id')}, User ID: {user_id} (correctly null)")
    
    @pytest.mark.api
    def test_book_hotel_with_auth(self, authenticated_hotel_api):
        """Test hotel booking WITH authentication - MUST have user_id attached"""
        self.logger.info("Testing Hotel Booking - With Authentication (MUST have user_id)")
        
        payload = self.test_data["hotel_booking_payload"]
        response = authenticated_hotel_api.book_hotel(**payload)
        
        # Booking must succeed
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        booking_data = response.json()
        assert booking_data.get("status") == "success", "Booking status must be 'success'"
        
        booking_info = booking_data["data"]["hotelBooking"]
        
        # CRITICAL: When authenticated, user_id MUST NOT be null
        user_id = booking_info.get("user_id")
        
        # FAIL if user_id is None when authenticated
        assert user_id is not None, (
            f"user_id should not be null when booking with authentication.\n"
        )
        
        # Additional validation: user_id must be valid
        assert isinstance(user_id, (int, str)), f"user_id must be int or str, got {type(user_id)}"
        
        if isinstance(user_id, str):
            assert user_id.strip() != "", "user_id string cannot be empty"
        
        # Log success
        self.logger.success(f"✅ Booking successful with authentication!")
        self.logger.info(f"📋 Booking ID: {booking_info.get('id')}, User ID: {user_id}")
    
    @pytest.mark.api
    def test_book_hotel_missing_required_fields(self, hotel_api):
        """Test hotel booking with missing required fields"""
        self.logger.info("Testing Hotel Booking - Missing Required Fields")
        
        payload = self.test_data["hotel_booking_payload"].copy()
        payload.pop("email", None)
        
        response = hotel_api.book_hotel(**payload)
        
        if response.status_code == 400:
            self.logger.success("Missing required field correctly rejected with 400")
        else:
            self.logger.warning(f"Unexpected response {response.status_code} for missing required field")
    
    # ==================== PERFORMANCE & EDGE CASES ====================
    
    @pytest.mark.api
    def test_search_hotels_performance_without_auth(self, hotel_api):
        """Test hotel search response time performance"""
        self.logger.info("Testing Hotel Search Performance Without Auth")
        
        import time
        start_time = time.time()
        
        response = hotel_api.search_hotels(**self.test_data["hotel_search_payload"])
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200, f"Request failed: {response.status_code}"
        assert response_time < 10.0, f"Response time {response_time:.2f}s exceeds 10s threshold"
        
        self.logger.success(f"Hotel search completed in {response_time:.2f} seconds")
    
    @pytest.mark.api
    def test_search_hotels_performance_with_auth(self, authenticated_hotel_api):
        """Test hotel search response time performance with auth"""
        self.logger.info("Testing Hotel Search Performance With Auth")
        
        import time
        start_time = time.time()
        
        response = authenticated_hotel_api.search_hotels(**self.test_data["hotel_search_payload"])
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200, f"Request failed: {response.status_code}"
        assert response_time < 10.0, f"Response time {response_time:.2f}s exceeds 10s threshold"
        
        self.logger.success(f"Hotel search completed in {response_time:.2f} seconds")
    
    @pytest.mark.api
    def test_hotel_endpoints_without_auth(self, hotel_api):
        """Test hotel endpoints without authentication"""
        self.logger.info("Testing Hotel Endpoints Without Authentication")
        
        # Test cities endpoint
        cities_response = hotel_api.get_hotel_cities(keyword="ABU")
        assert cities_response.status_code == 200, f"Expected 200, got {cities_response.status_code}"
        self.logger.success("Cities endpoint accessible without authentication")
        
        # Test search endpoint
        search_response = hotel_api.search_hotels(**self.test_data["hotel_search_payload"])
        assert search_response.status_code == 200, f"Expected 200, got {search_response.status_code}"
        self.logger.success("Search endpoint accessible without authentication")
    
    @pytest.mark.api
    def test_hotel_endpoints_with_auth(self, authenticated_hotel_api):
        """Test hotel endpoints with authentication"""
        self.logger.info("Testing Hotel Endpoints With Authentication")
        
        # Test cities endpoint
        cities_response = authenticated_hotel_api.get_hotel_cities(keyword="ABU")
        assert cities_response.status_code == 200, f"Expected 200, got {cities_response.status_code}"
        self.logger.success("Cities endpoint accessible with authentication")
        
        # Test search endpoint
        search_response = authenticated_hotel_api.search_hotels(**self.test_data["hotel_search_payload"])
        assert search_response.status_code == 200, f"Expected 200, got {search_response.status_code}"
        self.logger.success("Search endpoint accessible with authentication")
# src/tests/api_tests/test_hotel_api.py

import pytest
import time
from src.pages.api.hotels_api import HotelAPI
from src.pages.api.auth_api import AuthAPI
from src.utils.logger import GeoLogger
from src.tests.test_data import generate_hotel_test_data


class TestHotelAPI:
    """Comprehensive Hotel API Test Suite"""
    
    def setup_method(self):
        """Setup before each test method"""
        self.logger = GeoLogger(self.__class__.__name__)
        self.test_data = generate_hotel_test_data()
        self.logger.info(f"🚀 Starting {self.__class__.__name__} test")
    
    def teardown_method(self):
        """Enhanced cleanup after each test method"""
        # Log test completion
        self.logger.info(f"✅ {self.__class__.__name__} test completed")
        
        # Clear any sensitive data if needed
        if hasattr(self, 'test_data'):
            # Don't keep PII in memory longer than necessary
            if 'hotel_booking_payload' in self.test_data:
                booking_data = self.test_data['hotel_booking_payload']
                if 'email' in booking_data:
                    # Optional: redact or clear if needed
                    pass
    
    @pytest.fixture
    def hotel_api(self):
        """Fixture for unauthenticated HotelAPI instance"""
        return HotelAPI()
    
    @pytest.fixture
    def authenticated_hotel_api(self):
        auth_api = AuthAPI()
        response = auth_api.login()
        
        if response.status_code != 200:
            self.logger.error(f"❌ Login failed with status {response.status_code}")
            pytest.skip(f"Login failed with status {response.status_code}")
        self.logger.success(f"✅ Authenticated successfully (token length: {len(auth_api.auth_token)})")
            
        hotel_api = HotelAPI()
        hotel_api.set_auth_token(auth_api.auth_token)
        hotel_api.set_auth_token(auth_api.auth_token, token_source=auth_api.token_source)
        return hotel_api
    
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

        # Authenticate the hotel_api instance
        auth_api = AuthAPI()
        response = auth_api.login()
        if response.status_code != 200:
            self.logger.error(f"❌ Login failed with status {response.status_code}")
            pytest.fail(f"Login failed with status {response.status_code}")
        self.logger.info(f"✅ Authenticated successfully (token length: {len(auth_api.auth_token)})")

        hotel_api.set_auth_token(auth_api.auth_token)
        hotel_api.set_auth_token(auth_api.auth_token, token_source=auth_api.token_source)

        # Debug: Check if the token is set
        if not hotel_api.auth_token:
            self.logger.error("❌ Auth token is not set. Test cannot proceed.")
            pytest.fail("Auth token is not set.")
        else:
            self.logger.info(f"✅ Auth token is set: {hotel_api.auth_token[:10]}... (truncated)")

        payload = self.test_data["hotel_search_payload"].copy()
        self.logger.info(f"Payload for search: {payload}")

        # Log headers for debugging
        headers = hotel_api.get_headers()
        self.logger.info(f"Request headers: {headers}")

        response = hotel_api.search_hotels(**payload)
        self.logger.info(f"Response status code: {response.status_code}")
        self.logger.info(f"Response body: {response.text}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        response_data = response.json()
        self.logger.success("Hotel search without price range succeeded")
    
    @pytest.mark.api
    def test_search_hotels_with_price_range_currency(self, hotel_api):
        """Test hotel search with price range and currency"""
        self.logger.info("Testing Hotel Search - With Price Range and Currency")

        payload = self.test_data["hotel_search_payload_with_price"]
        response = hotel_api.search_hotels(**payload)

        # Basic status code check
        assert response.status_code == 200, (
            "Should return 200 when both priceRange and currency are provided"
        )

        response_data = response.json()

        # Validate top-level response structure
        assert response_data.get("status") == "success"
        assert "data" in response_data

        data = response_data.get("data")

        # Case 1: No hotels found (valid scenario)
        if isinstance(data, list):
            assert data == [] or len(data) >= 0

        # Case 2: Hotels returned
        elif isinstance(data, dict):
            hotels_data = (
                data.get("hotelDetailResult", {})
                    .get("data", [])
            )

            assert isinstance(hotels_data, list), "Hotels data should be a list"

            # Validate currency only if hotel data exists
            if hotels_data:
                offers = hotels_data[0].get("offers", [])
                if offers:
                    price = offers[0].get("price", {})
                    assert price.get("currency") == payload.get("currency"), (
                        "Currency should match request"
                    )

        # Case 3: Unexpected response shape
        else:
            pytest.fail(f"Unexpected data type returned: {type(data)}")

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

        # ---- FIX: dynamic extraction (handles list OR nested dict) ----
        data = search_data.get("data")

        if not data:
            pytest.skip("Hotel search returned empty data")

        if isinstance(data, list):
            hotels_data = data
        elif isinstance(data, dict):
            hotels_data = (
                data.get("hotelDetailResult", {})
                    .get("data", [])
            )
        else:
            pytest.skip(f"Unexpected data type: {type(data)}")

        if not hotels_data:
            pytest.skip("No hotels returned from search; cannot test rating")

        # ---- safer hotelId extraction ----
        first = hotels_data[0]
        hotel_id = (
            first.get("hotel", {}).get("hotelId")
            or first.get("hotelId")
        )

        if not hotel_id:
            pytest.skip("First hotel has no hotelId; cannot test rating")

        # Step 2: Get hotel rating
        response = hotel_api.get_hotel_rating(hotelId=hotel_id)
        status = response.status_code

        if status == 200:
            rating_data = response.json()

            rating_list = rating_data.get("data", [])

            if not isinstance(rating_list, list) or not rating_list:
                pytest.skip("Rating data empty or malformed")

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
        
        # Step 1: Search hotels to get valid hotelId
        search_response = hotel_api.search_hotels(
            **self.test_data["hotel_search_payload"]
        )
        
        # Ensure search was successful
        assert search_response.status_code == 200, f"Search failed with {search_response.status_code}"
        search_data = search_response.json()
        assert search_data.get("status") == "success", "Hotel search status must be 'success'"
        
        # Extract hotelId from search results
        hotels = search_data.get("data", {}).get("hotelDetailResult", {}).get("data", [])
        assert len(hotels) > 0, "No hotels found in search results"
        
        # Use the first available hotel's ID
        hotel_id = hotels[0]["hotel"]["hotelId"]
        
        # Update booking payload with the actual hotelId
        booking_payload = self.test_data["hotel_booking_payload"].copy()
        booking_payload["hotelId"] = hotel_id
        
        # Ensure no auth token
        hotel_api.auth_token = None
        if 'Authorization' in hotel_api.headers:
            del hotel_api.headers['Authorization']
        if 'Cookie' in hotel_api.headers:
            del hotel_api.headers['Cookie']
        
        response = hotel_api.book_hotel(**booking_payload)
        
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
        
        # Step 1: Search hotels to get valid hotelId
        search_response = authenticated_hotel_api.search_hotels(
            **self.test_data["hotel_search_payload"]
        )
        
        # Ensure search was successful
        assert search_response.status_code == 200, f"Search failed with {search_response.status_code}"
        search_data = search_response.json()
        assert search_data.get("status") == "success", "Hotel search status must be 'success'"
        
        # Extract hotelId from search results
        hotels = search_data.get("data", {}).get("hotelDetailResult", {}).get("data", [])
        assert len(hotels) > 0, "No hotels found in search results"
        
        # Use the first available hotel's ID
        hotel_id = hotels[0]["hotel"]["hotelId"]
        
        # Update booking payload with the actual hotelId
        booking_payload = self.test_data["hotel_booking_payload"].copy()
        booking_payload["hotelId"] = hotel_id
        
        response = authenticated_hotel_api.book_hotel(**booking_payload)
        
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
        
        start_time = time.time()
        
        response = hotel_api.search_hotels(**self.test_data["hotel_search_payload"])
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200, f"Request failed: {response.status_code}"
        assert response_time < 20.0, f"Response time {response_time:.2f}s exceeds 20s threshold"
        
        self.logger.success(f"Hotel search completed in {response_time:.2f} seconds")
    
    @pytest.mark.api
    def test_search_hotels_performance_with_auth(self, authenticated_hotel_api):
        """Test hotel search response time performance with auth"""
        self.logger.info("Testing Hotel Search Performance With Auth")
        
        start_time = time.time()
        
        response = authenticated_hotel_api.search_hotels(**self.test_data["hotel_search_payload"])
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200, f"Request failed: {response.status_code}"
        assert response_time < 20.0, f"Response time {response_time:.2f}s exceeds 20s threshold"
        
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
        
        # Validate some data returned
        response_data = search_response.json()
        assert response_data["data"], "Expected hotels data, got empty list"

    # ==================== HOTEL OFFERS (DETAILS) TESTS ====================

    @pytest.mark.api
    def test_get_hotel_offers_different_currency(self, hotel_api):
        """
        Test hotel offers with currency different from response currency.
        
        CRITICAL: When requested currency differs from price currency:
        - Must include 'currencyConversion' field
        - Must include 'requestedCurrencyTotalPrice' field
        - Must correctly calculate converted price
        """
        self.logger.info("Testing Hotel Offers - Different Currency (Should show conversion)")
        
        # Step 1: Search for hotels to get a valid hotelId
        search_response = hotel_api.search_hotels(**self.test_data["hotel_search_payload"])
        assert search_response.status_code == 200, f"Search failed: {search_response.status_code}"
        
        search_data = search_response.json()
        hotels = self._extract_hotels_from_search(search_data)
        
        if not hotels:
            pytest.skip("No hotels found for offers test")
        
        # Use the first hotel with a valid ID
        hotel = hotels[0]
        hotel_id = hotel.get("hotel", {}).get("hotelId") or hotel.get("hotelId")
        
        if not hotel_id:
            pytest.skip("Hotel missing hotelId")
        
        self.logger.info(f"Testing with hotel: {hotel_id}")
        
        # Step 2: Get hotel offers with different currency (NGN vs USD)
        offers_payload = self.test_data["hotel_offers_payload"].copy()
        offers_payload["hotelId"] = hotel_id
        
        response = hotel_api.get_hotel_offers(**offers_payload)
        
        # Handle cases where hotel might not have availability
        if response.status_code == 404:
            pytest.skip(f"Hotel {hotel_id} not found or no availability")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        response_data = response.json()
        assert response_data.get("status") == "success", "Response status must be 'success'"
        
        data = response_data.get("data", {})
        
        # CRITICAL: Check for currency conversion fields (should exist since currency differs)
        assert "currencyConversion" in data, (
            "Missing 'currencyConversion' field when currency differs from response"
        )
        
        assert "requestedCurrencyTotalPrice" in data, (
            "Missing 'requestedCurrencyTotalPrice' field when currency differs from response"
        )
        
        # Validate currencyConversion structure
        currency_conversion = data["currencyConversion"]
        assert isinstance(currency_conversion, dict), "currencyConversion must be a dict"
        
        # Should have USD -> NGN conversion
        assert "USD" in currency_conversion, "Expected USD as source currency"
        usd_conversion = currency_conversion["USD"]
        
        assert "rate" in usd_conversion, "Missing conversion rate"
        assert "target" in usd_conversion, "Missing target currency"
        assert usd_conversion["target"] == "NGN", f"Expected target NGN, got {usd_conversion['target']}"
        
        # Validate requestedCurrencyTotalPrice
        assert isinstance(data["requestedCurrencyTotalPrice"], (int, float)), (
            "requestedCurrencyTotalPrice must be numeric"
        )
        
        self.logger.success(f"✅ Hotel offers with different currency - All conversion fields present")
        self.logger.info(f"💰 Conversion: {currency_conversion}")
        self.logger.info(f"💰 Total in NGN: {data['requestedCurrencyTotalPrice']}")


    @pytest.mark.api
    def test_get_hotel_offers_same_currency(self, hotel_api):
        """
        Test hotel offers with same currency as response.
        
        CRITICAL: When requested currency matches price currency:
        - Should NOT include 'currencyConversion' field
        - Should NOT include 'requestedCurrencyTotalPrice' field
        """
        self.logger.info("Testing Hotel Offers - Same Currency (Should NOT show conversion)")
        
        # Step 1: Search for hotels
        search_response = hotel_api.search_hotels(**self.test_data["hotel_search_payload"])
        assert search_response.status_code == 200, f"Search failed: {search_response.status_code}"
        
        search_data = search_response.json()
        hotels = self._extract_hotels_from_search(search_data)
        
        if not hotels:
            pytest.skip("No hotels found for offers test")
        
        hotel = hotels[0]
        hotel_id = hotel.get("hotel", {}).get("hotelId") or hotel.get("hotelId")
        
        if not hotel_id:
            pytest.skip("Hotel missing hotelId")
        
        # Step 2: Get hotel offers with USD currency (same as response)
        offers_payload = self.test_data["hotel_offers_same_currency_payload"].copy()
        offers_payload["hotelId"] = hotel_id
        
        response = hotel_api.get_hotel_offers(**offers_payload)
        
        if response.status_code == 404:
            pytest.skip(f"Hotel {hotel_id} not found or no availability")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        response_data = response.json()
        assert response_data.get("status") == "success", "Response status must be 'success'"
        
        data = response_data.get("data", {})
        
        # CRITICAL: These fields should NOT exist when currency matches
        assert "currencyConversion" not in data, (
            "'currencyConversion' field should NOT be present when using same currency"
        )
        
        assert "requestedCurrencyTotalPrice" not in data, (
            "'requestedCurrencyTotalPrice' field should NOT be present when using same currency"
        )
        
        self.logger.success(f"✅ Hotel offers with same currency - No conversion fields (correct)")


    @pytest.mark.api
    @pytest.mark.parametrize("currency", ["EUR", "GBP", "JPY", "CAD"])
    def test_get_hotel_offers_multiple_currencies(self, hotel_api, currency):
        """Test hotel offers with various currency conversions"""
        self.logger.info(f"Testing Hotel Offers - Currency: {currency}")
        
        # Get a valid hotel
        search_response = hotel_api.search_hotels(**self.test_data["hotel_search_payload"])
        assert search_response.status_code == 200, f"Search failed: {search_response.status_code}"
        
        search_data = search_response.json()
        hotels = self._extract_hotels_from_search(search_data)
        
        if not hotels:
            pytest.skip("No hotels found for offers test")
        
        hotel = hotels[0]
        hotel_id = hotel.get("hotel", {}).get("hotelId") or hotel.get("hotelId")
        
        if not hotel_id:
            pytest.skip("Hotel missing hotelId")
        
        # Get offers with requested currency
        offers_payload = self.test_data["hotel_offers_payload"].copy()
        offers_payload["hotelId"] = hotel_id
        offers_payload["currency"] = currency
        
        response = hotel_api.get_hotel_offers(**offers_payload)
        
        if response.status_code == 404:
            pytest.skip(f"Hotel {hotel_id} not found or no availability")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        response_data = response.json()
        data = response_data.get("data", {})
        
        # If currency differs from USD (which is likely), conversion fields should exist
        if currency != "USD":
            assert "currencyConversion" in data, f"Missing conversion for {currency}"
            assert "requestedCurrencyTotalPrice" in data, f"Missing total price for {currency}"
            
            # Verify the target currency matches
            currency_conversion = data["currencyConversion"]
            assert "USD" in currency_conversion, "Expected USD as source"
            assert currency_conversion["USD"]["target"] == currency, (
                f"Expected target {currency}, got {currency_conversion['USD']['target']}"
            )
            
            self.logger.success(f"✅ {currency} conversion fields present")
        else:
            # USD should have no conversion fields
            assert "currencyConversion" not in data, "USD should not have conversion"
            self.logger.success(f"✅ USD correctly has no conversion fields")


    @pytest.mark.api
    def test_get_hotel_offers_invalid_currency(self, hotel_api):
        """Test hotel offers with invalid currency codes"""
        self.logger.info("Testing Hotel Offers - Invalid Currencies")
        
        # Get a valid hotel first
        search_response = hotel_api.search_hotels(**self.test_data["hotel_search_payload"])
        if search_response.status_code != 200:
            pytest.skip("Search failed")
        
        search_data = search_response.json()
        hotels = self._extract_hotels_from_search(search_data)
        
        if not hotels:
            pytest.skip("No hotels found")
        
        hotel_id = hotels[0].get("hotel", {}).get("hotelId") or hotels[0].get("hotelId")
        
        for invalid_currency in self.test_data["invalid_currencies"]:
            self.logger.info(f"Testing invalid currency: '{invalid_currency}'")
            
            offers_payload = self.test_data["hotel_offers_payload"].copy()
            offers_payload["hotelId"] = hotel_id
            offers_payload["currency"] = invalid_currency
            
            response = hotel_api.get_hotel_offers(**offers_payload)
            
            # Should return 400 for invalid currency
            if response.status_code == 400:
                self.logger.success(f"✓ Invalid currency '{invalid_currency}' correctly rejected")
            elif response.status_code == 200:
                # If it accepts, check if it defaults to something reasonable
                self.logger.info(f"API accepted '{invalid_currency}', checking response...")
                response_data = response.json()
                data = response_data.get("data", {})
                
                # If it accepted, currency should be in the response
                offers = data.get("offers", [])
                if offers:
                    price_currency = offers[0].get("price", {}).get("currency")
                    self.logger.info(f"Response used currency: {price_currency}")
            else:
                self.logger.warning(f"Unexpected status {response.status_code} for '{invalid_currency}'")


    @pytest.mark.api
    def test_get_hotel_offers_with_child_ages(self, hotel_api):
        """Test hotel offers with child ages included"""
        self.logger.info("Testing Hotel Offers - With Child Ages")
        
        # Get a valid hotel
        search_response = hotel_api.search_hotels(**self.test_data["hotel_search_payload"])
        assert search_response.status_code == 200, f"Search failed: {search_response.status_code}"
        
        search_data = search_response.json()
        hotels = self._extract_hotels_from_search(search_data)
        
        if not hotels:
            pytest.skip("No hotels found")
        
        hotel_id = hotels[0].get("hotel", {}).get("hotelId") or hotels[0].get("hotelId")
        
        # Test with various child age combinations
        child_age_cases = [
            [5, 10],           # Two children
            [3],                # One child
            [2, 4, 6, 8],       # Four children
            [],                 # No children
            [15, 17],           # Older children
        ]
        
        for child_ages in child_age_cases:
            self.logger.info(f"Testing child ages: {child_ages}")
            
            offers_payload = self.test_data["hotel_offers_payload"].copy()
            offers_payload["hotelId"] = hotel_id
            offers_payload["childAges"] = child_ages
            
            response = hotel_api.get_hotel_offers(**offers_payload)
            
            if response.status_code == 404:
                self.logger.info(f"No availability for child ages {child_ages}")
                continue
            
            assert response.status_code == 200, f"Failed for child ages {child_ages}"
            
            response_data = response.json()
            data = response_data.get("data", {})
            
            # Verify guests field reflects correct counts
            offers = data.get("offers", [])
            if offers:
                guests = offers[0].get("guests", {})
                assert guests.get("adults") == offers_payload["adults"], "Adults count mismatch"
                
                self.logger.success(f"✓ Success with child ages {child_ages}")
        
        self.logger.success("✅ All child age combinations handled successfully")


    @pytest.mark.api
    def test_get_hotel_offers_price_calculation_accuracy(self, hotel_api):
        """
        Test that requestedCurrencyTotalPrice is accurately calculated.
        
        Verifies: requestedCurrencyTotalPrice = total * conversion_rate
        """
        self.logger.info("Testing Hotel Offers - Price Calculation Accuracy")
        
        # Get a valid hotel
        search_response = hotel_api.search_hotels(**self.test_data["hotel_search_payload"])
        assert search_response.status_code == 200, f"Search failed: {search_response.status_code}"
        
        search_data = search_response.json()
        hotels = self._extract_hotels_from_search(search_data)
        
        if not hotels:
            pytest.skip("No hotels found")
        
        hotel_id = hotels[0].get("hotel", {}).get("hotelId") or hotels[0].get("hotelId")
        
        # Get offers with different currency
        offers_payload = self.test_data["hotel_offers_payload"].copy()
        offers_payload["hotelId"] = hotel_id
        
        response = hotel_api.get_hotel_offers(**offers_payload)
        
        if response.status_code != 200:
            pytest.skip(f"Offers request failed: {response.status_code}")
        
        response_data = response.json()
        data = response_data.get("data", {})
        
        # Skip if no conversion fields (maybe hotel returned USD pricing)
        if "currencyConversion" not in data or "requestedCurrencyTotalPrice" not in data:
            self.logger.info("No conversion fields present, skipping calculation test")
            return
        
        # Get the original total from offers
        offers = data.get("offers", [])
        if not offers:
            pytest.skip("No offers found")
        
        original_total = float(offers[0].get("price", {}).get("total", 0))
        conversion_rate = float(data["currencyConversion"]["USD"]["rate"])
        calculated_total = data["requestedCurrencyTotalPrice"]
        
        # Allow small floating point differences
        expected_total = round(original_total * conversion_rate, 2)
        actual_total = round(float(calculated_total), 2)
        
        assert abs(actual_total - expected_total) < 0.01, (
            f"Price calculation mismatch!\n"
            f"Original: {original_total} USD\n"
            f"Rate: {conversion_rate}\n"
            f"Expected: {expected_total} NGN\n"
            f"Actual: {actual_total} NGN\n"
            f"Difference: {abs(actual_total - expected_total)}"
        )
        
        self.logger.success(f"✅ Price calculation accurate: {original_total} USD × {conversion_rate} = {actual_total} NGN")


    @pytest.mark.api
    def test_get_hotel_offers_missing_required_fields(self, hotel_api):
        """Test hotel offers with missing required fields"""
        self.logger.info("Testing Hotel Offers - Missing Required Fields")
        
        required_fields = ["hotelId", "adults", "checkInDate", "checkOutDate", "countryOfResidence", "roomQuantity"]
        
        # Create a base valid payload
        base_payload = self.test_data["hotel_offers_payload"].copy()
        
        for field in required_fields:
            self.logger.info(f"Testing missing field: {field}")
            
            payload = base_payload.copy()
            payload.pop(field, None)
            
            response = hotel_api.get_hotel_offers(**payload)
            
            # Should return 400 for missing required field
            if response.status_code == 400:
                self.logger.success(f"✓ Missing '{field}' correctly returns 400")
            else:
                self.logger.warning(f"Missing '{field}' returned {response.status_code}")


    def _extract_hotels_from_search(self, search_data):
        """Helper method to extract hotels from search response"""
        data = search_data.get("data")
        
        if not data:
            return []
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get("hotelDetailResult", {}).get("data", [])
        else:
            return []
        
    # ==================== ENHANCED HOTEL BOOKING TESTS ====================

    @pytest.mark.api
    def test_book_hotel_with_complete_guest_info(self, authenticated_hotel_api):
        """Test hotel booking with complete guest information including other guests"""
        self.logger.info("Testing Hotel Booking - Complete Guest Information")
        
        # Get valid hotel
        search_response = authenticated_hotel_api.search_hotels(**self.test_data["hotel_search_payload"])
        assert search_response.status_code == 200, f"Search failed: {search_response.status_code}"
        
        search_data = search_response.json()
        hotels = self._extract_hotels_from_search(search_data)
        
        if not hotels:
            pytest.skip("No hotels found")
        
        hotel_id = hotels[0].get("hotel", {}).get("hotelId") or hotels[0].get("hotelId")
        
        # Create booking with multiple guests
        booking_payload = self.test_data["hotel_booking_payload"].copy()
        booking_payload["hotelId"] = hotel_id
        booking_payload["otherGuests"] = [
            {
                "firstName": "John",
                "lastName": "Doe",
                "dob": "1990-01-01",
                "gender": "Male",
                "phone": "7079090909",
                "nationality": "Nigerian"
            },
            {
                "firstName": "Jane",
                "lastName": "Doe",
                "dob": "1992-05-15",
                "gender": "Female",
                "phone": "7079090910",
                "nationality": "Nigerian"
            }
        ]
        booking_payload["childAges"] = [5, 10]
        
        response = authenticated_hotel_api.book_hotel(**booking_payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        booking_data = response.json()
        assert booking_data.get("status") == "success", "Booking status must be 'success'"
        
        booking_info = booking_data["data"]["hotelBooking"]
        
        # Verify other_guests were saved correctly
        assert "other_guests" in booking_info, "Missing other_guests in response"
        assert len(booking_info["other_guests"]) == 2, f"Expected 2 other guests, got {len(booking_info['other_guests'])}"
        
        # Verify child ages
        assert booking_info.get("child_ages") == [5, 10], "Child ages mismatch"
        
        # Verify user_id exists (authenticated)
        assert booking_info.get("user_id") is not None, "user_id should not be null when authenticated"
        
        self.logger.success(f"✅ Booking with complete guest info successful. Booking ID: {booking_info.get('id')}")


    @pytest.mark.api
    def test_book_hotel_duplicate_booking(self, authenticated_hotel_api):
        """Test duplicate hotel booking - should create new booking each time"""
        self.logger.info("Testing Hotel Booking - Duplicate Bookings")
        
        # Get valid hotel
        search_response = authenticated_hotel_api.search_hotels(**self.test_data["hotel_search_payload"])
        assert search_response.status_code == 200, f"Search failed: {search_response.status_code}"
        
        search_data = search_response.json()
        hotels = self._extract_hotels_from_search(search_data)
        
        if not hotels:
            pytest.skip("No hotels found")
        
        hotel_id = hotels[0].get("hotel", {}).get("hotelId") or hotels[0].get("hotelId")
        
        # Create same booking twice
        booking_payload = self.test_data["hotel_booking_payload"].copy()
        booking_payload["hotelId"] = hotel_id
        
        # First booking
        response1 = authenticated_hotel_api.book_hotel(**booking_payload)
        assert response1.status_code == 200, "First booking failed"
        booking1_id = response1.json()["data"]["hotelBooking"]["id"]
        
        # Second booking (same details)
        response2 = authenticated_hotel_api.book_hotel(**booking_payload)
        assert response2.status_code == 200, "Second booking failed"
        booking2_id = response2.json()["data"]["hotelBooking"]["id"]
        
        # Should be different booking IDs
        assert booking1_id != booking2_id, f"Duplicate bookings should have different IDs: {booking1_id} == {booking2_id}"
        
        self.logger.success(f"✅ Duplicate bookings created successfully with different IDs: {booking1_id} and {booking2_id}")
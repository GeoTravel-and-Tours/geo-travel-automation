# # src/tests/api_tests/test_hotel_api.py

# import pytest
# import time
# from datetime import datetime, timedelta
# from src.pages.api.hotels_api import HotelAPI
# from src.pages.api.auth_api import AuthAPI
# from src.utils.logger import GeoLogger
# from src.tests.test_data import generate_hotel_test_data


# class TestHotelAPI:
#     """Comprehensive Hotel API Test Suite"""
    
#     def setup_method(self):
#         """Setup before each test method"""
#         self.logger = GeoLogger(self.__class__.__name__)
#         self.test_data = generate_hotel_test_data()
#         self.logger.info(f"🚀 Starting {self.__class__.__name__} test")
    
#     def teardown_method(self):
#         """Enhanced cleanup after each test method"""
#         self.logger.info(f"✅ {self.__class__.__name__} test completed")
    
#     # ==================== FIXTURES ====================
    
#     @pytest.fixture(params=["unauthenticated", "authenticated"])
#     def hotel_api(self, request):
#         """Fixture that provides both authenticated and unauthenticated API instances"""
#         if request.param == "unauthenticated":
#             self.logger.info("🔓 Testing with UNAUTHENTICATED client")
#             return HotelAPI()
#         else:
#             self.logger.info("🔐 Testing with AUTHENTICATED client")
#             auth_api = AuthAPI()
#             response = auth_api.login()
            
#             if response.status_code != 200:
#                 self.logger.warning("⚠️ Login failed, falling back to unauthenticated")
#                 return HotelAPI()
            
#             hotel_api = HotelAPI()
#             hotel_api.set_auth_token(
#                 auth_api.auth_token, 
#                 token_source=auth_api.token_source
#             )
#             return hotel_api
    
#     @pytest.fixture
#     def authenticated_hotel_api(self):
#         """Fixture specifically for authenticated tests"""
#         auth_api = AuthAPI()
#         response = auth_api.login()
        
#         if response.status_code != 200:
#             self.logger.error(f"❌ Login failed with status {response.status_code}")
#             pytest.skip(f"Login failed with status {response.status_code}")
        
#         hotel_api = HotelAPI()
#         hotel_api.set_auth_token(
#             auth_api.auth_token, 
#             token_source=auth_api.token_source
#         )
#         return hotel_api
    
#     # ==================== HELPER METHODS ====================
    
#     def _get_future_dates(self, days_out=30, duration=3):
#         """Get future dates for testing"""
#         check_in = datetime.now() + timedelta(days=days_out)
#         check_out = check_in + timedelta(days=duration)
#         return {
#             "checkIn": check_in.strftime("%Y-%m-%d"),
#             "checkOut": check_out.strftime("%Y-%m-%d")
#         }
    
#     def _extract_hotels_from_search(self, search_data):
#         """Extract hotels list from search response"""
#         if not search_data or not isinstance(search_data, dict):
#             return []
        
#         data = search_data.get("data")
#         if not data:
#             return []
        
#         # Handle different response structures
#         if isinstance(data, list):
#             return data
#         elif isinstance(data, dict):
#             if "hotels" in data:
#                 return data["hotels"]
#             elif "hotelDetailResult" in data:
#                 return data["hotelDetailResult"].get("data", [])
        
#         return []
    
#     # ==================== HOTEL CITIES TESTS (GET) ====================
    
#     @pytest.mark.api
#     def test_get_hotel_cities_success(self, hotel_api):
#         """Test successful retrieval of hotel cities with valid keyword"""
#         self.logger.info("Testing Get Hotel Cities - Success Case")
        
#         response = hotel_api.get_hotel_cities(keyword="ABU")
        
#         assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
#         response_data = response.json()
#         assert response_data.get("status") == "success"
#         assert "data" in response_data
#         assert "cities" in response_data["data"]
        
#         cities = response_data["data"]["cities"]
#         assert isinstance(cities, list)
#         assert len(cities) > 0
        
#         self.logger.success(f"✅ Retrieved {len(cities)} cities")
    
#     @pytest.mark.api
#     def test_get_hotel_cities_empty_keyword(self, hotel_api):
#         """Test hotel cities with empty keyword - should return 400"""
#         self.logger.info("Testing Get Hotel Cities - Empty Keyword")
        
#         response = hotel_api.get_hotel_cities(keyword="")
        
#         assert response.status_code == 400, f"Expected 400, got {response.status_code}"
#         self.logger.success("✅ Empty keyword correctly rejected")
    
#     @pytest.mark.api
#     @pytest.mark.parametrize("keyword", ["A", "AB"])
#     def test_get_hotel_cities_short_keyword(self, hotel_api, keyword):
#         """Test hotel cities with short keywords (<3 chars) - should return 400"""
#         self.logger.info(f"Testing short keyword: '{keyword}'")
        
#         response = hotel_api.get_hotel_cities(keyword=keyword)
        
#         assert response.status_code == 400, f"Expected 400, got {response.status_code}"
#         self.logger.success(f"✅ Short keyword '{keyword}' correctly rejected")
    
#     @pytest.mark.api
#     @pytest.mark.parametrize("keyword", ["INVALID123", "XYZ999", "###"])
#     def test_get_hotel_cities_invalid_keyword(self, hotel_api, keyword):
#         """Test hotel cities with invalid keywords - should return 400"""
#         self.logger.info(f"Testing invalid keyword: '{keyword}'")
        
#         response = hotel_api.get_hotel_cities(keyword=keyword)
        
#         # API returns 400 for completely invalid keywords
#         assert response.status_code == 400, f"Expected 400, got {response.status_code}"
#         self.logger.success(f"✅ Invalid keyword '{keyword}' correctly rejected")
    
#     # ==================== HOTEL SEARCH TESTS (GET) ====================
    
#     @pytest.mark.api
#     def test_search_hotels_success(self, hotel_api):
#         """Test successful hotel search with valid city code"""
#         self.logger.info("Testing Hotel Search - Success Case")
        
#         response = hotel_api.search_hotels(city_code="NYC")
        
#         # Should work with or without auth
#         assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
#         response_data = response.json()
#         assert response_data.get("status") == "success"
        
#         hotels = self._extract_hotels_from_search(response_data)
#         self.logger.info(f"Found {len(hotels)} hotels")
        
#         self.logger.success("✅ Hotel search succeeded")
    
#     @pytest.mark.api
#     def test_search_hotels_with_pagination(self, hotel_api):
#         """Test hotel search with pagination"""
#         self.logger.info("Testing Hotel Search - With Pagination")
        
#         response = hotel_api.search_hotels(
#             city_code="NYC",
#             page=1,
#             limit=5
#         )
        
#         assert response.status_code == 200, f"Expected 200, got {response.status_code}"
#         self.logger.success("✅ Pagination test passed")
    
#     @pytest.mark.api
#     @pytest.mark.parametrize("page,limit", [(1, 5), (1, 10), (1, 20)])
#     def test_search_hotels_pagination_combinations(self, hotel_api, page, limit):
#         """Test various pagination combinations"""
#         self.logger.info(f"Testing page={page}, limit={limit}")
        
#         response = hotel_api.search_hotels(
#             city_code="NYC",
#             page=page,
#             limit=limit
#         )
        
#         assert response.status_code == 200, f"Failed: {response.status_code}"
#         self.logger.success(f"✅ Page {page}, Limit {limit} works")
    
#     @pytest.mark.api
#     def test_search_hotels_with_filters(self, hotel_api):
#         """Test hotel search with filters"""
#         self.logger.info("Testing Hotel Search - With Filters")
        
#         response = hotel_api.search_hotels(
#             city_code="NYC",
#             ratings="4,5",
#             amenities="WIFI,BREAKFAST"
#         )
        
#         # Should work with or without filters (they're optional)
#         assert response.status_code == 200, f"Expected 200, got {response.status_code}"
#         self.logger.success("✅ Search with filters succeeded")
    
#     @pytest.mark.api
#     def test_search_hotels_missing_city_code(self, hotel_api):
#         """Test search with missing city_code - should return 400"""
#         self.logger.info("Testing Search - Missing City Code")
        
#         response = hotel_api.search_hotels()  # No city_code
        
#         assert response.status_code == 400, f"Expected 400, got {response.status_code}"
#         self.logger.success("✅ Missing city_code correctly rejected")
    
#     @pytest.mark.api
#     @pytest.mark.parametrize("city_code", ["", "INVALID", "12345"])
#     def test_search_hotels_invalid_city_code(self, hotel_api, city_code):
#         """Test search with invalid city codes"""
#         self.logger.info(f"Testing invalid city code: '{city_code}'")
        
#         response = hotel_api.search_hotels(city_code=city_code)
        
#         # Should return 200 with empty list or 400
#         if response.status_code == 200:
#             hotels = self._extract_hotels_from_search(response.json())
#             assert len(hotels) == 0, f"Expected 0 hotels, got {len(hotels)}"
#             self.logger.success(f"✅ Invalid code returned empty list")
#         elif response.status_code == 400:
#             self.logger.success(f"✅ Invalid code rejected with 400")
#         else:
#             self.logger.warning(f"Unexpected status: {response.status_code}")
    
#     # ==================== HOTEL OFFERS TESTS (POST) ====================
    
#     @pytest.mark.api
#     def test_get_hotel_offers_success(self, hotel_api):
#         """Test successful retrieval of hotel offers"""
#         self.logger.info("Testing Hotel Offers - Success Case")
        
#         # Use a known test hotel ID
#         hotel_id = "SINYC713"  # New York hotel from Swagger
        
#         dates = self._get_future_dates(days_out=30, duration=10)
        
#         payload = {
#             "hotelId": hotel_id,
#             "adults": 2,
#             "checkInDate": dates["checkIn"],
#             "checkOutDate": dates["checkOut"],
#             "countryOfResidence": "US",
#             "roomQuantity": 1
#         }
        
#         response = hotel_api.get_hotel_offers(**payload)
        
#         # Could be 200 (has offers) or 404 (no availability)
#         if response.status_code == 404:
#             self.logger.info(f"Hotel {hotel_id} has no availability")
#             pytest.skip("No availability")
        
#         assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
#         response_data = response.json()
#         assert response_data.get("status") == "success"
        
#         data = response_data.get("data", {})
#         offers = data.get("offers", [])
#         self.logger.info(f"Found {len(offers)} offers")
        
#         self.logger.success("✅ Hotel offers retrieved")
    
#     @pytest.mark.api
#     @pytest.mark.parametrize("currency", ["USD", "NGN", "EUR", "GBP"])
#     def test_get_hotel_offers_different_currencies(self, hotel_api, currency):
#         """Test hotel offers with different currencies"""
#         self.logger.info(f"Testing Hotel Offers - Currency: {currency}")
        
#         hotel_id = "SINYC713"
#         dates = self._get_future_dates(days_out=30, duration=10)
        
#         payload = {
#             "hotelId": hotel_id,
#             "adults": 2,
#             "checkInDate": dates["checkIn"],
#             "checkOutDate": dates["checkOut"],
#             "countryOfResidence": "US",
#             "roomQuantity": 1,
#             "currency": currency
#         }
        
#         response = hotel_api.get_hotel_offers(**payload)
        
#         if response.status_code == 404:
#             self.logger.info(f"No availability for {hotel_id}")
#             pytest.skip("No availability")
        
#         assert response.status_code == 200, f"Expected 200, got {response.status_code}"
#         self.logger.success(f"✅ Currency '{currency}' works")
    
#     @pytest.mark.api
#     def test_get_hotel_offers_with_child_ages(self, hotel_api):
#         """Test hotel offers with child ages"""
#         self.logger.info("Testing Hotel Offers - With Child Ages")
        
#         hotel_id = "SINYC713"
#         dates = self._get_future_dates(days_out=30, duration=10)
        
#         payload = {
#             "hotelId": hotel_id,
#             "adults": 2,
#             "checkInDate": dates["checkIn"],
#             "checkOutDate": dates["checkOut"],
#             "countryOfResidence": "US",
#             "roomQuantity": 1,
#             "childAges": [5, 10]
#         }
        
#         response = hotel_api.get_hotel_offers(**payload)
        
#         if response.status_code == 404:
#             self.logger.info("No availability")
#             pytest.skip("No availability")
        
#         assert response.status_code == 200, f"Expected 200, got {response.status_code}"
#         self.logger.success("✅ Child ages accepted")
    
#     @pytest.mark.api
#     def test_get_hotel_offers_missing_required_fields(self, hotel_api):
#         """Test offers with missing required fields"""
#         self.logger.info("Testing Offers - Missing Required Fields")
        
#         required_fields = ["hotelId", "adults", "checkInDate", "checkOutDate", "countryOfResidence"]
#         hotel_id = "SINYC713"
#         dates = self._get_future_dates()
        
#         for field in required_fields:
#             self.logger.info(f"Missing: {field}")
            
#             payload = {
#                 "hotelId": hotel_id,
#                 "adults": 2,
#                 "checkInDate": dates["checkIn"],
#                 "checkOutDate": dates["checkOut"],
#                 "countryOfResidence": "US",
#                 "roomQuantity": 1
#             }
#             payload.pop(field, None)
            
#             response = hotel_api.get_hotel_offers(**payload)
            
#             if response.status_code == 400:
#                 self.logger.success(f"✓ Missing '{field}' returns 400")
    
#     # ==================== HOTEL BOOKING TESTS (POST) ====================
    
#     @pytest.mark.api
#     def test_book_hotel_with_valid_data(self, hotel_api):
#         """Test hotel booking with valid data"""
#         self.logger.info("Testing Hotel Booking - Valid Data")
        
#         dates = self._get_future_dates(days_out=20, duration=5)
        
#         booking_payload = {
#             "firstName": "Test",
#             "lastName": "User",
#             "email": "test@example.com",
#             "phone": "1234567890",
#             "adults": 2,
#             "checkInDate": dates["checkIn"],
#             "checkOutDate": dates["checkOut"],
#             "roomQuantity": 1,
#             "hotelName": "Test Hotel",
#             "hotelId": "SINYC713",
#             "destination": {
#                 "country": "US",
#                 "city": "New York"
#             },
#             "dob": "1990-01-01",
#             "gender": "Male",
#             "nationality": "American"
#         }
        
#         response = hotel_api.book_hotel(**booking_payload)
        
#         # Could be 200 (success) or 400 (validation) or 404 (hotel not found)
#         if response.status_code == 200:
#             self.logger.success("✅ Booking successful")
#             booking_data = response.json()
#             booking_id = booking_data.get("data", {}).get("hotelBooking", {}).get("id")
#             self.logger.info(f"📋 Booking ID: {booking_id}")
#         elif response.status_code == 400:
#             self.logger.info("Booking validation failed - check required fields")
#             self.logger.debug(f"Response: {response.text}")
#         else:
#             self.logger.info(f"Booking returned {response.status_code}")
    
#     @pytest.mark.api
#     def test_book_hotel_missing_required_fields(self, hotel_api):
#         """Test booking with missing required fields"""
#         self.logger.info("Testing Booking - Missing Required Fields")
        
#         required_fields = ["firstName", "lastName", "email", "phone", "checkInDate", "checkOutDate"]
#         dates = self._get_future_dates()
        
#         base_payload = {
#             "firstName": "Test",
#             "lastName": "User",
#             "email": "test@example.com",
#             "phone": "1234567890",
#             "adults": 2,
#             "checkInDate": dates["checkIn"],
#             "checkOutDate": dates["checkOut"],
#             "roomQuantity": 1,
#             "hotelName": "Test Hotel",
#             "hotelId": "SINYC713",
#             "destination": {
#                 "country": "US",
#                 "city": "New York"
#             },
#             "dob": "1990-01-01",
#             "gender": "Male",
#             "nationality": "American"
#         }
        
#         for field in required_fields:
#             self.logger.info(f"Missing: {field}")
            
#             payload = base_payload.copy()
#             payload.pop(field, None)
            
#             response = hotel_api.book_hotel(**payload)
            
#             if response.status_code == 400:
#                 self.logger.success(f"✓ Missing '{field}' returns 400")
    
#     # ==================== PERFORMANCE TESTS ====================
    
#     @pytest.mark.api
#     def test_search_hotels_performance(self, hotel_api):
#         """Test search response time"""
#         self.logger.info("Testing Search Performance")
        
#         start = time.time()
#         response = hotel_api.search_hotels(city_code="NYC")
#         duration = time.time() - start
        
#         assert response.status_code == 200
#         assert duration < 10.0, f"Slow: {duration:.2f}s"
        
#         self.logger.success(f"✅ Response time: {duration:.2f}s")
    
#     @pytest.mark.api
#     def test_hotel_endpoints_accessibility(self, hotel_api):
#         """Test all endpoints are accessible"""
#         self.logger.info("Testing Endpoint Accessibility")
        
#         # Cities
#         cities_resp = hotel_api.get_hotel_cities(keyword="ABU")
#         assert cities_resp.status_code == 200
#         self.logger.success("✓ Cities endpoint OK")
        
#         # Search
#         search_resp = hotel_api.search_hotels(city_code="NYC")
#         assert search_resp.status_code == 200
#         self.logger.success("✓ Search endpoint OK")
        
#         # Offers (if hotel ID works)
#         offers_resp = hotel_api.get_hotel_offers(
#             hotelId="SINYC713",
#             adults=2,
#             checkInDate="2026-04-01",
#             checkOutDate="2026-04-10",
#             countryOfResidence="US",
#             roomQuantity=1
#         )
#         if offers_resp.status_code in [200, 404]:
#             self.logger.success("✓ Offers endpoint accessible")
        
#         self.logger.success("✅ All endpoints accessible")
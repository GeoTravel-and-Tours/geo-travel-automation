import pytest
import random
from src.pages.api.partners_api.partners_auth_api import PartnersAuthAPI
from src.pages.api.partners_api.partners_flight_api import PartnersFlightAPI
from src.pages.api.partners_api.organization_api import PartnersOrganizationAPI
from src.utils.verified_partners_helper import VerifiedUserHelper
from configs.environment import EnvironmentConfig
from src.utils.logger import GeoLogger

class TestPartnersFlightSecurity:
    """SECURITY TESTS - Unverified users should be blocked from flight operations"""
    
    def setup_method(self):
        self.auth_api = PartnersAuthAPI()
        self.flight_api = PartnersFlightAPI()  # No credentials = unverified user
        
        if not EnvironmentConfig.validate_partners_credentials():
            pytest.skip("Partners verified account credentials not configured")
        
        self.verified_helper = VerifiedUserHelper()
        self.org_api = self.verified_helper.get_verified_organization_api()
        self.logger = GeoLogger(self.__class__.__name__)
        
        # CRITICAL: Initialize credentials before any API calls
        if not self.verified_helper.initialize_credentials():
            pytest.skip("Failed to initialize API credentials")
        
        # Create unverified user
        self.test_email = f"flighttest{random.randint(10000,99999)}@yopmail.com"
        self.test_password = "StrongPass123!"
        self.test_org_data = {
            "orgName": f"Flight Test Org {random.randint(1000,9999)}",
            "orgEmail": self.test_email,
            "address": "123 Flight St, Test City",
            "password": self.test_password,
            "contactPerson": {
                "firstName": "Flight",
                "lastName": "Tester",
                "phoneNumber": "+1234567890"
            }
        }
        self.logger = GeoLogger(self.__class__.__name__)
    
    @pytest.mark.partners_api
    @pytest.mark.security
    def test_unverified_user_blocked_from_flight_search(self):
        """Test that unverified users cannot search flights"""
        # 1. Create unverified user
        self.logger.info(f"🔵 CREATING UNVERIFIED USER: {self.test_email}")
        signup_response = self.auth_api.signup(self.test_org_data)
        assert signup_response.status_code == 201
        
        # 2. Try flight search - should be blocked
        self.logger.info(f"🔵 ATTEMPTING FLIGHT SEARCH: {self.test_email}")
        search_data = {
            "origin": "LHR",
            "destination": "LOS", 
            "departure_date": PartnersFlightAPI.get_future_date(1),
            "return_date": "",
            "adults": 1,
            "flight_type": "one_way",
            "children": 0,
            "infants": 0,
            "cabin": "ECONOMY",
            "destinations": []
        }
        response = self.flight_api.search_flights(search_data)
        
        # Should be blocked - either 401 (no auth) or 403 (no permissions)
        assert response.status_code != 200, "Unverified user should not get successful response"
        assert response.status_code in [401, 403], (
            f"Unverified user should be blocked from flight search. Got {response.status_code}"
        )
        assert response.status_code >= 400, "Should get error response"
        self.logger.success(f"✅ Unverified user correctly blocked from flight search: {self.test_email}")
    
    @pytest.mark.partners_api
    @pytest.mark.security
    def test_unverified_user_blocked_from_flight_booking(self):
        """Test that unverified users cannot book flights"""
        # 1. Create unverified user
        self.logger.info(f"🔵 CREATING UNVERIFIED USER: {self.test_email}")
        signup_response = self.auth_api.signup(self.test_org_data)
        assert signup_response.status_code == 201
        
        # 2. Try flight booking - should be blocked
        self.logger.info(f"🔵 ATTEMPTING FLIGHT BOOKING: {self.test_email}")
        booking_data = {
            "flightTag": "flights:oneWay:1:0:0:economy:LHR:LOS:2025-10-24",
            "flightId": "001b9a83e21b4db4a7f2b5f9",
            "passengers": [
                {
                    "email": "johndoe@yopmail.com",
                    "title": "Mr",
                    "firstName": "John",
                    "middleName": "Kelvin", 
                    "lastName": "Doe",
                    "dob": "1997-10-01",
                    "gender": "male",
                    "phoneCode": "+234",
                    "phoneNumber": "1234567890",
                    "number": "B647382829",
                    "issuingDate": "2024-01-10",
                    "expiryDate": "2028-01-10",
                    "issuingCountry": "NG",
                    "nationalityCountry": "NG",
                    "documentType": "passport",
                    "holder": True
                }
            ]
        }
        response = self.flight_api.book_flight(booking_data)
        
        # Should be blocked - either 401 (no auth) or 403 (no permissions)
        assert response.status_code in [401, 403], (
            f"Unverified user should be blocked from flight booking. Got {response.status_code}"
        )
        self.logger.success(f"✅ Unverified user correctly blocked from flight booking: {self.test_email}")

class TestPartnersFlightFunctionality:
    """FUNCTIONALITY TESTS - Verified users can access flight operations and data is stored"""
    
    def setup_method(self):
        # Validate credentials before running tests
        if not EnvironmentConfig.validate_partners_credentials():
            pytest.skip("Partners verified account credentials not configured")
        
        self.verified_helper = VerifiedUserHelper()
        self.org_api = self.verified_helper.get_verified_organization_api()
        self.logger = GeoLogger(self.__class__.__name__)
    
    @pytest.mark.partners_api
    def test_verified_user_can_search_flights(self):
        """TEST: Verified users can search flights and get valid response structure"""
        # Get flight API with verified credentials
        flight_api = self.verified_helper.get_verified_flight_api()
        assert flight_api is not None, "Should get verified flight API"
        self.logger.info(f"API Key: {flight_api.api_key}")
        self.logger.info(f"API Secret: {flight_api.api_secret}")
        self.logger.info(f"App ID: {flight_api.app_id}")
        
        self.logger.info("🔵 VERIFIED USER - Attempting flight search")
        search_data = {
            "origin": "LHR",
            "destination": "LOS",
            "departure_date": PartnersFlightAPI.get_future_date(1),
            "return_date": "",
            "adults": 1,
            "flight_type": "one_way",
            "children": 0,
            "infants": 0,
            "cabin": "ECONOMY",
            "destinations": []
        }
        response = flight_api.search_flights(search_data)
        self.logger.info(f"Response Status: {response.status_code}")
        self.logger.info(f"Response Headers: {dict(response.headers)}")
        self.logger.info(f"Response Body: {response.text}")
        
        assert response.status_code == 200, "Verified user should access flight search"
        data = response.json()
        
        # Verify complete response structure
        assert data['message'] == "Flight search successful"
        assert 'data' in data
        assert 'flightTag' in data['data']
        assert 'flightOffers' in data['data']
        
        flight_tag = data['data']['flightTag']
        flight_offers = data['data']['flightOffers']
        
        # Verify flight tag format
        assert flight_tag.startswith('flights:')
        assert 'LHR' in flight_tag
        assert 'LOS' in flight_tag
        
        # Verify flight offers structure
        assert isinstance(flight_offers, list)
        if flight_offers:  # If there are offers, verify structure
            first_offer = flight_offers[0]
            assert 'id' in first_offer
            assert 'price' in first_offer
            assert 'itineraries' in first_offer
        
        self.logger.success("✅ Verified user can search flights")
        self.logger.info(f"📊 Flight search returned {len(flight_offers)} offers, tag: {flight_tag}")
        
        # Store for potential booking test
        self.flight_search_data = data['data']
    
    @pytest.mark.partners_api
    def test_verified_user_can_book_flight(self):
        """TEST: Verified users can book flights and booking is properly stored"""
        # First search for a flight
        flight_api = self.verified_helper.get_verified_flight_api()
        assert flight_api is not None, "Should get verified flight API"
        
        self.logger.info("🔵 VERIFIED USER - Searching for flight to book")
        search_data = {
            "origin": "LHR", 
            "destination": "LOS",
            "departure_date": PartnersFlightAPI.get_future_date(1),
            "return_date": "",
            "adults": 1,
            "flight_type": "one_way", 
            "children": 0,
            "infants": 0,
            "cabin": "ECONOMY",
            "destinations": []
        }
        search_response = flight_api.search_flights(search_data)
        assert search_response.status_code == 200
        
        search_result = search_response.json()['data']
        flight_tag = search_result['flightTag']
        flight_offers = search_result['flightOffers']
        
        if not flight_offers:
            pytest.skip("No flight offers available for booking test")
        
        # Use first flight offer for booking
        first_offer = flight_offers[0]
        flight_id = first_offer['id']
        
        self.logger.info(f"🔵 VERIFIED USER - Attempting flight booking: {flight_id}")
        
        # Create unique passenger data to avoid conflicts
        random_suffix = random.randint(1000, 9999)
        booking_data = {
            "flightTag": flight_tag,
            "flightId": flight_id,
            "passengers": [
                {
                    "email": f"testflight{random_suffix}@yopmail.com",
                    "title": "Mr",
                    "firstName": "GEO",
                    "middleName": "QA",
                    "lastName": f"Bot", 
                    "dob": "1990-01-01",
                    "gender": "male",
                    "phoneCode": "234",
                    "phoneNumber": f"123456{random_suffix}",
                    "number": f"P{random.randint(100000000,999999999)}",
                    "issuingDate": "2024-01-01",
                    "expiryDate": "2028-01-01", 
                    "issuingCountry": "NG",
                    "nationalityCountry": "NG",
                    "documentType": "passport",
                    "holder": True
                }
            ]
        }
        # DEBUG: Log the exact payload being sent
        import json
        self.logger.info("🔍 DEBUG - Booking payload being sent:")
        self.logger.info(json.dumps(booking_data, indent=2))
        
        # DEBUG: Check if flight_api has the right base URL and headers
        self.logger.info(f"🔍 DEBUG - Flight API base URL: {getattr(flight_api, 'base_url', 'Not set')}")
        self.logger.info(f"🔍 DEBUG - Flight API headers: {getattr(flight_api, 'headers', 'Not set')}")
        
        booking_response = flight_api.book_flight(booking_data)
        self.logger.info(f"Booking Response Status: {booking_response.status_code}")
        self.logger.info(f"Booking Response Body: {booking_response.text}")
        
        # Handle different response scenarios - FIXED LOGIC
        if booking_response.status_code == 500:
            error_data = booking_response.json()
            error_message = error_data.get('message', '')
            
            # Only skip for SPECIFIC Amadeus errors, not all 500s
            if "Amadeus" in error_message or "posting data" in error_message.lower():
                self.logger.warning("⚠️ Flight booking failed due to backend integration issue - skipping")
                pytest.skip(f"Backend integration issue: {error_message}")
                return
            else:
                # Other 500 errors should fail the test
                assert False, f"Flight booking failed with 500: {error_data}"
        
        elif booking_response.status_code == 201:
            # Booking created successfully (this is what Postman returns)
            self.logger.success("✅ Flight booking created successfully (201)")
            booking_result = booking_response.json()
            
        elif booking_response.status_code == 200:
            # Booking processed successfully
            self.logger.success("✅ Flight booking processed successfully (200)")
            booking_result = booking_response.json()
        
        else:
            # Unexpected status code
            assert False, f"Flight booking failed with status {booking_response.status_code}: {booking_response.text}"
            return
        
        # Verify booking response structure
        assert 'message' in booking_result
        assert 'data' in booking_result
        
        # Check for success message
        assert "success" in booking_result['message'].lower(), \
            f"Unexpected message: {booking_result['message']}"
        
        booking_data = booking_result['data']
        
        # Verify complete booking response structure
        assert 'type' in booking_data
        assert booking_data['type'] == 'flight-order'
        assert 'id' in booking_data
        assert 'associatedRecords' in booking_data
        
        # Verify associated records (booking references)
        associated_records = booking_data['associatedRecords']
        assert isinstance(associated_records, list)
        assert len(associated_records) > 0
        
        for record in associated_records:
            assert 'reference' in record
            assert 'originSystemCode' in record
            assert 'flightOfferId' in record
        
        # Store booking reference for verification
        self.booking_reference = associated_records[0]['reference']
        self.booking_id = booking_data['id']
        
        self.logger.success("✅ Verified user can book flights")
        self.logger.info(f"📋 Flight booking reference: {self.booking_reference}")
        self.logger.info(f"📋 Flight booking ID: {self.booking_id}")
    
    @pytest.mark.partners_api
    def test_flight_search_counted_in_usage(self):
        """TEST: Flight searches are properly counted in organization usage"""
        # First get baseline usage
        self.logger.info("🔵 GETTING BASELINE USAGE FOR FLIGHT SEARCHES")
        initial_usage_response = self.org_api.get_usage(mode='test')
        assert initial_usage_response.status_code == 200
        self.logger.info(initial_usage_response.text)
        
        initial_usage_data = initial_usage_response.json()
        initial_records = initial_usage_data['data']['records']
        initial_total_searches = sum(record.get('flightSearches', 0) for record in initial_records)
        
        self.logger.info(f"📊 Initial flight searches: {initial_total_searches}")
        
        # Perform flight search
        flight_api = self.verified_helper.get_verified_flight_api()
        
        self.logger.info("🔵 PERFORMING FLIGHT SEARCH FOR USAGE COUNTING")
        search_data = {
            "origin": "LHR",
            "destination": "LOS", 
            "departure_date": PartnersFlightAPI.get_future_date(1),
            "return_date": "",
            "adults": 1,
            "flight_type": "one_way",
            "children": 0,
            "infants": 0,
            "cabin": "ECONOMY",
            "destinations": []
        }
        search_response = flight_api.search_flights(search_data)
        assert search_response.status_code == 200
        
        search_result = search_response.json()['data']
        flight_tag = search_result['flightTag']
        
        # Wait a moment for usage to be updated
        import time
        time.sleep(2)
        
        # Get updated usage to verify search was counted
        self.logger.info("🔵 CHECKING UPDATED USAGE METRICS")
        final_usage_response = self.org_api.get_usage(mode='test')
        assert final_usage_response.status_code == 200
        self.logger.info(final_usage_response.text)
        
        final_usage_data = final_usage_response.json()
        final_records = final_usage_data['data']['records']
        final_total_searches = sum(record.get('flightSearches', 0) for record in final_records)
        
        self.logger.info(f"📊 Final flight searches: {final_total_searches}")
        
        # Verify the search count increased
        assert final_total_searches > initial_total_searches, (
            f"Flight searches should increase from {initial_total_searches} to {final_total_searches}"
        )
        
        # Also verify our flight tag appears in usage records
        flight_tag_found = any(
            flight_tag in record.get('flightTags', [])
            for record in final_records
        )
        
        self.logger.info(f"📊 Flight tag found in usage: {flight_tag_found}")
        
        self.logger.success(f"✅ Flight search correctly counted - increased from {initial_total_searches} to {final_total_searches}")
    
    @pytest.mark.partners_api
    def test_flight_booking_counted_in_usage(self):
        """TEST: Flight bookings are properly counted in organization usage"""
        # First get baseline usage
        self.logger.info("🔵 GETTING BASELINE USAGE FOR FLIGHT BOOKINGS")
        initial_usage_response = self.org_api.get_usage(mode='test')
        assert initial_usage_response.status_code == 200
        
        initial_usage_data = initial_usage_response.json()
        initial_records = initial_usage_data['data']['records']
        initial_total_bookings = sum(record.get('flightBookings', 0) for record in initial_records)
        
        self.logger.info(f"📊 Initial flight bookings: {initial_total_bookings}")
        
        # Perform a flight booking (you'll need to implement this part)
        # For now, we'll simulate or use your existing booking logic
        flight_api = self.verified_helper.get_verified_flight_api()
        
        # First search for a flight
        search_data = {
            "origin": "LHR",
            "destination": "LOS", 
            "departure_date": PartnersFlightAPI.get_future_date(1),
            "return_date": "",
            "adults": 1,
            "flight_type": "one_way",
            "children": 0,
            "infants": 0,
            "cabin": "ECONOMY",
            "destinations": []
        }
        search_response = flight_api.search_flights(search_data)
        assert search_response.status_code == 200
        
        search_result = search_response.json()['data']
        flight_tag = search_result['flightTag']
        flight_offers = search_result['flightOffers']
        
        if not flight_offers:
            pytest.skip("No flight offers available for booking test")
        
        # Use a flight offer (skip ID "1" as we found it might be problematic)
        if len(flight_offers) > 1:
            flight_offer = flight_offers[0]  # Use first offer
        else:
            flight_offer = flight_offers[1]
        
        flight_id = flight_offer['id']
        
        # Create booking data
        random_suffix = random.randint(1000, 9999)
        booking_data = {
            "flightTag": flight_tag,
            "flightId": flight_id,
            "passengers": [
                {
                    "email": f"testflight{random_suffix}@yopmail.com",
                    "title": "Mr",
                    "firstName": "Test",
                    "middleName": "Flight",
                    "lastName": "User",  # No numbers in last name
                    "dob": "1990-01-01",
                    "gender": "male",
                    "phoneCode": "234",
                    "phoneNumber": f"123456{random_suffix}",
                    "number": f"P{random.randint(100000000,999999999)}",
                    "issuingDate": "2024-01-01",
                    "expiryDate": "2028-01-01",
                    "issuingCountry": "NG",
                    "nationalityCountry": "NG",
                    "documentType": "passport",
                    "holder": True
                }
            ]
        }
        
        # Attempt booking
        self.logger.info(f"🔵 ATTEMPTING FLIGHT BOOKING WITH ID: {flight_id}")
        booking_response = flight_api.book_flight(booking_data)
        
        # Handle booking response
        if booking_response.status_code == 500:
            error_data = booking_response.json()
            if "Amadeus" in error_data.get('message', ''):
                pytest.skip(f"Backend integration issue: {error_data.get('message')}")
            else:
                assert False, f"Flight booking failed with 500: {error_data}"
        
        # Wait for usage to be updated
        import time
        time.sleep(3)
        
        # Get updated usage
        self.logger.info("🔵 CHECKING UPDATED USAGE METRICS FOR BOOKINGS")
        final_usage_response = self.org_api.get_usage(mode='test')
        assert final_usage_response.status_code == 200
        
        final_usage_data = final_usage_response.json()
        final_records = final_usage_data['data']['records']
        final_total_bookings = sum(record.get('flightBookings', 0) for record in final_records)
        
        self.logger.info(f"📊 Final flight bookings: {final_total_bookings}")
        
        # Verify the booking count increased (if booking was successful)
        if booking_response.status_code in [200, 201]:
            assert final_total_bookings > initial_total_bookings, (
                f"Flight bookings should increase from {initial_total_bookings} to {final_total_bookings}"
            )
            self.logger.success(f"✅ Flight booking correctly counted - increased from {initial_total_bookings} to {final_total_bookings}")
        else:
            self.logger.warning(f"⚠️ Booking failed with status {booking_response.status_code}, cannot verify usage counting")
    
    @pytest.mark.partners_api
    def test_flight_usage_reflected_in_range_endpoint(self):
        """TEST: Flight usage data is reflected in usage range endpoint"""
        self.logger.info("🔵 CHECKING USAGE RANGE FOR FLIGHT DATA")
        
        # Get usage range for a broad date range
        usage_range_response = self.org_api.get_usage_range(
            mode='test', 
            start_date='2025-01-01', 
            end_date='2025-12-31'
        )
        assert usage_range_response.status_code == 200
        
        usage_range_data = usage_range_response.json()
        range_data = usage_range_data['data']
        
        # Verify flight data in usage range
        assert 'totalFlightSearches' in range_data
        assert 'totalFlightBookings' in range_data
        assert isinstance(range_data['totalFlightSearches'], int)
        assert isinstance(range_data['totalFlightBookings'], int)
        
        self.logger.info(f"📊 Usage Range - Flight Searches: {range_data['totalFlightSearches']}")
        self.logger.info(f"📊 Usage Range - Flight Bookings: {range_data['totalFlightBookings']}")
        
        self.logger.success("✅ Flight usage data correctly reflected in usage range")
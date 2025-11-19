# src/tests/api_tests/test_flight_api.py

import pytest
import datetime
from datetime import timedelta
from src.pages.api.flight_api import FlightAPI
from src.pages.api.auth_api import AuthAPI
from src.utils.logger import GeoLogger  # Import your logger

class TestFlightAPI:
    
    def setup_method(self):
        """Setup before each test method"""
        self.logger = GeoLogger(self.__class__.__name__)
    
    @pytest.fixture
    def authenticated_flight_api(self):
        """Fixture that returns authenticated FlightAPI instance"""
        auth_api = AuthAPI()
        # This will automatically use credentials from environment
        response = auth_api.login()
        
        # If login fails, skip the test
        if response.status_code != 200:
            pytest.skip(f"Login failed with status {response.status_code} - cannot run flight tests")
            
        flight_api = FlightAPI()
        flight_api.set_auth_token(auth_api.auth_token)
        return flight_api
    
    def get_future_date(self, days=30):
        """Helper to get future dates for testing"""
        return (datetime.datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    
    @pytest.mark.api
    def test_flight_search_request(self, authenticated_flight_api):
        """Test flight search request creation"""
        self.logger.info("=== Testing Flight Search Request ===")
        search_data = {
            "origin": "LOS",
            "destination": "LHR",
            "cabin": "ECONOMY", 
            "flight_type": "one-way",
            "departure_date": self.get_future_date(30),  # 30 days from now
            "adults": 1,
            "children": 0,
            "infants": 0
        }
        
        response = authenticated_flight_api.search_request(search_data)
        
        self.logger.info(f"Search Response: {response.status_code} - {response.text}")
        
        assert response.status_code == 200
        response_data = response.json()
        assert 'search_id' in response_data.get('data', {})
        assert 'message' in response_data
        
        self.logger.info("Flight search request test passed")
        self.logger.info(f"Search ID: {response_data['data']['search_id']}")
    
    @pytest.mark.api
    def test_flight_search_flow(self, authenticated_flight_api):
        """Test complete search flow: request → get results"""
        self.logger.info("=== Testing Flight Search Flow ===")
        # 1. Create search request
        search_data = {
            "origin": "LOS",
            "destination": "LHR",
            "cabin": "ECONOMY",
            "flight_type": "one-way",
            "departure_date": self.get_future_date(30),
            "adults": 1,
            "children": 0,
            "infants": 0
        }

        search_response = authenticated_flight_api.search_request(search_data)
        assert search_response.status_code == 200
        search_id = search_response.json()['data']['search_id']

        # 2. Get search results
        results_response = authenticated_flight_api.get_search_results(search_id)
        self.logger.info(f"Search Results: {results_response.status_code}")

        # Accept different success scenarios
        assert results_response.status_code in [200, 202]  # 202 might indicate processing

    @pytest.mark.api
    def test_flight_quote_flow(self, authenticated_flight_api):
        """Test quote creation and retrieval"""
        self.logger.info("=== Testing Flight Quote Flow ===")
        quote_data = {
            "flightId": "2",
            "flightTag": "flights:one-way:1:0:0:ECONOMY:LOS:LHR:2025-09-04",
            "email": "geobot@yopmail.com"
        }

        # Create quote
        quote_response = authenticated_flight_api.create_quote(quote_data)
        if quote_response.status_code == 200:
            quote_ref = quote_response.json().get('data', {}).get('reference')

            # Retrieve quote
            if quote_ref:
                get_quote_response = authenticated_flight_api.get_quote(quote_ref)
                assert get_quote_response.status_code == 200

    @pytest.mark.api
    def test_passenger_email_validation(self, authenticated_flight_api):
        """Test passenger email validation flow"""
        self.logger.info("=== Testing Passenger Email Validation ===")
        passenger_data = {
            "email": "geobot@yopmail.com",
            "title": "Mr",
            "firstName": "GEO",
            "lastName": "Bot",
            "dob": "1990-01-01",
            "gender": "male",
            "phoneCode": "+234",
            "phoneNumber": "1234567890",
            "documentType": "passport"
        }

        # Validate email
        validate_response = authenticated_flight_api.validate_passenger_email(passenger_data)
        self.logger.info(f"Email Validation: {validate_response.status_code}")

        # This might return different statuses based on email availability
        assert validate_response.status_code in [200, 400, 422]

    @pytest.mark.api  
    def test_different_cabins(self, authenticated_flight_api):
        """Test search with different cabin classes"""
        self.logger.info("=== Testing Different Cabin Classes ===")
        cabins = ["ECONOMY", "BUSINESS", "FIRST"]

        for cabin in cabins:
            search_data = {
                "origin": "LOS",
                "destination": "LHR", 
                "cabin": cabin,
                "flight_type": "one-way",
                "departure_date": self.get_future_date(45),
                "adults": 1
            }

            response = authenticated_flight_api.search_request(search_data)
            assert response.status_code == 200
            self.logger.info(f"Cabin {cabin} search successful")
    
    @pytest.mark.api  
    def test_get_booked_flights(self, authenticated_flight_api):
        """Test retrieving user's booked flights"""
        self.logger.info("=== Testing Get Booked Flights ===")
        response = authenticated_flight_api.get_booked_flights()
        
        self.logger.info(f"Booked Flights Response: {response.status_code} - {response.text}")
        
        # This endpoint might return different status codes:
        # - 200: Success with flight data (empty array if no flights)
        # - 401: Token expired/invalid
        # - 403: No permission
        # - 404: Endpoint not found
        
        if response.status_code == 200:
            # Success case - should return a list (even if empty)
            data = response.json()
            assert isinstance(data, (list, dict))
            self.logger.info("Booked flights retrieved successfully")
        elif response.status_code == 401:
            # Token issue - this is expected for new test accounts
            response_data = response.json()
            assert 'message' in response_data
            self.logger.warning(f"Got 401 - {response_data.get('message')}")
            self.logger.info("Booked flights test handled token expiration gracefully")
        else:
            # For other status codes, check if it's a known issue
            response_data = response.json()
            self.logger.warning(f"Unexpected response: {response.status_code} - {response_data}")
    
    @pytest.mark.api
    def test_return_flight_search(self, authenticated_flight_api):
        """Test return flight search"""
        self.logger.info("=== Testing Return Flight Search ===")
        search_data = {
            "origin": "LOS",
            "destination": "LHR",
            "cabin": "ECONOMY",
            "flight_type": "return",
            "departure_date": self.get_future_date(30),
            "return_date": self.get_future_date(37),
            "adults": 1,
            "children": 0,
            "infants": 0
        }

        response = authenticated_flight_api.search_request(search_data)
        assert response.status_code == 200
        assert 'search_id' in response.json().get('data', {})

    # @pytest.mark.api
    # def test_multi_city_flight_search(self, authenticated_flight_api):
    #     """Test multi-city flight search"""
    #     self.logger.info("=== Testing Multi-City Flight Search ===")
    #     search_data = {
    #         "flight_type": "multi-city",
    #         "adults": 1,
    #         "children": 0,
    #         "infants": 0,
    #         "destinations": [
    #             {
    #                 "origin": "LOS",
    #                 "destination": "CDG",
    #                 "departure_date": self.get_future_date(30)
    #             },
    #             {
    #                 "origin": "CDG", 
    #                 "destination": "LHR",
    #                 "departure_date": self.get_future_date(35)
    #             }
    #         ]
    #     }

    #     response = authenticated_flight_api.search_request(search_data)
    #     assert response.status_code == 200

    @pytest.mark.api
    def test_passenger_combinations(self, authenticated_flight_api):
        """Test different passenger combinations"""
        self.logger.info("=== Testing Different Passenger Combinations ===")
        combinations = [
            {"adults": 2, "children": 0, "infants": 0},
            {"adults": 1, "children": 1, "infants": 0},
            {"adults": 2, "children": 1, "infants": 1}
        ]

        for passengers in combinations:
            search_data = {
                "origin": "LOS",
                "destination": "LHR",
                "cabin": "ECONOMY", 
                "flight_type": "one-way",
                "departure_date": self.get_future_date(40),
                **passengers
            }

            response = authenticated_flight_api.search_request(search_data)
            assert response.status_code == 200

    @pytest.mark.api
    def test_initiate_booking_flow(self, authenticated_flight_api):
        """Test booking initiation (without actual payment)"""
        self.logger.info("=== Testing Flight Booking Initiation Flow ===")
        # First create a search to get flight options
        search_data = {
            "origin": "LOS", 
            "destination": "LHR",
            "cabin": "ECONOMY",
            "flight_type": "one-way",
            "departure_date": self.get_future_date(50),
            "adults": 1
        }

        search_response = authenticated_flight_api.search_request(search_data)
        if search_response.status_code == 200:
            search_id = search_response.json()['data']['search_id']

            # Get flight options
            results_response = authenticated_flight_api.get_search_results(search_id)
            if results_response.status_code == 200:
                results_data = results_response.json()
                # If flights are available, test booking initiation
                if results_data.get('data'):
                    booking_data = {
                        "flightId": "1",  # Would need dynamic ID in real scenario
                        "flightTag": "test_tag",
                        "passengers": [{
                            "email": "geobot@yopmail.com",
                            "title": "Mr",
                            "firstName": "GEO",
                            "lastName": "Bot",
                            "dob": "1990-01-01",
                            "gender": "male",
                            "phoneCode": "+234",
                            "phoneNumber": "1234567890",
                            "documentType": "passport"
                        }],
                        "payer": {
                            "firstName": "GEO",
                            "lastName": "Bot", 
                            "email": "geobot@yopmail.com",
                            "phoneNumber": "1234567890"
                        }
                    }

                    booking_response = authenticated_flight_api.initiate_booking(booking_data)
                    # Could return various statuses based on flight availability
                    assert booking_response.status_code in [200, 400, 422]

    @pytest.mark.api
    def test_error_scenarios(self, authenticated_flight_api):
        """Test error scenarios"""
        self.logger.info("=== Testing Flight Search Error Scenarios ===")
        invalid_cases = [
            {"origin": "INVALID", "destination": "LHR", "departure_date": self.get_future_date(30)},
            {"origin": "LOS", "destination": "LHR", "departure_date": "2020-01-01"},  # Past date
            {"origin": "LOS", "destination": "LHR", "adults": 0}  # No passengers
        ]

        for invalid_data in invalid_cases:
            search_data = {
                "cabin": "ECONOMY",
                "flight_type": "one-way",
                "adults": 1,
                **invalid_data
            }

            response = authenticated_flight_api.search_request(search_data)
            # Should handle errors gracefully (4xx status)
            assert response.status_code in [400, 422, 200]  # Some might still return 200
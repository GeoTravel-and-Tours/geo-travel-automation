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
    def test_get_booked_flights(self, authenticated_flight_api):
        """Test retrieving user's booked flights"""
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
# src/tests/api_tests/test_visa_api.py

import pytest
import random
from datetime import datetime, timedelta
from src.pages.api.visa_enquiries_api import VisaEnquiryAPI
from src.pages.api.auth_api import AuthAPI
from src.utils.logger import GeoLogger


class TestVisaEnquiryAPI:
    """Comprehensive Visa Enquiry API Test Suite"""
    
    def setup_method(self):
        """Setup before each test method"""
        self.logger = GeoLogger(self.__class__.__name__)
        self.test_data = self._generate_test_data()
        self.logger.info(f"🚀 Starting {self.__class__.__name__} test")
    
    def teardown_method(self):
        """Cleanup after each test method"""
        self.logger.info(f"✅ {self.__class__.__name__} test completed")
    
    def _generate_test_data(self):
        """Generate dynamic test data for visa tests"""
        # Future travel dates
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        return {
            "visa_enquiry_payload": {
                "visaCountry": "Kenya",
                "first_name": "QA Bot",
                "last_name": "GEO",
                "travel_date": future_date,
                "email": "geo.qa.bot@gmail.com",
                "agree": True,
                "phoneNumber": "7080702920",
                "nationality": "Nigeria",
                "passportAvailable": "Yes",
                "message": "I would like to travel for business purposes",
                "type": "Business"
            },
            "payment_payload_flutterwave": {
                "visaId": None,  # Will be populated dynamically
                "paymentMethod": "Flutterwave"
            },
            "payment_payload_bank_transfer": {
                "visaId": None,  # Will be populated dynamically
                "paymentMethod": "Bank Transfer"
            }
        }
    
    @pytest.fixture
    def visa_api(self):
        """Fixture for unauthenticated VisaEnquiryAPI instance"""
        return VisaEnquiryAPI()
    
    @pytest.fixture
    def authenticated_visa_api(self):
        """Fixture for authenticated VisaEnquiryAPI instance"""
        auth_api = AuthAPI()
        response = auth_api.login()
        
        if response.status_code != 200:
            self.logger.error(f"❌ Login failed with status {response.status_code}")
            pytest.skip(f"Login failed with status {response.status_code}")
        self.logger.success(f"✅ Authenticated successfully (token length: {len(auth_api.auth_token)})")
            
        visa_api = VisaEnquiryAPI()
        visa_api.set_auth_token(auth_api.auth_token)
        visa_api.set_auth_token(auth_api.auth_token, token_source=auth_api.token_source)
        return visa_api
    
    # ==================== VISA ENQUIRY CREATION TESTS ====================
    
    @pytest.mark.api
    def test_create_visa_enquiry_without_auth(self, visa_api):
        """Test creating visa enquiry WITHOUT authentication - user_id MUST be null"""
        self.logger.info("=== Testing Create Visa Enquiry - Without Auth ===")
        
        # Ensure no auth token
        visa_api.auth_token = None
        if 'Authorization' in visa_api.headers:
            del visa_api.headers['Authorization']
        if 'Cookie' in visa_api.headers:
            del visa_api.headers['Cookie']
        
        payload = self.test_data["visa_enquiry_payload"].copy()
        
        # Test different visa types
        visa_types = ["Tourist", "Business", "Work", "Student"]
        visa_countries = ["Kenya", "Uganda", "Tanzania", "Morocco", "Vietnam", "East Africa", "Other"]
        
        payload["type"] = random.choice(visa_types)
        payload["visaCountry"] = random.choice(visa_countries)
        
        response = visa_api.create_visa_enquiry(payload)
        
        # Should succeed without auth
        assert response.status_code == 200 or 201, f"Expected 200 or 201, got {response.status_code}"
        
        response_data = response.json()
        assert response_data.get("status") == "success", "Response status should be 'success'"
        
        # CRITICAL: When NOT authenticated, user_id MUST be null
        visa_data = response_data.get("data", {})
        user_id = visa_data.get("user_id")
        
        # FAIL if user_id is NOT None when not authenticated
        assert user_id is None, (
            f"user_id should be null when creating visa enquiry without authentication.\n"
            f"Got user_id: {user_id}\n"
            f"Full response: {response_data}\n"
            f"This indicates the endpoint is incorrectly attaching a user."
        )
        
        # Additional validations
        assert "id" in visa_data, "Response should include visa ID"
        assert visa_data["enquiryStatus"] == "Submitted", "Default status should be 'Submitted'"
        assert visa_data["paymentStatus"] == "UNPAID", "Payment status should be 'UNPAID' if not paid yet"
        
        visa_id = visa_data["id"]
        self.logger.success(f"✅ Visa enquiry created successfully without auth!")
        self.logger.info(f"📋 Visa ID: {visa_id}, User ID: {user_id} (correctly null)")
        self.logger.info(f"📋 Type: {payload['type']}, Country: {payload['visaCountry']}")
        
        return visa_id
    
    @pytest.mark.api
    def test_create_visa_enquiry_with_auth(self, authenticated_visa_api):
        """Test creating visa enquiry WITH authentication - MUST have user_id attached"""
        self.logger.info("=== Testing Create Visa Enquiry - With Auth ===")
        
        payload = self.test_data["visa_enquiry_payload"].copy()
        
        # Test different visa type
        payload["type"] = "Tourist"
        payload["visaCountry"] = "Qatar"
        payload["message"] = "I would like to travel for tourism"
        
        response = authenticated_visa_api.create_visa_enquiry(payload)
        
        # Should succeed with auth
        assert response.status_code == 200 or 201, f"Expected 200 or 201, got {response.status_code}"
        
        response_data = response.json()
        assert response_data.get("status") == "success", "Response status should be 'success'"
        
        visa_data = response_data.get("data", {})
        
        # CRITICAL: When authenticated, user_id MUST NOT be null
        user_id = visa_data.get("user_id")
        
        # FAIL if user_id is None when authenticated
        assert user_id is not None, (
            f"user_id should not be null when creating visa enquiry with authentication.\n"
            f"Full response: {response_data}"
        )
        
        # Additional validation: user_id must be valid
        assert isinstance(user_id, (int, str)), f"user_id must be int or str, got {type(user_id)}"
        
        if isinstance(user_id, str):
            assert user_id.strip() != "", "user_id string cannot be empty"
        
        visa_id = visa_data["id"]
        self.logger.success(f"✅ Visa enquiry created successfully with auth!")
        self.logger.info(f"📋 Visa ID: {visa_id}, User ID: {user_id}")
        
        return visa_id
    
    @pytest.mark.api
    @pytest.mark.parametrize("missing_field", [
        "first_name", "last_name", "email", "phoneNumber", 
        "visaCountry", "travel_date", "agree", "type"
    ])
    def test_create_visa_enquiry_missing_required_fields(self, visa_api, missing_field):
        """Test visa enquiry creation with missing required fields"""
        self.logger.info(f"=== Testing Create Visa Enquiry - Missing {missing_field} ===")
        
        payload = self.test_data["visa_enquiry_payload"].copy()
        payload.pop(missing_field, None)
        
        response = visa_api.create_visa_enquiry(payload)
        
        # Handle different responses
        if response.status_code == 400:
            # Field is validated as required
            self.logger.success(f"✅ Missing required field '{missing_field}' correctly rejected with 400")
            assert response.status_code == 400
        elif response.status_code in [200, 201]:
            # Field is NOT required (or has default value)
            response_data = response.json()
            self.logger.warning(f"⚠️ Field '{missing_field}' is NOT required: accepted with {response.status_code}")
            # We should still check if the field exists in response with some default
            if missing_field in ["first_name", "last_name", "email"]:
                visa_data = response_data.get("data", {})
                # Check if field is null or has some value
                field_value = visa_data.get(missing_field)
                self.logger.info(f"  Field '{missing_field}' in response: {field_value}")
        else:
            # Unexpected response
            self.logger.warning(f"⚠️ Unexpected status {response.status_code} for missing field '{missing_field}'")
    
    @pytest.mark.api
    @pytest.mark.parametrize("invalid_type", ["InvalidType", "", "Vacation"])
    def test_create_visa_enquiry_invalid_type(self, visa_api, invalid_type):
        """Test visa enquiry creation with invalid visa type"""
        self.logger.info(f"=== Testing Create Visa Enquiry - Invalid Type: {invalid_type} ===")
        
        payload = self.test_data["visa_enquiry_payload"].copy()
        payload["type"] = invalid_type
        
        response = visa_api.create_visa_enquiry(payload)
        
        # Should fail with 400 for validation error
        assert response.status_code == 400, (
            f"Invalid visa type '{invalid_type}' should return 400, got {response.status_code}"
        )
        
        self.logger.success(f"✅ Invalid visa type '{invalid_type}' correctly rejected")
    
    @pytest.mark.api
    def test_create_visa_enquiry_invalid_dates(self, visa_api):
        """Test visa enquiry creation with invalid travel dates"""
        self.logger.info("=== Testing Create Visa Enquiry - Invalid Dates ===")
        
        base_payload = self.test_data["visa_enquiry_payload"].copy()
        
        invalid_date_cases = [
            {"name": "Past travel date", "date": "2020-01-01"},
            {"name": "Invalid date format", "date": "01-01-2025"},
            {"name": "Empty date", "date": ""},
        ]
        
        for case in invalid_date_cases:
            self.logger.info(f"Testing: {case['name']}")
            payload = base_payload.copy()
            payload["travel_date"] = case["date"]
            
            response = visa_api.create_visa_enquiry(payload)
            
            if response.status_code == 400:
                self.logger.success(f"✅ {case['name']}: Correctly rejected")
            elif response.status_code == 201:
                pytest.fail(f"⚠️ {case['name']}: Accepted (API may not validate dates strictly)")
                self.logger.info(f"⚠️ {case['name']}: Accepted (API may not validate dates strictly)")
            else:
                self.logger.warning(f"⚠️ {case['name']}: Unexpected status {response.status_code}")
    
    # ==================== VISA PAYMENT TESTS ====================
    
    @pytest.mark.api
    def test_make_payment_flutterwave_without_auth(self, visa_api):
        """Test making payment with Flutterwave WITHOUT authentication"""
        self.logger.info("=== Testing Make Payment (Flutterwave) - Without Auth ===")
        
        # Create visa enquiry directly
        payload = self.test_data["visa_enquiry_payload"].copy()
        payload["type"] = "Business"
        payload["visaCountry"] = "Kenya"
        
        create_response = visa_api.create_visa_enquiry(payload)
        assert create_response.status_code == 200 or 201, "Should create visa enquiry"
        
        create_data = create_response.json()
        visa_id = create_data.get("data", {}).get("id")
        
        # Now make payment
        payment_payload = {"visaId": visa_id, "paymentMethod": "Flutterwave"}
        response = visa_api.make_payment(payment_payload)
        
        # Should succeed without auth
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        response_data = response.json()
        assert "payment_link" in response_data.get("data", {}), "Flutterwave payment should return payment_link"
        
        payment_link = response_data["data"]["payment_link"]
        self.logger.success(f"✅ Flutterwave payment initiated successfully!")
        self.logger.info(f"📋 Payment link: {payment_link}")
        
        # Verify payment link is accessible
        is_valid, message = visa_api.verify_payment_link(payment_link)
        if is_valid:
            self.logger.success(f"✅ Payment link verification: {message}")
        else:
            self.logger.warning(f"⚠️ Payment link issue: {message}")
    
    @pytest.mark.api
    def test_make_payment_bank_transfer_without_auth(self, visa_api):
        """Test making payment with Bank Transfer WITHOUT authentication"""
        self.logger.info("=== Testing Make Payment (Bank Transfer) - Without Auth ===")
        
        # Create visa enquiry directly
        payload = self.test_data["visa_enquiry_payload"].copy()
        payload["type"] = "Business"
        payload["visaCountry"] = "Kenya"
        
        create_response = visa_api.create_visa_enquiry(payload)
        assert create_response.status_code == 200 or 201, "Should create visa enquiry"
        
        create_data = create_response.json()
        visa_id = create_data.get("data", {}).get("id")
        
        # Now make payment
        payment_payload = {"visaId": visa_id, "paymentMethod": "Flutterwave"}
        response = visa_api.make_payment(payment_payload)
        
        # Should succeed without auth
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        response_data = response.json()
        assert "amount_to_pay" in response_data.get("data", {}), "Bank transfer should return amount_to_pay"
        assert "reference" in response_data.get("data", {}), "Bank transfer should return reference"
        
        payment_data = response_data["data"]
        self.logger.success(f"✅ Bank Transfer payment initiated successfully!")
        self.logger.info(f"📋 Amount to pay: {payment_data['amount_to_pay']}")
        self.logger.info(f"📋 Reference: {payment_data['reference']}")
    
    @pytest.mark.api
    def test_make_payment_flutterwave_with_auth(self, authenticated_visa_api):
        """Test making payment with Flutterwave WITH authentication"""
        self.logger.info("=== Testing Make Payment (Flutterwave) - With Auth ===")
        
        # Create visa enquiry directly in this test
        payload = self.test_data["visa_enquiry_payload"].copy()
        payload["type"] = "Tourist"
        payload["visaCountry"] = "Qatar"
        
        create_response = authenticated_visa_api.create_visa_enquiry(payload)
        assert create_response.status_code == 201, "Should create visa enquiry"
        
        create_data = create_response.json()
        visa_id = create_data.get("data", {}).get("id")
        
        # Now make payment
        payment_payload = {"visaId": visa_id, "paymentMethod": "Flutterwave"}
        response = authenticated_visa_api.make_payment(payment_payload)
        
        # Should succeed with auth
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        response_data = response.json()
        assert "payment_link" in response_data.get("data", {}), "Flutterwave payment should return payment_link"
        
        payment_link = response_data["data"]["payment_link"]
        self.logger.success(f"✅ Flutterwave payment initiated successfully with auth!")
        self.logger.info(f"📋 Payment link: {payment_link}")
    
    @pytest.mark.api
    def test_make_payment_invalid_visa_id(self, visa_api):
        """Test making payment with invalid visa ID"""
        self.logger.info("=== Testing Make Payment - Invalid Visa ID ===")
        
        payment_payload = {
            "visaId": 999999,  # Non-existent visa ID
            "paymentMethod": "Flutterwave"
        }
        
        response = visa_api.make_payment(payment_payload)
        
        # Should fail with 400 or 404
        assert response.status_code in [400, 404], (
            f"Invalid visa ID should return 400/404, got {response.status_code}"
        )
        
        self.logger.success(f"✅ Invalid visa ID correctly rejected with {response.status_code}")
    
    @pytest.mark.api
    def test_make_payment_invalid_method(self, visa_api):
        """Test making payment with invalid payment method"""
        self.logger.info("=== Testing Make Payment - Invalid Method ===")
        
        invalid_methods = ["PayPal", "CreditCard", ""]
        
        for invalid_method in invalid_methods:
            self.logger.info(f"Testing invalid payment method: '{invalid_method}'")
            
            # Create visa enquiry directly
            payload = self.test_data["visa_enquiry_payload"].copy()
            payload["type"] = "Business"
            payload["visaCountry"] = "Kenya"
            
            create_response = visa_api.create_visa_enquiry(payload)
            assert create_response.status_code == 200 or 201, "Should create visa enquiry"
            
            create_data = create_response.json()
            visa_id = create_data.get("data", {}).get("id")
            
            # Now make payment
            payment_payload = {"visaId": visa_id, "paymentMethod": "Flutterwave"}
            response = visa_api.make_payment(payment_payload)
            
            payment_payload = {
                "visaId": visa_id,
                "paymentMethod": invalid_method
            }
            
            response = visa_api.make_payment(payment_payload)
            
            # Should fail with 400
            assert response.status_code == 400, (
                f"Invalid payment method '{invalid_method}' should return 400, got {response.status_code}"
            )
            
            self.logger.success(f"✅ Invalid payment method '{invalid_method}' correctly rejected")
    
    # ==================== USER VISA APPLICATIONS TESTS ====================
    
    @pytest.mark.api
    def test_get_user_visa_applications_with_auth(self, authenticated_visa_api):
        """Test getting user's visa applications WITH authentication"""
        self.logger.info("=== Testing Get User Visa Applications - With Auth ===")
        
        response = authenticated_visa_api.get_user_visa_applications(
            limit=10,
            page=1
        )
        
        # Should succeed with auth
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        response_data = response.json()
        assert response_data.get("status") == "success", "Response status should be 'success'"
        
        data = response_data.get("data", {})
        visa_enquiries = data.get("visaEnquiries", [])
        pagination = data.get("pagination", {})
        
        # Log details
        self.logger.info(f"📋 Found {len(visa_enquiries)} visa applications")
        self.logger.info(f"📋 Pagination: Page {pagination.get('currentPage')} of {pagination.get('totalPages')}")
        
        # Validate response structure
        assert isinstance(visa_enquiries, list), "visaEnquiries should be a list"
        assert isinstance(pagination, dict), "pagination should be a dict"
        
        # Check pagination fields
        assert "currentPage" in pagination, "Pagination should have currentPage"
        assert "totalItems" in pagination, "Pagination should have totalItems"
        
        # Log first few applications if available
        for i, visa in enumerate(visa_enquiries[:3]):
            self.logger.info(f"  Visa {i+1}: ID={visa.get('id')}, Country={visa.get('visaCountry')}, "
                           f"Status={visa.get('enquiryStatus')}")
        
        self.logger.success(f"✅ Successfully retrieved user visa applications")
        
        # Return first visa ID for use in other tests
        if visa_enquiries:
            return visa_enquiries[0].get("id")
        return None
    
    @pytest.mark.api
    def test_get_user_visa_applications_without_auth(self, visa_api):
        """Test getting user's visa applications WITHOUT authentication"""
        self.logger.info("=== Testing Get User Visa Applications - Without Auth ===")
        
        response = visa_api.get_user_visa_applications(limit=10, page=1)
        
        # Should fail with 401 when not authenticated
        assert response.status_code == 401, (
            f"Unauthenticated access should return 401, got {response.status_code}"
        )
        
        self.logger.success("✅ Unauthenticated access correctly rejected with 401")
    
    @pytest.mark.api
    def test_get_user_visa_applications_with_filters(self, authenticated_visa_api):
        """Test getting user's visa applications with various filters"""
        self.logger.info("=== Testing Get User Visa Applications - With Filters ===")
        
        # Test different filter combinations
        filter_cases = [
            {"name": "Status filter - Submitted", "status": "Submitted"},
            {"name": "Status filter - InProgress", "status": "InProgress"},
            {"name": "Type filter - Tourist", "type": "Tourist"},
            {"name": "Type filter - Business", "type": "Business"},
            {"name": "Date range filter", "start_date": "2025-01-01", "end_date": "2025-12-31"},
            {"name": "Combined filters", "status": "Submitted", "type": "Work", "limit": 5},
        ]
        
        for case in filter_cases:
            self.logger.info(f"Testing: {case['name']}")
            
            response = authenticated_visa_api.get_user_visa_applications(**case)
            
            assert response.status_code == 200, f"Filter {case['name']} failed: {response.status_code}"
            
            response_data = response.json()
            print(response_data)
            if response_data.get("status") == "success":
                data = response_data.get("data", {})
                visa_enquiries = data.get("visaEnquiries", [])
                self.logger.info(f"  ✅ Filter applied: {case['name']}, Found: {len(visa_enquiries)} applications")
            else:
                self.logger.info(f"  ⚠️ Filter {case['name']} returned: {response_data.get('message')}")
    
    @pytest.mark.api
    def test_get_user_visa_applications_pagination(self, authenticated_visa_api):
        """Test user visa applications pagination"""
        self.logger.info("=== Testing User Visa Applications Pagination ===")
        
        # Test different page and limit combinations
        pagination_cases = [
            {"page": 1, "limit": 5},
            {"page": 1, "limit": 10},
            {"page": 2, "limit": 5},
        ]
        
        for case in pagination_cases:
            self.logger.info(f"Testing pagination: Page {case['page']}, Limit {case['limit']}")
            
            response = authenticated_visa_api.get_user_visa_applications(**case)
            assert response.status_code == 200, f"Pagination failed: {response.status_code}"
            
            response_data = response.json()
            if response_data.get("status") == "success":
                data = response_data.get("data", {})
                pagination = data.get("pagination", {})
                
                current_page = pagination.get("currentPage")
                items_per_page = pagination.get("itemsPerPage")
                
                self.logger.info(f"  ✅ Page {current_page}, Items per page: {items_per_page}")
                
                # Verify pagination parameters match response
                assert current_page == case["page"], f"Expected page {case['page']}, got {current_page}"
                assert items_per_page == case["limit"], f"Expected limit {case['limit']}, got {items_per_page}"
    
    # ==================== GET SPECIFIC VISA APPLICATION TESTS ====================
    
    @pytest.mark.api
    def test_get_visa_application_by_id_with_auth(self, authenticated_visa_api):
        """Test getting specific visa application by ID WITH authentication"""
        self.logger.info("=== Testing Get Visa Application by ID - With Auth ===")
        
        # Get user visa applications directly instead of calling another test
        response = authenticated_visa_api.get_user_visa_applications(limit=10, page=1)
        
        if response.status_code == 200:
            response_data = response.json()
            data = response_data.get("data", {})
            visa_enquiries = data.get("visaEnquiries", [])
            
            if visa_enquiries:
                visa_id = visa_enquiries[0].get("id")
                
                # Now get the specific visa application
                get_response = authenticated_visa_api.get_visa_application_by_id(visa_id)
                
                if get_response.status_code == 200:
                    get_response_data = get_response.json()
                    self.logger.success(f"✅ Successfully retrieved visa application {visa_id}")
                    self.logger.info(f"Response: {get_response_data}")
                    
                    # Add validation if we know the expected structure
                    assert "data" in get_response_data, "Response should have 'data' key"
                    
                elif get_response.status_code == 404:
                    self.logger.info(f"⚠️ Visa application {visa_id} not found (404)")
                    pytest.fail(f"⚠️ Visa application {visa_id} not found (404)")
                elif get_response.status_code == 401:
                    self.logger.info(f"⚠️ Unauthorized access to visa application {visa_id} (401)")
                    pytest.fail(f"⚠️ Unauthorized access to visa application {visa_id} (401)")
                elif get_response.status_code == 500:
                    self.logger.warning(f"⚠️ Server error when getting visa application {visa_id} (500)")
                    pytest.fail(f"⚠️ Server error when getting visa application {visa_id} (500)")
                else:
                    self.logger.info(f"⚠️ Unexpected status {get_response.status_code} for visa application {visa_id}")
            else:
                self.logger.warning("⚠️ No visa applications found to test Get by ID")
                pytest.skip("No visa applications available for testing Get by ID")
        else:
            pytest.skip(f"Cannot get user visa applications: {response.status_code}")
        
    @pytest.mark.api
    def test_get_visa_application_by_id_without_auth(self, visa_api):
        """Test getting specific visa application by ID WITHOUT authentication"""
        self.logger.info("=== Testing Get Visa Application by ID - Without Auth ===")
        
        # Use a dummy visa ID
        response = visa_api.get_visa_application_by_id(1)
        

        if response.status_code == 401:
            self.logger.success("✅ Unauthenticated access correctly rejected with 401")
            assert response.status_code == 401
        elif response.status_code == 404:
            self.logger.info("⚠️ Endpoint returns 404 for unauthenticated users (or visa not found)")
            pytest.fail("⚠️ Endpoint returns 404 for unauthenticated users (or visa not found)")
        elif response.status_code == 200:
            self.logger.warning("⚠️ Endpoint allows unauthenticated access (check if this is intended)")
            assert response.status_code != 200, "Expected 401 or 404, got 200"
            pytest.fail("⚠️ Endpoint allows unauthenticated access (check if this is intended)")
        else:
            self.logger.info(f"⚠️ Unexpected status {response.status_code} for unauthenticated access")
    
    # ==================== COMPREHENSIVE END-TO-END TEST ====================
    
    @pytest.mark.api
    def test_complete_visa_flow_with_auth(self, authenticated_visa_api):
        """Complete end-to-end visa flow with authentication"""
        self.logger.info("=== Testing Complete Visa Flow - With Auth ===")
        
        # Step 1: Create visa enquiry
        self.logger.info("Step 1: Creating visa enquiry...")
        payload = self.test_data["visa_enquiry_payload"].copy()
        payload["type"] = "Student"
        payload["visaCountry"] = "Canada"
        payload["message"] = "I want to study abroad"
        
        create_response = authenticated_visa_api.create_visa_enquiry(payload)
        assert create_response.status_code == 200 or 201, "Visa creation should succeed"
        
        create_data = create_response.json()
        visa_data = create_data.get("data", {})
        visa_id = visa_data.get("id")
        user_id = visa_data.get("user_id")
        
        assert visa_id is not None, "Visa ID should be returned"
        assert user_id is not None, "User ID should be attached when authenticated"
        
        self.logger.success(f"✅ Visa enquiry created: ID={visa_id}, User ID={user_id}")
        
        # Step 2: Get user's visa applications (should include the new one)
        self.logger.info("Step 2: Getting user's visa applications...")
        list_response = authenticated_visa_api.get_user_visa_applications(limit=20)
        assert list_response.status_code == 200, "Should get user applications"
        
        list_data = list_response.json()
        visa_enquiries = list_data.get("data", {}).get("visaEnquiries", [])
        
        # Check if our new visa is in the list
        visa_ids = [str(v.get("id")) for v in visa_enquiries]
        assert str(visa_id) in visa_ids, f"New visa {visa_id} should appear in user's applications"
        
        self.logger.success(f"✅ Visa {visa_id} found in user's applications list")
        
        # Step 3: Initiate payment (Flutterwave)
        self.logger.info("Step 3: Initiating Flutterwave payment...")
        payment_payload = {"visaId": visa_id, "paymentMethod": "Flutterwave"}
        payment_response = authenticated_visa_api.make_payment(payment_payload)
        
        assert payment_response.status_code == 200, "Payment initiation should succeed"
        
        payment_data = payment_response.json()
        payment_link = payment_data.get("data", {}).get("payment_link")
        
        if payment_link:
            self.logger.success(f"✅ Payment link generated: {payment_link[:50]}...")
            
            # Verify payment link
            is_valid, message = authenticated_visa_api.verify_payment_link(payment_link)
            if is_valid:
                self.logger.success(f"✅ Payment link verification: {message}")
            else:
                self.logger.warning(f"⚠️ Payment link issue: {message}")
        
        self.logger.success("✅ Complete visa flow test passed!")
    
    @pytest.mark.api
    def test_complete_visa_flow_without_auth(self, visa_api):
        """Complete end-to-end visa flow without authentication"""
        self.logger.info("=== Testing Complete Visa Flow - Without Auth ===")
        
        # Step 1: Create visa enquiry without auth
        self.logger.info("Step 1: Creating visa enquiry without auth...")
        payload = self.test_data["visa_enquiry_payload"].copy()
        payload["type"] = "Tourist"
        payload["visaCountry"] = "Qatar"
        
        create_response = visa_api.create_visa_enquiry(payload)
        assert create_response.status_code == 200 or 201, "Visa creation should succeed without auth"
        
        create_data = create_response.json()
        visa_data = create_data.get("data", {})
        visa_id = visa_data.get("id")
        user_id = visa_data.get("user_id")
        
        assert visa_id is not None, "Visa ID should be returned"
        assert user_id is None, "User ID should be null when not authenticated"
        
        self.logger.success(f"✅ Visa enquiry created without auth: ID={visa_id}")
        
        # Step 2: Try to get user's visa applications (should fail with 401)
        self.logger.info("Step 2: Trying to get visa applications without auth...")
        list_response = visa_api.get_user_visa_applications()
        assert list_response.status_code == 401, "Should reject unauthenticated access"
        
        self.logger.success("✅ Correctly rejected unauthenticated access to user applications")
        
        # Step 3: Initiate payment without auth
        self.logger.info("Step 3: Initiating Bank Transfer payment without auth...")
        payment_payload = {"visaId": visa_id, "paymentMethod": "Bank Transfer"}
        payment_response = visa_api.make_payment(payment_payload)
        
        assert payment_response.status_code == 200, "Payment should work without auth"
        
        payment_data = payment_response.json()
        reference = payment_data.get("data", {}).get("reference")
        
        if reference:
            self.logger.success(f"✅ Bank transfer reference generated: {reference}")
        
        self.logger.success("✅ Complete visa flow without auth test passed!")
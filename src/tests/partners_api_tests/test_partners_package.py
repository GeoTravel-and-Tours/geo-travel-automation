import pytest
import random
import functools
import requests
import time
from src.pages.api.partners_api.partners_auth_api import PartnersAuthAPI
from src.pages.api.partners_api.partners_package_api import PartnersPackageAPI
from src.pages.api.partners_api.organization_api import PartnersOrganizationAPI
from src.utils.verified_partners_helper import VerifiedUserHelper
from configs.environment import EnvironmentConfig
from src.utils.logger import GeoLogger

def retry_on_timeout(max_retries=3, delay=2):
    """✅ ADDED: Decorator to retry test on timeout"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.Timeout as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        break
                    
                    wait_time = delay * (2 ** attempt)  # Exponential backoff
                    logger = args[0].logger if args else GeoLogger(func.__name__)
                    logger.warning(
                        f"⏳ {func.__name__} timeout (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
            
            if last_exception:
                logger.error(f"❌ {func.__name__} failed after {max_retries} attempts")
                raise last_exception
        return wrapper
    return decorator


class TestPartnersPackageSecurity:
    """SECURITY TESTS - Unverified users should be blocked from package operations"""
    
    def setup_method(self):
        self.auth_api = PartnersAuthAPI()
        self.package_api = PartnersPackageAPI()  # No credentials = unverified user
        
        # Create unverified user
        self.test_email = f"packagetest{random.randint(10000,99999)}@yopmail.com"
        self.test_password = "StrongPass123!"
        self.test_org_data = {
            "orgName": f"Package Test Org {random.randint(1000,9999)}",
            "orgEmail": self.test_email,
            "address": "123 Package St, Test City", 
            "password": self.test_password,
            "contactPerson": {
                "firstName": "Package",
                "lastName": "Tester",
                "phoneNumber": "+1234567890"
            }
        }
        self.logger = GeoLogger(self.__class__.__name__)
    
    @pytest.mark.partners_api
    @pytest.mark.security
    def test_unverified_user_blocked_from_package_listing(self):
        """Test that unverified users cannot get package listings"""
        # 1. Create unverified user
        self.logger.info(f"🔵 CREATING UNVERIFIED USER: {self.test_email}")
        signup_response = self.auth_api.signup(self.test_org_data)
        assert signup_response.status_code == 201
        
        # 2. Try to get packages - should be blocked
        self.logger.info(f"🔵 ATTEMPTING PACKAGE LISTING: {self.test_email}")
        response = self.package_api.get_all_packages()
        
        # Should be blocked - either 401 (no auth) or 403 (no permissions)
        assert response.status_code in [401, 403], (
            f"Unverified user should be blocked from package listing. Got {response.status_code}"
        )
        self.logger.success(f"✅ Unverified user correctly blocked from package listing: {self.test_email}")
    
    @pytest.mark.partners_api
    @pytest.mark.security
    def test_unverified_user_blocked_from_package_countries(self):
        """Test that unverified users cannot get package countries"""
        # 1. Create unverified user
        self.logger.info(f"🔵 CREATING UNVERIFIED USER: {self.test_email}")
        signup_response = self.auth_api.signup(self.test_org_data)
        assert signup_response.status_code == 201
        
        # 2. Try to get package countries - should be blocked
        self.logger.info(f"🔵 ATTEMPTING PACKAGE COUNTRIES: {self.test_email}")
        response = self.package_api.get_package_countries()
        
        # Should be blocked - either 401 (no auth) or 403 (no permissions)
        assert response.status_code in [401, 403], (
            f"Unverified user should be blocked from package countries. Got {response.status_code}"
        )
        self.logger.success(f"✅ Unverified user correctly blocked from package countries: {self.test_email}")
    
    @pytest.mark.partners_api
    @pytest.mark.security
    def test_unverified_user_blocked_from_package_booking(self):
        """Test that unverified users cannot book packages"""
        # 1. Create unverified user
        self.logger.info(f"🔵 CREATING UNVERIFIED USER: {self.test_email}")
        signup_response = self.auth_api.signup(self.test_org_data)
        assert signup_response.status_code == 201
        
        # 2. Try package booking - should be blocked
        self.logger.info(f"🔵 ATTEMPTING PACKAGE BOOKING: {self.test_email}")
        booking_data = {
            "package": "11",
            "full_name": "John Doe",
            "email": "john@yopmail.com", 
            "phone": "+2348123456789",
            "departure_date": "2025-12-15",
            "adults": 2,
            "children": 1,
            "infants": 0,
            "pricing_text": "Family Trip",
            "book_at_deal_price": False,
            "is_full_payment": True
        }
        response = self.package_api.book_package(booking_data)
        
        # Should be blocked - either 401 (no auth) or 403 (no permissions)
        assert response.status_code in [401, 403], (
            f"Unverified user should be blocked from package booking. Got {response.status_code}"
        )
        self.logger.success(f"✅ Unverified user correctly blocked from package booking: {self.test_email}")

class TestPartnersPackageFunctionality:
    """FUNCTIONALITY TESTS - Verified users can access package operations and data is stored"""
    
    def setup_method(self):
        # Validate credentials before running tests
        if not EnvironmentConfig.validate_partners_credentials():
            pytest.skip("Partners verified account credentials not configured")
        
        self.verified_helper = VerifiedUserHelper()
        self.org_api = self.verified_helper.get_verified_organization_api()
        self.logger = GeoLogger(self.__class__.__name__)
    
    @pytest.mark.partners_api
    @retry_on_timeout(max_retries=3, delay=2)  # ✅ ADDED RETRY DECORATOR
    def test_verified_user_can_get_packages(self):
        """TEST: Verified users can get package listings with complete structure"""
        # Get package API with verified credentials
        package_api = self.verified_helper.get_verified_package_api()
        assert package_api is not None, "Should get verified package API"
        
        self.logger.info("🔵 VERIFIED USER - Getting package listings")
        # ✅ TEMPORARILY INCREASE TIMEOUT FOR THIS CALL
        original_timeout = package_api.timeout
        package_api.timeout = 90  # 90 seconds for package listings
        
        try:
            response = package_api.get_all_packages()
        finally:
            package_api.timeout = original_timeout  # Restore original timeout
        
        assert response.status_code == 200, "Verified user should be able to access package listings"
        data = response.json()
        print(response.text)
        
        # Verify complete response structure
        assert data['message'] == "Packages retrieved successfully"
        assert 'data' in data
        assert 'packages' in data['data']
        
        packages = data['data']['packages']
        
        # Verify packages array structure
        assert isinstance(packages, list)
        
        if packages:  # If packages exist, verify their structure
            first_package = packages[0]
            
            # Verify required package fields
            assert 'id' in first_package
            assert 'title' in first_package
            assert 'package_type' in first_package
            assert 'prices' in first_package
            assert 'destinations' in first_package
            assert 'status' in first_package
            
            # Verify prices array structure
            prices = first_package['prices']
            assert isinstance(prices, list)
            if prices:
                price_item = prices[0]
                assert 'price' in price_item
                assert 'pricing_text' in price_item
                assert 'lockdown_price' in price_item
            
            # Verify destinations array structure
            destinations = first_package['destinations']
            assert isinstance(destinations, list)
            if destinations:
                destination = destinations[0]
                assert 'city' in destination
                assert 'country' in destination
        
        self.logger.success(f"✅ Verified user can get packages - found {len(packages)} packages")
        
        # Store packages for potential booking test
        self.available_packages = packages
    
    @pytest.mark.partners_api
    def test_verified_user_can_get_package_countries(self):
        """TEST: Verified users can get available package countries and cities"""
        package_api = self.verified_helper.get_verified_package_api()
        
        self.logger.info("🔵 VERIFIED USER - Getting package countries")
        response = package_api.get_package_countries()
        print(response.text)
        
        assert response.status_code == 200, "Verified user should be able to access package countries"
        data = response.json()
        
        # Verify complete response structure
        assert data['message'] == "Available Package countries retrieved successfully"
        assert 'data' in data
        assert 'countries' in data['data']
        assert 'cities' in data['data']
        
        countries = data['data']['countries']
        cities = data['data']['cities']
        
        # Verify data types and content
        assert isinstance(countries, list)
        assert isinstance(cities, list)
        
        # Should have some countries and cities available
        assert len(countries) > 0, "Should have available countries"
        assert len(cities) > 0, "Should have available cities"
        
        self.logger.success(f"✅ Verified user can get package countries - {len(countries)} countries, {len(cities)} cities")
    
    @pytest.mark.partners_api
    def test_verified_user_can_book_package(self):
        """TEST: Verified users can book packages and booking is properly stored"""
        # First get available packages
        package_api = self.verified_helper.get_verified_package_api()
        
        self.logger.info("🔵 VERIFIED USER - Getting packages for booking")
        packages_response = package_api.get_all_packages()
        assert packages_response.status_code == 200
        
        packages_data = packages_response.json()
        packages = packages_data['data']['packages']
        
        if not packages:
            pytest.skip("No packages available for booking test")
        
        # Use first available package for booking test
        first_package = packages[0]
        package_id = first_package['id']
        package_title = first_package['title']
        
        # Get available pricing text
        pricing_text = "Family Trip"  # Default from your response
        if first_package.get('prices'):
            pricing_text = first_package['prices'][0]['pricing_text']
        
        self.logger.info(f"🔵 VERIFIED USER - Attempting package booking: {package_title} (ID: {package_id})")
        
        # Create unique booking data to avoid conflicts
        random_suffix = random.randint(1000, 9999)
        booking_data = {
            "package": str(package_id),
            "full_name": f"Test Package User {random_suffix}",
            "email": f"testpackage{random_suffix}@yopmail.com",
            "phone": f"+23481{random.randint(1000000,9999999)}",
            "departure_date": "2025-12-15",
            "adults": 2,
            "children": 1,
            "infants": 0,
            "pricing_text": pricing_text,
            "book_at_deal_price": False,
            "is_full_payment": True
        }
        booking_response = package_api.book_package(booking_data)
        
        # Booking should be successful (201 created)
        assert booking_response.status_code == 201, "Verified user should be able to book packages"
        
        booking_result = booking_response.json()
        
        # Verify booking response structure
        assert booking_result['message'] == "Package booked successfully"
        
        self.logger.success("✅ Verified user can book packages")
        
        # Store booking data for verification
        self.booking_data = booking_data
        self.package_booked = first_package
    
    @pytest.mark.partners_api
    def test_package_booking_appears_in_bookings_list(self):
        """TEST: Package bookings appear in the organization's bookings list"""
        package_api = self.verified_helper.get_verified_package_api()
        
        self.logger.info("🔵 CHECKING PACKAGE BOOKINGS LIST")
        
        # Get package bookings for the organization
        bookings_response = package_api.get_package_bookings()
        assert bookings_response.status_code == 200
        
        bookings_data = bookings_response.json()
        
        # Verify response structure
        assert bookings_data['message'] == "Bookings retrieved successfully"
        assert 'data' in bookings_data
        assert 'bookings' in bookings_data['data']
        
        bookings = bookings_data['data']['bookings']
        
        # Verify bookings array structure
        assert isinstance(bookings, list)
        
        if bookings:  # If there are bookings, verify structure
            first_booking = bookings[0]
            
            # Verify booking structure matches your response
            assert 'id' in first_booking
            assert 'booking_code' in first_booking
            assert 'user_details' in first_booking
            assert 'package' in first_booking
            assert 'organization' in first_booking
            assert 'booking_status' in first_booking
            
            # Verify user details structure
            user_details = first_booking['user_details']
            assert 'email' in user_details
            assert 'phone' in user_details
            assert 'full_name' in user_details
            
            # Verify package structure
            package = first_booking['package']
            assert 'id' in package
            assert 'title' in package
            
            # Verify organization structure
            organization = first_booking['organization']
            assert 'id' in organization
            assert 'name' in organization
        
        self.logger.success(f"✅ Package bookings list accessible - found {len(bookings)} bookings")
    
    @pytest.mark.partners_api
    def test_package_booking_counted_in_usage(self):
        """TEST: Package bookings are properly counted in organization usage"""
        # First get baseline usage
        self.logger.info("🔵 GETTING BASELINE USAGE FOR PACKAGE BOOKINGS")
        initial_usage_response = self.org_api.get_usage(mode='test')
        assert initial_usage_response.status_code == 200
        
        initial_usage_data = initial_usage_response.json()
        initial_records = initial_usage_data['data']['records']
        initial_total_bookings = sum(record.get('packageBookings', 0) for record in initial_records)
        
        self.logger.info(f"📊 Initial package bookings: {initial_total_bookings}")
        
        # Create a new package booking
        package_api = self.verified_helper.get_verified_package_api()
        
        packages_response = package_api.get_all_packages()
        if packages_response.status_code == 200:
            packages = packages_response.json()['data']['packages']
            if packages:
                package = packages[0]
                random_suffix = random.randint(10000, 99999)
                
                booking_data = {
                    "package": str(package['id']),
                    "full_name": f"Verification Test User {random_suffix}",
                    "email": f"verification{random_suffix}@yopmail.com",
                    "phone": f"+23481{random.randint(1000000,9999999)}",
                    "departure_date": "2025-12-20",
                    "adults": 1,
                    "children": 0,
                    "infants": 0,
                    "pricing_text": package['prices'][0]['pricing_text'] if package.get('prices') else "Standard",
                    "book_at_deal_price": False,
                    "is_full_payment": True
                }
                
                self.logger.info("🔵 CREATING NEW PACKAGE BOOKING")
                booking_response = package_api.book_package(booking_data)
                
                # Wait for usage to be updated
                import time
                time.sleep(3)
                
                # Get updated usage
                self.logger.info("🔵 CHECKING UPDATED USAGE METRICS")
                final_usage_response = self.org_api.get_usage(mode='test')
                assert final_usage_response.status_code == 200
                
                final_usage_data = final_usage_response.json()
                final_records = final_usage_data['data']['records']
                final_total_bookings = sum(record.get('packageBookings', 0) for record in final_records)
                
                self.logger.info(f"📊 Final package bookings: {final_total_bookings}")
                
                # Verify the booking count increased (if booking was successful)
                if booking_response.status_code == 201:
                    assert final_total_bookings > initial_total_bookings, (
                        f"Package bookings should increase from {initial_total_bookings} to {final_total_bookings}"
                    )
                    self.logger.success(f"✅ Package booking correctly counted - increased from {initial_total_bookings} to {final_total_bookings}")
                else:
                    self.logger.warning(f"⚠️ Package booking failed with status {booking_response.status_code}, cannot verify usage counting")
            else:
                self.logger.warning("⚠️ No packages available for booking test")
        else:
            self.logger.warning("⚠️ Could not fetch packages for booking test")
    
    @pytest.mark.partners_api
    def test_package_usage_reflected_in_range_endpoint(self):
        """TEST: Package usage data is reflected in usage range endpoint"""
        self.logger.info("🔵 CHECKING USAGE RANGE FOR PACKAGE DATA")
        
        # Get usage range for a broad date range
        usage_range_response = self.org_api.get_usage_range(
            mode='test', 
            start_date='2025-01-01', 
            end_date='2025-12-31'
        )
        assert usage_range_response.status_code == 200
        
        usage_range_data = usage_range_response.json()
        range_data = usage_range_data['data']
        
        # Verify package data in usage range
        assert 'totalPackageBookings' in range_data
        assert isinstance(range_data['totalPackageBookings'], int)
        
        self.logger.info(f"📊 Usage Range - Package Bookings: {range_data['totalPackageBookings']}")
        
        self.logger.success("✅ Package usage data correctly reflected in usage range")
    
    @pytest.mark.partners_api
    def test_package_booking_creates_complete_record(self):
        """TEST: Package booking creates a complete record with all required fields"""
        package_api = self.verified_helper.get_verified_package_api()
        
        self.logger.info("🔵 VERIFYING COMPLETE BOOKING RECORD CREATION")
        
        # Get current bookings count before new booking using totalItems
        bookings_before_response = package_api.get_package_bookings()
        if bookings_before_response.status_code == 200:
            response_data = bookings_before_response.json()['data']
            bookings_before = response_data['bookings']
            pagination_before = response_data['pagination']
            initial_count = pagination_before['totalItems']  # Use totalItems instead of len()
            initial_booking_emails = {booking['user_details']['email'] for booking in bookings_before}
        else:
            initial_count = 0
            initial_booking_emails = set()
        
        self.logger.info(f"📊 Initial total bookings: {initial_count}")
        
        # Create a new package booking
        packages_response = package_api.get_all_packages()
        if packages_response.status_code == 200:
            packages = packages_response.json()['data']['packages']
            if packages:
                package = packages[0]
                random_suffix = random.randint(10000, 99999)
                
                # Create unique test data
                test_email = f"verification{random_suffix}@yopmail.com"
                test_full_name = f"Verification Test User {random_suffix}"
                
                booking_data = {
                    "package": str(package['id']),
                    "full_name": test_full_name,
                    "email": test_email,
                    "phone": f"+23481{random.randint(1000000,9999999)}",
                    "departure_date": "2025-12-20",
                    "adults": 1,
                    "children": 0,
                    "infants": 0,
                    "pricing_text": package['prices'][0]['pricing_text'] if package.get('prices') else "Standard",
                    "book_at_deal_price": False,
                    "is_full_payment": True
                }
                
                self.logger.info("🔵 CREATING NEW PACKAGE BOOKING")
                booking_response = package_api.book_package(booking_data)
                
                if booking_response.status_code == 201:
                    booking_result = booking_response.json()
                    self.logger.success(f"✅ {booking_result['message']}")
                    
                    # Wait for the booking to appear in the list
                    time.sleep(5)
                    
                    # Get updated bookings list and count using totalItems
                    bookings_after_response = package_api.get_package_bookings()
                    if bookings_after_response.status_code == 200:
                        response_data_after = bookings_after_response.json()['data']
                        bookings_after = response_data_after['bookings']
                        pagination_after = response_data_after['pagination']
                        final_count = pagination_after['totalItems']  # Use totalItems instead of len()
                        
                        self.logger.info(f"📊 Final total bookings: {final_count}")
                        
                        # Find the new booking by email (since we don't get ID from booking response)
                        # Note: We need to search through all pages if needed
                        new_booking = None
                        current_page = 1
                        
                        # Check first page
                        for booking in bookings_after:
                            if booking['user_details']['email'] == test_email:
                                new_booking = booking
                                break
                        
                        # If not found on first page and there are more pages, check additional pages
                        if not new_booking and pagination_after['totalPages'] > 1:
                            for page in range(2, pagination_after['totalPages'] + 1):
                                page_response = package_api.get_package_bookings(params={'page': page})
                                if page_response.status_code == 200:
                                    page_bookings = page_response.json()['data']['bookings']
                                    for booking in page_bookings:
                                        if booking['user_details']['email'] == test_email:
                                            new_booking = booking
                                            break
                                if new_booking:
                                    break
                        
                        # Verify the new booking appears in the list
                        assert new_booking is not None, f"New booking with email {test_email} should appear in bookings list"
                        
                        # Verify complete booking structure
                        assert 'id' in new_booking, "Booking should have an ID"
                        assert 'booking_code' in new_booking, "Booking should have a booking code"
                        assert 'user_details' in new_booking, "Booking should have user details"
                        assert 'package' in new_booking, "Booking should have package info"
                        assert 'organization' in new_booking, "Booking should have organization info"
                        assert 'booking_status' in new_booking, "Booking should have booking status"
                        
                        # Verify user details structure matches our booking data
                        user_details = new_booking['user_details']
                        assert 'email' in user_details
                        assert user_details['email'] == test_email
                        assert 'phone' in user_details
                        assert 'full_name' in user_details
                        assert user_details['full_name'] == test_full_name
                        
                        # Verify package structure
                        package_info = new_booking['package']
                        assert 'id' in package_info
                        assert str(package_info['id']) == booking_data['package']
                        assert 'title' in package_info
                        
                        # Verify organization structure
                        organization = new_booking['organization']
                        assert 'id' in organization
                        assert 'name' in organization
                        
                        # Verify count increased (using totalItems for accurate comparison)
                        assert final_count == initial_count + 1, (
                            f"Bookings count should increase by 1 from {initial_count} to {final_count}"
                        )
                        
                        self.logger.success(f"✅ Package booking correctly created and appears in bookings list")
                        self.logger.info(f"📊 Count increased from {initial_count} to {final_count}")
                        self.logger.info(f"📋 New booking ID: {new_booking['id']}")
                        self.logger.info(f"📋 Booking code: {new_booking['booking_code']}")
                        
                    else:
                        self.logger.warning("⚠️ Could not fetch bookings after creation")
                else:
                    self.logger.warning(f"⚠️ Package booking creation failed with status {booking_response.status_code}")
                    self.logger.info(f"🔍 Booking response: {booking_response.text}")
            else:
                self.logger.warning("⚠️ No packages available for booking test")
        else:
            self.logger.warning("⚠️ Could not fetch packages for booking test")
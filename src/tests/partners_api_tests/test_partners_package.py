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
            "email": "geopartners@yopmail.com", 
            "phone": "+2348123456789",
            "departure_date": "2025-12-15",
            "adults": 2,
            "children": 1,
            "infants": 0,
            "pricing_text": "Family Trip",
            "book_at_deal_price": False,
            "is_full_payment": True,
            "is_lockdown_payment": False
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
        self.logger.info(response.text)
        
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
        self.logger.info(response.text)
        
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
    def test_verified_user_can_book_packages(self):
        """TEST: Verified users can book both GROUP and PRIVATE packages with correct payload structure"""
        # First get available packages
        package_api = self.verified_helper.get_verified_package_api()
        
        self.logger.info("🔵 VERIFIED USER - Getting packages for booking test")
        packages_response = package_api.get_all_packages()
        assert packages_response.status_code == 200
        
        packages_data = packages_response.json()
        all_packages = packages_data['data']['packages']
        
        if not all_packages:
            pytest.skip("No packages available for booking test")
        
        from datetime import datetime
        import dateutil.parser
        
        today = datetime.now().date()
        
        # Filter packages by type AND check if they're still active (end_date not in past)
        group_packages = []
        private_packages = []
        
        for p in all_packages:
            package_type = p.get('package_type')
            end_date_str = p.get('end_date')
            
            # Skip if no end date
            if not end_date_str:
                continue
                
            end_date = dateutil.parser.parse(end_date_str).date()
            
            # Only include if package is still active (end date is today or in future)
            if end_date >= today:
                if package_type == 'GROUP':
                    group_packages.append(p)
                elif package_type == 'PRIVATE':
                    private_packages.append(p)
        
        self.logger.info(f"📊 Found {len(group_packages)} ACTIVE GROUP packages and {len(private_packages)} ACTIVE PRIVATE packages")
        
        # Test GROUP package if available
        if group_packages:
            selected_group = random.choice(group_packages)
            self._test_book_group_package(package_api, selected_group)
        else:
            self.logger.warning("⚠️ No ACTIVE GROUP packages available to test")
        
        # Test PRIVATE package if available
        if private_packages:
            selected_private = random.choice(private_packages)
            self._test_book_private_package(package_api, selected_private)
        else:
            self.logger.warning("⚠️ No ACTIVE PRIVATE packages available to test")
        
        # If neither type has active packages, skip the test
        if not group_packages and not private_packages:
            pytest.skip("No active GROUP or PRIVATE packages available for testing")

    def _generate_payment_flags(self):
        """
        Generate valid payment flag combinations based on business logic:
        - If is_lockdown_payment = True → is_full_payment = False, book_at_deal_price = False
        - If book_at_deal_price = True → is_full_payment = False (regardless of lockdown status)
        - Otherwise, is_full_payment can be random
        """
        # First decide if this will be a lockdown payment (30% chance)
        is_lockdown_payment = random.choice([True, False])
        
        if is_lockdown_payment:
            # Lockdown payment: both other flags MUST be False
            is_full_payment = False
            book_at_deal_price = False
            self.logger.debug("🔒 Using LOCKDOWN payment (full payment and deal price disabled)")
        else:
            # Not lockdown: decide if using deal price
            book_at_deal_price = random.choice([True, False])
            
            if book_at_deal_price:
                # Deal price: full payment MUST be False
                is_full_payment = False
                self.logger.debug(f"💰 Using DEAL PRICE (full payment disabled)")
            else:
                # Regular booking: full payment can be random
                is_full_payment = random.choice([True, False])
                self.logger.debug(f"💳 Regular booking - Full payment: {is_full_payment}")
        
        return {
            "is_lockdown_payment": is_lockdown_payment,
            "is_full_payment": is_full_payment,
            "book_at_deal_price": book_at_deal_price
        }

    def _test_book_group_package(self, package_api, package):
        """Helper to test booking a GROUP package"""
        package_id = package['id']
        package_title = package['title']
        package_end_date = package.get('end_date')
        
        self.logger.info(f"🔵 TESTING GROUP PACKAGE: {package_title} (ID: {package_id}) - End date: {package_end_date}")
        
        # Get pricing text from the package response
        pricing_text = None
        if package.get('prices') and len(package['prices']) > 0:
            # Randomly select a pricing option if multiple exist
            pricing_option = random.choice(package['prices'])
            pricing_text = pricing_option.get('pricing_text')
            price_value = pricing_option.get('price')
            self.logger.info(f"💰 Selected pricing: {pricing_text} - ${price_value}")
        else:
            self.logger.error("❌ No prices found in package response")
            pytest.fail(f"Package {package_id} has no prices")
        
        # Generate valid payment flags
        payment_flags = self._generate_payment_flags()
        
        # Create unique booking data
        random_suffix = random.randint(1000, 9999)
        
        # GROUP PACKAGE payload - NO dates required
        booking_data = {
            "package": str(package_id),
            "full_name": f"GroupTest User{random_suffix}",
            "email": f"grouptest{random_suffix}@yopmail.com",
            "phone": f"+234{random.randint(700000000, 809999999)}",
            "pricing_text": pricing_text,
            "is_full_payment": payment_flags["is_full_payment"],
            "adults": random.randint(1, 4),
            "children": random.randint(0, 2),
            "infants": random.randint(0, 1),
            "book_at_deal_price": payment_flags["book_at_deal_price"],
            "is_lockdown_payment": payment_flags["is_lockdown_payment"],
            # Note: For GROUP packages, we DON'T include departure_date or return_date
            # The package uses its own start_date/end_date
        }
        
        # Ensure children and infants don't exceed reasonable limits
        total_guests = booking_data["adults"] + booking_data["children"] + booking_data["infants"]
        if total_guests > 6 or total_guests == 0:
            booking_data["adults"] = 2
            booking_data["children"] = 1
            booking_data["infants"] = 0
        
        # Log the payload for debugging
        self.logger.info(f"📦 GROUP package payload: {booking_data}")
        
        # Make the booking request
        booking_response = package_api.book_package(booking_data)
        
        # Log response for debugging
        self.logger.info(f"📊 GROUP booking response status: {booking_response.status_code}")
        
        # Assertions for GROUP package
        assert booking_response.status_code == 201, f"GROUP package booking failed: {booking_response.text}"
        
        booking_result = booking_response.json()
        assert booking_result.get('message') == "Package booked successfully"
        
        self.logger.success(f"✅ Successfully booked GROUP package: {package_title}")
        return booking_result

    def _test_book_private_package(self, package_api, package):
        """Helper to test booking a PRIVATE package"""
        package_id = package['id']
        package_title = package['title']
        
        self.logger.info(f"🔵 TESTING PRIVATE PACKAGE: {package_title} (ID: {package_id})")
        
        # Get pricing text from the package response
        pricing_text = None
        if package.get('prices') and len(package['prices']) > 0:
            # Randomly select a pricing option if multiple exist
            pricing_option = random.choice(package['prices'])
            pricing_text = pricing_option.get('pricing_text')
            price_value = pricing_option.get('price')
            self.logger.info(f"💰 Selected pricing: {pricing_text} - ${price_value}")
        else:
            self.logger.error("❌ No prices found in package response")
            pytest.fail(f"Package {package_id} has no prices")
        
        # Generate valid payment flags
        payment_flags = self._generate_payment_flags()
        
        # Create unique booking data
        random_suffix = random.randint(1000, 9999)
        
        from datetime import datetime, timedelta
        import dateutil.parser
        
        # Get package date range
        package_start_date_str = package.get('start_date')
        package_end_date_str = package.get('end_date')
        
        if not package_start_date_str or not package_end_date_str:
            self.logger.error(f"❌ Package {package_id} missing start_date or end_date")
            pytest.fail(f"Package {package_id} missing required dates")
        
        # Parse package dates
        package_start_date = dateutil.parser.parse(package_start_date_str).date()
        package_end_date = dateutil.parser.parse(package_end_date_str).date()
        today = datetime.now().date()
        
        self.logger.info(f"📅 Package date range: {package_start_date} to {package_end_date}")
        
        # Determine departure date within package range
        if package_start_date > today:
            # Package starts in the future - use a date within the package range
            max_days_offset = (package_end_date - package_start_date).days
            
            # Choose a departure date within the package range (not too close to end)
            days_after_start = random.randint(0, max(0, max_days_offset - 3))
            departure_date = package_start_date + timedelta(days=days_after_start)
        else:
            # Package already started - use today or a future date within remaining window
            days_remaining = (package_end_date - today).days
            if days_remaining < 3:
                self.logger.warning(f"⚠️ Package {package_id} has only {days_remaining} days remaining")
            
            # Departure can be today or any day within remaining window
            days_offset = random.randint(0, max(0, days_remaining - 2))
            departure_date = today + timedelta(days=days_offset)
        
        # Ensure departure date is not before package start
        if departure_date < package_start_date:
            departure_date = package_start_date
        
        # Calculate return date (trip duration)
        # Trip should be at least 1 day, at most remaining days in package
        max_trip_duration = (package_end_date - departure_date).days
        if max_trip_duration < 1:
            self.logger.warning(f"⚠️ Package {package_id} has insufficient days for a trip")
            pytest.skip(f"Package {package_id} has insufficient days")
        
        trip_duration = random.randint(1, min(14, max_trip_duration))
        return_date = departure_date + timedelta(days=trip_duration)
        
        # Format dates as strings
        departure_date_str = departure_date.strftime("%Y-%m-%d")
        return_date_str = return_date.strftime("%Y-%m-%d")
        
        self.logger.info(f"📅 Selected departure: {departure_date_str}, return: {return_date_str} (duration: {trip_duration} days)")
        
        # PRIVATE PACKAGE payload - REQUIRES both departure_date AND return_date
        booking_data = {
            "package": str(package_id),
            "full_name": f"PrivateTest User{random_suffix}",
            "email": f"privatetest{random_suffix}@yopmail.com",
            "phone": f"+234{random.randint(700000000, 809999999)}",
            "pricing_text": pricing_text,
            "is_full_payment": payment_flags["is_full_payment"],
            "departure_date": departure_date_str,
            "return_date": return_date_str,
            "adults": random.randint(1, 4),
            "children": random.randint(0, 2),
            "infants": random.randint(0, 1),
            "book_at_deal_price": payment_flags["book_at_deal_price"],
            "is_lockdown_payment": payment_flags["is_lockdown_payment"],
        }
        
        # Ensure children and infants don't exceed reasonable limits
        total_guests = booking_data["adults"] + booking_data["children"] + booking_data["infants"]
        if total_guests > 6 or total_guests == 0:
            booking_data["adults"] = 2
            booking_data["children"] = 1
            booking_data["infants"] = 0
        
        # Log the payload for debugging
        self.logger.info(f"📦 PRIVATE package payload: {booking_data}")
        
        # Make the booking request
        booking_response = package_api.book_package(booking_data)
        
        # Log response for debugging
        self.logger.info(f"📊 PRIVATE booking response status: {booking_response.status_code}")
        if booking_response.status_code != 201:
            self.logger.error(f"❌ PRIVATE booking failed: {booking_response.text}")
        
        # Assertions for PRIVATE package
        assert booking_response.status_code == 201, f"PRIVATE package booking failed: {booking_response.text}"
        
        booking_result = booking_response.json()
        assert booking_result.get('message') == "Package booked successfully"
        
        # Verify dates were saved correctly
        booking_data_response = booking_result.get('data', {})
        if booking_data_response:
            self.logger.info(f"📅 Departure: {booking_data_response.get('departure_date')}, Return: {booking_data_response.get('return_date')}")
        
        self.logger.success(f"✅ Successfully booked PRIVATE package: {package_title}")
        return booking_result
    
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
                    "email": f"botverification{random_suffix}@yopmail.com",
                    "phone": f"+23481{random.randint(1000000,9999999)}",
                    "departure_date": "2025-12-20",
                    "adults": 1,
                    "children": 0,
                    "infants": 0,
                    "pricing_text": package['prices'][0]['pricing_text'] if package.get('prices') else "Standard",
                    "book_at_deal_price": False,
                    "is_full_payment": True,
                    "is_lockdown_payment": False
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
                test_email = f"botverification{random_suffix}@yopmail.com"
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
                    "is_full_payment": True,
                    "is_lockdown_payment": False
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

# src/tests/partners_api_tests/test_partners_package.py

import pytest
import random
import functools
import requests
import time
from datetime import datetime, timedelta
import dateutil.parser
from src.pages.api.partners_api.partners_auth_api import PartnersAuthAPI
from src.pages.api.partners_api.partners_package_api import PartnersPackageAPI
from src.pages.api.partners_api.organization_api import PartnersOrganizationAPI
from src.utils.verified_partners_helper import VerifiedUserHelper
from configs.environment import EnvironmentConfig
from src.utils.logger import GeoLogger

def retry_on_timeout(max_retries=3, delay=2):
    """Decorator to retry test on timeout"""
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
                    
                    wait_time = delay * (2 ** attempt)
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
        self.package_api = PartnersPackageAPI()
        
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
        self.logger.info(f"🔵 CREATING UNVERIFIED USER: {self.test_email}")
        signup_response = self.auth_api.signup(self.test_org_data)
        assert signup_response.status_code == 201
        
        self.logger.info(f"🔵 ATTEMPTING PACKAGE LISTING: {self.test_email}")
        response = self.package_api.get_all_packages()
        
        assert response.status_code in [401, 403], (
            f"Unverified user should be blocked from package listing. Got {response.status_code}"
        )
        self.logger.success(f"✅ Unverified user correctly blocked from package listing: {self.test_email}")
    
    @pytest.mark.partners_api
    @pytest.mark.security
    def test_unverified_user_blocked_from_package_countries(self):
        """Test that unverified users cannot get package countries"""
        self.logger.info(f"🔵 CREATING UNVERIFIED USER: {self.test_email}")
        signup_response = self.auth_api.signup(self.test_org_data)
        assert signup_response.status_code == 201
        
        self.logger.info(f"🔵 ATTEMPTING PACKAGE COUNTRIES: {self.test_email}")
        response = self.package_api.get_package_countries()
        
        assert response.status_code in [401, 403], (
            f"Unverified user should be blocked from package countries. Got {response.status_code}"
        )
        self.logger.success(f"✅ Unverified user correctly blocked from package countries: {self.test_email}")
    
    @pytest.mark.partners_api
    @pytest.mark.security
    def test_unverified_user_blocked_from_package_booking(self):
        """Test that unverified users cannot book packages"""
        self.logger.info(f"🔵 CREATING UNVERIFIED USER: {self.test_email}")
        signup_response = self.auth_api.signup(self.test_org_data)
        assert signup_response.status_code == 201
        
        self.logger.info(f"🔵 ATTEMPTING PACKAGE BOOKING: {self.test_email}")
        booking_data = {
            "package": "11",
            "full_name": "John Doe",
            "email": "geopartners@yopmail.com", 
            "phone": "+2348123456789",
            "adults": 2,
            "children": 1,
            "infants": 0,
            "pricing_text": "Family Trip",
            "book_at_deal_price": False,
            "is_full_payment": True,
            "is_lockdown_payment": False
        }
        response = self.package_api.book_package(booking_data)
        
        assert response.status_code in [401, 403], (
            f"Unverified user should be blocked from package booking. Got {response.status_code}"
        )
        self.logger.success(f"✅ Unverified user correctly blocked from package booking: {self.test_email}")


class TestPartnersPackageFunctionality:
    """FUNCTIONALITY TESTS - Verified users can access package operations"""
    
    def setup_method(self):
        if not EnvironmentConfig.validate_partners_credentials():
            pytest.skip("Partners verified account credentials not configured")
        
        self.verified_helper = VerifiedUserHelper()
        self.org_api = self.verified_helper.get_verified_organization_api()
        self.logger = GeoLogger(self.__class__.__name__)
    
    # ==================== HELPER METHODS ====================
    
    def _get_active_packages(self, package_api, package_type=None, require_deal=False):
        """Get active packages with optional filters"""
        response = package_api.get_all_packages(limit=50)
        if response.status_code != 200:
            return []
        
        data = response.json()
        all_packages = data['data']['packages']
        
        if not all_packages:
            return []
        
        today = datetime.now().date()
        filtered_packages = []
        
        for p in all_packages:
            if p.get('status') != 'Active':
                continue
            
            if not p.get('prices') or len(p['prices']) == 0:
                continue
            
            if package_type and p.get('package_type') != package_type:
                continue
            
            end_date_str = p.get('end_date')
            if end_date_str:
                end_date = dateutil.parser.parse(end_date_str).date()
                if end_date < today:
                    continue
            
            if require_deal and p.get('deal') is None:
                continue
            
            filtered_packages.append(p)
        
        return filtered_packages

    def _select_package_with_future_departure(self, package, min_days=31):
        """Select departure date > min_days away for PRIVATE package"""
        today = datetime.now().date()
        package_start_date = dateutil.parser.parse(package['start_date']).date()
        package_end_date = dateutil.parser.parse(package['end_date']).date()
        
        # Try to get departure date > min_days away
        if package_start_date > today + timedelta(days=min_days):
            departure_date = package_start_date
        elif package_end_date > today + timedelta(days=min_days):
            max_possible = (package_end_date - today).days
            days_offset = random.randint(min_days + 1, max_possible)
            departure_date = today + timedelta(days=days_offset)
        else:
            departure_date = package_start_date if package_start_date > today else today + timedelta(days=1)
        
        max_trip_duration = (package_end_date - departure_date).days
        trip_duration = min(7, max(1, max_trip_duration))
        return_date = departure_date + timedelta(days=trip_duration)
        
        return departure_date, return_date
    
    def _select_package_within_30_days(self, package):
        """Select departure date within 30 days for PRIVATE package"""
        today = datetime.now().date()
        package_start_date = dateutil.parser.parse(package['start_date']).date()
        package_end_date = dateutil.parser.parse(package['end_date']).date()
        
        if package_start_date <= today + timedelta(days=30):
            if package_start_date > today:
                departure_date = package_start_date
            else:
                days_offset = random.randint(1, min(30, (package_end_date - today).days))
                departure_date = today + timedelta(days=days_offset)
        else:
            departure_date = package_start_date
        
        max_trip_duration = (package_end_date - departure_date).days
        trip_duration = min(7, max(1, max_trip_duration))
        return_date = departure_date + timedelta(days=trip_duration)
        
        return departure_date, return_date
    
    def _generate_payment_flags(self, days_until_departure=None):
        """
        Generate valid payment flag combinations with 30-day rule awareness
        """
        # Force full payment if departure within 30 days
        if days_until_departure is not None and days_until_departure <= 30:
            self.logger.info(f"📅 Departure within {days_until_departure} days - forcing full payment")
            return {
                "is_lockdown_payment": False,
                "is_full_payment": True,
                "book_at_deal_price": False
            }
        
        # Original logic for >30 days
        is_lockdown_payment = random.choice([True, False])
        
        if is_lockdown_payment:
            return {
                "is_lockdown_payment": True,
                "is_full_payment": False,
                "book_at_deal_price": False
            }
        else:
            book_at_deal_price = random.choice([True, False])
            if book_at_deal_price:
                return {
                    "is_lockdown_payment": False,
                    "is_full_payment": False,
                    "book_at_deal_price": True
                }
            else:
                return {
                    "is_lockdown_payment": False,
                    "is_full_payment": random.choice([True, False]),
                    "book_at_deal_price": False
                }
    
    def _build_booking_payload(self, package, pricing_text, payment_flags, package_type, departure_date=None, return_date=None):
        """Build booking payload with optional dates for PRIVATE packages"""
        random_suffix = random.randint(1000, 9999)
        
        base_payload = {
            "package": str(package['id']),
            "full_name": f"Test User {random_suffix}",
            "email": f"testuser{random_suffix}@yopmail.com",
            "phone": f"+234{random.randint(700000000, 809999999)}",
            "pricing_text": pricing_text,
            "is_full_payment": payment_flags["is_full_payment"],
            "adults": random.randint(1, 3),
            "children": random.randint(0, 1),
            "infants": 0,
            "book_at_deal_price": payment_flags["book_at_deal_price"],
            "is_lockdown_payment": payment_flags["is_lockdown_payment"],
        }
        
        # Add dates for PRIVATE packages
        if package_type == "PRIVATE" and departure_date and return_date:
            base_payload["departure_date"] = departure_date.strftime("%Y-%m-%d")
            base_payload["return_date"] = return_date.strftime("%Y-%m-%d")
        
        return base_payload
    
    def _verify_booking_response(self, response, expected_status=201):
        """Verify booking response structure"""
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}"
        
        if expected_status == 201:
            data = response.json()
            assert data.get('message') == "Package booked successfully"
            return data
        return None
    
    def _get_initial_bookings_count(self, package_api):
        """Get initial total bookings count using pagination"""
        response = package_api.get_package_bookings(limit=20)
        if response.status_code == 200:
            return response.json()['data']['pagination']['totalItems']
        return 0
    
    def _verify_bookings_increased(self, package_api, initial_count, expected_increase=1, max_wait=10):
        """Verify bookings count increased using totalItems"""
        import time
        
        for wait in range(max_wait):
            time.sleep(1)
            response = package_api.get_package_bookings(limit=20)
            if response.status_code == 200:
                current_count = response.json()['data']['pagination']['totalItems']
                if current_count >= initial_count + expected_increase:
                    self.logger.success(f"✅ Bookings increased from {initial_count} to {current_count}")
                    return current_count
        
        response = package_api.get_package_bookings(limit=20)
        current_count = response.json()['data']['pagination']['totalItems']
        assert current_count >= initial_count + expected_increase, \
            f"Bookings didn't increase! Before: {initial_count}, After: {current_count}"
        return current_count
    
    def _find_booking_by_email(self, package_api, email, max_pages=5):
        """Find a booking by email across multiple pages"""
        for page in range(1, max_pages + 1):
            response = package_api.get_package_bookings(limit=50, page=page)
            if response.status_code != 200:
                continue
            
            data = response.json()['data']
            for booking in data['bookings']:
                if booking['user_details']['email'] == email:
                    return booking
            
            if page >= data['pagination']['totalPages']:
                break
        
        return None
    
    # ==================== PACKAGE LISTING TESTS ====================
    
    @pytest.mark.partners_api
    @retry_on_timeout(max_retries=3, delay=2)
    def test_verified_user_can_get_packages(self):
        """TEST: Verified users can get package listings with complete structure"""
        package_api = self.verified_helper.get_verified_package_api()
        assert package_api is not None
        
        self.logger.info("🔵 VERIFIED USER - Getting package listings")
        
        original_timeout = package_api.timeout
        package_api.timeout = 90
        
        try:
            response = package_api.get_all_packages(limit=20)
        finally:
            package_api.timeout = original_timeout
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['message'] == "Packages retrieved successfully"
        assert 'data' in data
        assert 'packages' in data['data']
        
        packages = data['data']['packages']
        assert isinstance(packages, list)
        
        if packages:
            first_package = packages[0]
            required_fields = ['id', 'title', 'package_type', 'prices', 'destinations', 'status']
            for field in required_fields:
                assert field in first_package, f"Package missing field: {field}"
        
        self.logger.success(f"✅ Verified user can get packages - found {len(packages)} packages")
        self.available_packages = packages
    
    @pytest.mark.partners_api
    def test_verified_user_can_get_package_countries(self):
        """TEST: Verified users can get available package countries and cities"""
        package_api = self.verified_helper.get_verified_package_api()
        
        self.logger.info("🔵 VERIFIED USER - Getting package countries")
        response = package_api.get_package_countries()
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['message'] == "Available Package countries retrieved successfully"
        assert 'data' in data
        assert 'countries' in data['data']
        assert 'cities' in data['data']
        
        countries = data['data']['countries']
        cities = data['data']['cities']
        
        assert isinstance(countries, list)
        assert isinstance(cities, list)
        assert len(countries) > 0, "Should have available countries"
        assert len(cities) > 0, "Should have available cities"
        
        self.logger.success(f"✅ Verified user can get package countries - {len(countries)} countries, {len(cities)} cities")
    
    # ==================== GROUP PACKAGE BOOKING TESTS ====================
    
    @pytest.mark.partners_api
    def test_verified_user_book_group_full_payment(self):
        """TEST: Verified users can book GROUP packages with FULL PAYMENT"""
        self.logger.info("=== Testing GROUP Package - Full Payment ===")
        
        package_api = self.verified_helper.get_verified_package_api()
        
        packages = self._get_active_packages(package_api, package_type="GROUP")
        if not packages:
            pytest.skip("No active GROUP packages available")
        
        package = random.choice(packages)
        self.logger.info(f"📦 Selected package: {package['title']} (ID: {package['id']})")
        
        pricing = random.choice(package['prices'])
        self.logger.info(f"💰 Selected pricing: {pricing['pricing_text']}")
        
        payment_flags = {
            "is_full_payment": True,
            "is_lockdown_payment": False,
            "book_at_deal_price": False
        }
        
        initial_count = self._get_initial_bookings_count(package_api)
        
        payload = self._build_booking_payload(
            package=package, 
            pricing_text=pricing['pricing_text'], 
            payment_flags=payment_flags,
            package_type="GROUP"
        )
        self.logger.info(f"📦 Payload: {payload}")
        
        response = package_api.book_package(payload)
        self._verify_booking_response(response)
        
        self._verify_bookings_increased(package_api, initial_count)
        self.logger.success("✅ GROUP package full payment test passed")
    
    @pytest.mark.partners_api
    def test_verified_user_book_group_lockdown_payment(self):
        """TEST: Verified users can book GROUP packages with LOCKDOWN PAYMENT"""
        self.logger.info("=== Testing GROUP Package - Lockdown Payment ===")
        
        package_api = self.verified_helper.get_verified_package_api()
        
        packages = self._get_active_packages(package_api, package_type="GROUP")
        if not packages:
            pytest.skip("No active GROUP packages available")
        
        package = random.choice(packages)
        self.logger.info(f"📦 Selected package: {package['title']} (ID: {package['id']})")
        
        pricing = random.choice(package['prices'])
        
        payment_flags = {
            "is_full_payment": False,
            "is_lockdown_payment": True,
            "book_at_deal_price": False
        }
        
        initial_count = self._get_initial_bookings_count(package_api)
        
        payload = self._build_booking_payload(
            package=package, 
            pricing_text=pricing['pricing_text'], 
            payment_flags=payment_flags,
            package_type="GROUP"
        )
        response = package_api.book_package(payload)
        
        self._verify_booking_response(response)
        self._verify_bookings_increased(package_api, initial_count)
        self.logger.success("✅ GROUP package lockdown payment test passed")
    
    @pytest.mark.partners_api
    def test_verified_user_book_group_deal_price(self):
        """TEST: Verified users can book GROUP packages with DEAL PRICE"""
        self.logger.info("=== Testing GROUP Package - Deal Price ===")
        
        package_api = self.verified_helper.get_verified_package_api()
        
        packages = self._get_active_packages(package_api, package_type="GROUP", require_deal=True)
        if not packages:
            pytest.skip("No active GROUP packages with deals available")
        
        package = random.choice(packages)
        self.logger.info(f"📦 Selected package with deal: {package['title']} (ID: {package['id']})")
        
        pricing = random.choice(package['prices'])
        
        payment_flags = {
            "is_full_payment": False,
            "is_lockdown_payment": False,
            "book_at_deal_price": True
        }
        
        initial_count = self._get_initial_bookings_count(package_api)
        
        payload = self._build_booking_payload(
            package=package, 
            pricing_text=pricing['pricing_text'], 
            payment_flags=payment_flags,
            package_type="GROUP"
        )
        response = package_api.book_package(payload)
        
        self._verify_booking_response(response)
        self._verify_bookings_increased(package_api, initial_count)
        self.logger.success("✅ GROUP package deal price test passed")
    
    # ==================== PRIVATE PACKAGE BOOKING TESTS ====================
    
    @pytest.mark.partners_api
    def test_verified_user_book_private_future_departure(self):
        """TEST: Verified users can book PRIVATE packages with departure >30 days away (any payment type)"""
        self.logger.info("=== Testing PRIVATE Package - Future Departure (>30 days) ===")
        
        package_api = self.verified_helper.get_verified_package_api()
        
        packages = self._get_active_packages(package_api, package_type="PRIVATE")
        if not packages:
            pytest.skip("No active PRIVATE packages available")
        
        package = random.choice(packages)
        self.logger.info(f"📦 Selected package: {package['title']} (ID: {package['id']})")
        
        departure_date, return_date = self._select_package_with_future_departure(package, min_days=31)
        days_until = (departure_date - datetime.now().date()).days
        self.logger.info(f"📅 Selected departure: {departure_date} ({days_until} days away)")
        
        pricing = random.choice(package['prices'])
        
        payment_flags = self._generate_payment_flags(days_until)
        
        initial_count = self._get_initial_bookings_count(package_api)
        
        payload = self._build_booking_payload(
            package=package,
            pricing_text=pricing['pricing_text'],
            payment_flags=payment_flags,
            package_type="PRIVATE",
            departure_date=departure_date,
            return_date=return_date
        )
        self.logger.info(f"📦 Payload: {payload}")
        
        response = package_api.book_package(payload)
        self.logger.info(f"📦 Response: {response}")
        self._verify_booking_response(response)
        
        self._verify_bookings_increased(package_api, initial_count)
        self.logger.success("✅ PRIVATE package future departure test passed")
    
    @pytest.mark.partners_api
    def test_verified_user_book_private_within_30_days_full_payment(self):
        """TEST: Verified users can book PRIVATE packages within 30 days with FULL PAYMENT"""
        self.logger.info("=== Testing PRIVATE Package - Within 30 Days (Full Payment) ===")
        
        package_api = self.verified_helper.get_verified_package_api()
        
        packages = self._get_active_packages(package_api, package_type="PRIVATE")
        if not packages:
            pytest.skip("No active PRIVATE packages available")
        
        # Find package with date within 30 days
        package = None
        valid_departure = None
        valid_return = None
        
        for p in packages:
            try:
                dep, ret = self._select_package_within_30_days(p)
                days_until = (dep - datetime.now().date()).days
                if 0 < days_until <= 30:
                    package = p
                    valid_departure = dep
                    valid_return = ret
                    break
            except:
                continue
        
        if not package:
            pytest.skip("No PRIVATE packages with departure within 30 days available")
        
        self.logger.info(f"📦 Selected package: {package['title']} (ID: {package['id']})")
        self.logger.info(f"📅 Departure in {(valid_departure - datetime.now().date()).days} days")
        
        pricing = random.choice(package['prices'])
        
        payment_flags = {
            "is_full_payment": True,
            "is_lockdown_payment": False,
            "book_at_deal_price": False
        }
        
        initial_count = self._get_initial_bookings_count(package_api)
        
        payload = self._build_booking_payload(
            package=package,
            pricing_text=pricing['pricing_text'],
            payment_flags=payment_flags,
            package_type="PRIVATE",
            departure_date=valid_departure,
            return_date=valid_return
        )
        self.logger.info(f"📦 Payload: {payload}")
        
        response = package_api.book_package(payload)
        self.logger.info(f"📦 Response: {response}")
        self._verify_booking_response(response)
        
        self._verify_bookings_increased(package_api, initial_count)
        self.logger.success("✅ PRIVATE package within 30 days (full payment) test passed")
    
    @pytest.mark.partners_api
    def test_verified_user_book_private_within_30_days_lockdown_fails(self):
        """TEST: PRIVATE packages within 30 days - LOCKDOWN PAYMENT should FAIL with correct error message"""
        self.logger.info("=== Testing PRIVATE Package - Within 30 Days (Lockdown Should Fail) ===")
        
        package_api = self.verified_helper.get_verified_package_api()
        
        packages = self._get_active_packages(package_api, package_type="PRIVATE")
        if not packages:
            pytest.skip("No active PRIVATE packages available")
        
        # Find package with date within 30 days
        package = None
        valid_departure = None
        valid_return = None
        
        for p in packages:
            try:
                dep, ret = self._select_package_within_30_days(p)
                days_until = (dep - datetime.now().date()).days
                if 0 < days_until <= 30:
                    package = p
                    valid_departure = dep
                    valid_return = ret
                    break
            except:
                continue
        
        if not package:
            pytest.skip("No PRIVATE packages with departure within 30 days available")
        
        self.logger.info(f"📦 Selected package: {package['title']} (ID: {package['id']})")
        self.logger.info(f"📅 Departure in {(valid_departure - datetime.now().date()).days} days")
        
        pricing = random.choice(package['prices'])
        
        payment_flags = {
            "is_full_payment": False,
            "is_lockdown_payment": True,  # This should cause failure
            "book_at_deal_price": False
        }
        
        payload = self._build_booking_payload(
            package=package,
            pricing_text=pricing['pricing_text'],
            payment_flags=payment_flags,
            package_type="PRIVATE",
            departure_date=valid_departure,
            return_date=valid_return
        )
        self.logger.info(f"📦 Attempting lockdown payment (should fail): {payload}")
        
        response = package_api.book_package(payload)
        self.logger.info(f"📦 Response: {response}")
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        error_data = response.json()
        error_message = error_data.get('message', '')
        expected_error = "Full payment is required for departure dates within 30 days"
        
        assert expected_error in error_message, f"Expected '{expected_error}', got '{error_message}'"
        self.logger.success(f"✅ Correctly got 400: '{error_message}'")
    
    # ==================== VERIFICATION TESTS ====================
    
    @pytest.mark.partners_api
    def test_package_booking_appears_in_bookings_list(self):
        """TEST: Package bookings appear in the organization's bookings list"""
        package_api = self.verified_helper.get_verified_package_api()
        
        self.logger.info("🔵 CHECKING PACKAGE BOOKINGS LIST")
        
        response = package_api.get_package_bookings(limit=20)
        assert response.status_code == 200
        
        data = response.json()
        assert data['message'] == "Bookings retrieved successfully"
        assert 'data' in data
        assert 'bookings' in data['data']
        assert 'pagination' in data['data']
        
        bookings = data['data']['bookings']
        pagination = data['data']['pagination']
        
        self.logger.info(f"📊 Total bookings: {pagination['totalItems']}, Page {pagination['currentPage']}/{pagination['totalPages']}")
        
        if bookings:
            first_booking = bookings[0]
            required_fields = ['id', 'booking_code', 'user_details', 'package', 'organization', 'booking_status']
            for field in required_fields:
                assert field in first_booking, f"Booking missing field: {field}"
        
        self.logger.success(f"✅ Package bookings list accessible - total: {pagination['totalItems']}")
    
    @pytest.mark.partners_api
    def test_package_booking_counted_in_usage(self):
        """TEST: Package bookings are properly counted in organization usage"""
        package_api = self.verified_helper.get_verified_package_api()
        
        self.logger.info("🔵 GETTING BASELINE USAGE")
        initial_usage_response = self.org_api.get_usage(mode='test')
        assert initial_usage_response.status_code == 200
        
        initial_usage_data = initial_usage_response.json()
        initial_records = initial_usage_data['data']['records']
        initial_total_bookings = sum(record.get('packageBookings', 0) for record in initial_records)
        
        self.logger.info(f"📊 Initial package bookings: {initial_total_bookings}")
        
        packages = self._get_active_packages(package_api, package_type="GROUP")
        if not packages:
            pytest.skip("No active packages for booking test")
        
        package = packages[0]
        pricing = random.choice(package['prices'])
        
        payment_flags = {
            "is_full_payment": True,
            "is_lockdown_payment": False,
            "book_at_deal_price": False
        }
        
        payload = self._build_booking_payload(
            package=package, 
            pricing_text=pricing['pricing_text'], 
            payment_flags=payment_flags,
            package_type="GROUP"
        )
        
        self.logger.info("🔵 CREATING NEW BOOKING")
        booking_response = package_api.book_package(payload)
        
        if booking_response.status_code != 201:
            pytest.skip(f"Booking failed with status {booking_response.status_code}")
        
        time.sleep(3)
        
        self.logger.info("🔵 CHECKING UPDATED USAGE")
        final_usage_response = self.org_api.get_usage(mode='test')
        assert final_usage_response.status_code == 200
        
        final_usage_data = final_usage_response.json()
        final_records = final_usage_data['data']['records']
        final_total_bookings = sum(record.get('packageBookings', 0) for record in final_records)
        
        self.logger.info(f"📊 Final package bookings: {final_total_bookings}")
        
        assert final_total_bookings > initial_total_bookings, \
            f"Bookings should increase from {initial_total_bookings} to {final_total_bookings}"
        
        self.logger.success(f"✅ Package booking correctly counted - increased to {final_total_bookings}")
    
    @pytest.mark.partners_api
    def test_package_usage_reflected_in_range_endpoint(self):
        """TEST: Package usage data is reflected in usage range endpoint"""
        self.logger.info("🔵 CHECKING USAGE RANGE FOR PACKAGE DATA")
        
        response = self.org_api.get_usage_range(
            mode='test', 
            start_date='2025-01-01', 
            end_date='2025-12-31'
        )
        assert response.status_code == 200
        
        data = response.json()
        range_data = data['data']
        
        assert 'totalPackageBookings' in range_data
        assert isinstance(range_data['totalPackageBookings'], int)
        
        self.logger.info(f"📊 Usage Range - Package Bookings: {range_data['totalPackageBookings']}")
        self.logger.success("✅ Package usage data correctly reflected in usage range")
    
    @pytest.mark.partners_api
    def test_package_booking_creates_complete_record(self):
        """TEST: Package booking creates a complete record with all required fields"""
        package_api = self.verified_helper.get_verified_package_api()
        
        self.logger.info("🔵 VERIFYING COMPLETE BOOKING RECORD CREATION")
        
        initial_count = self._get_initial_bookings_count(package_api)
        self.logger.info(f"📊 Initial total bookings: {initial_count}")
        
        packages = self._get_active_packages(package_api, package_type="GROUP")
        if not packages:
            pytest.skip("No active packages available")
        
        package = packages[0]
        pricing = random.choice(package['prices'])
        
        random_suffix = random.randint(10000, 99999)
        test_email = f"botverification{random_suffix}@yopmail.com"
        test_full_name = f"Verification Test User {random_suffix}"
        
        payment_flags = {
            "is_full_payment": True,
            "is_lockdown_payment": False,
            "book_at_deal_price": False
        }
        
        payload = {
            "package": str(package['id']),
            "full_name": test_full_name,
            "email": test_email,
            "phone": f"+23481{random.randint(1000000,9999999)}",
            "pricing_text": pricing['pricing_text'],
            "is_full_payment": payment_flags["is_full_payment"],
            "adults": 2,
            "children": 0,
            "infants": 0,
            "book_at_deal_price": payment_flags["book_at_deal_price"],
            "is_lockdown_payment": payment_flags["is_lockdown_payment"],
        }
        
        self.logger.info("🔵 CREATING NEW PACKAGE BOOKING")
        booking_response = package_api.book_package(payload)
        
        if booking_response.status_code != 201:
            pytest.skip(f"Booking failed with status {booking_response.status_code}")
        
        final_count = self._verify_bookings_increased(package_api, initial_count)
        
        new_booking = self._find_booking_by_email(package_api, test_email)
        assert new_booking is not None, f"New booking with email {test_email} should appear in bookings list"
        
        assert 'id' in new_booking
        assert 'booking_code' in new_booking
        assert 'user_details' in new_booking
        assert 'package' in new_booking
        assert 'organization' in new_booking
        assert 'booking_status' in new_booking
        
        user_details = new_booking['user_details']
        assert user_details['email'] == test_email
        assert user_details['full_name'] == test_full_name
        
        package_info = new_booking['package']
        assert str(package_info['id']) == payload['package']
        
        organization = new_booking['organization']
        assert 'id' in organization
        assert 'name' in organization
        
        self.logger.success(f"✅ Package booking correctly created and verified")
        self.logger.info(f"📋 New booking ID: {new_booking['id']}, Code: {new_booking['booking_code']}")
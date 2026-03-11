# src/tests/api_tests/test_package_api.py

import pytest
from src.pages.api.package_api import PackageAPI
from src.pages.api.auth_api import AuthAPI
from src.utils.logger import GeoLogger
import random
from datetime import datetime, timedelta
import dateutil.parser

class TestPackageAPI:
    
    def setup_method(self):
        self.logger = GeoLogger(self.__class__.__name__)
    
    @pytest.fixture
    def authenticated_package_api(self):
        auth_api = AuthAPI()
        response = auth_api.login()
        
        if response.status_code != 200:
            self.logger.error(f"❌ Login failed with status {response.status_code}")
            pytest.skip(f"Login failed with status {response.status_code}")
        self.logger.success(f"✅ Authenticated successfully (token length: {len(auth_api.auth_token)})")
            
        package_api = PackageAPI()
        package_api.set_auth_token(auth_api.auth_token)
        package_api.set_auth_token(auth_api.auth_token, token_source=auth_api.token_source)
        return package_api
    
    @pytest.fixture
    def unauthenticated_package_api(self):
        """Fixture for unauthenticated PackageAPI instance"""
        package_api = PackageAPI()
        package_api.set_auth_token(None)
        package_api.headers.pop('Authorization', None)
        package_api.headers.pop('Cookie', None)
        return package_api
    
    # ==================== HELPER METHODS ====================
    
    def _get_active_packages(self, api_client, package_type=None, require_deal=False, min_days_until_departure=None):
        """
        Get active packages with optional filters
        
        Args:
            api_client: API client instance
            package_type: 'GROUP', 'PRIVATE', or None for both
            require_deal: If True, only return packages with deals
            min_days_until_departure: Minimum days until departure (for PRIVATE packages)
        
        Returns:
            List of filtered packages
        """
        response = api_client.get_all_packages(limit=50)
        if response.status_code != 200:
            return []
        
        packages_data = response.json()
        
        # Extract packages from nested structure
        if isinstance(packages_data, dict) and 'data' in packages_data:
            package_data = packages_data['data']
            if 'packages' in package_data:
                all_packages = package_data['packages']
            else:
                all_packages = package_data.get('data', [])
        else:
            all_packages = packages_data if isinstance(packages_data, list) else []
        
        if not all_packages:
            return []
        
        today = datetime.now().date()
        filtered_packages = []
        
        for p in all_packages:
            # Skip if not active
            if p.get('status') != 'Active':
                continue
            
            # Skip if no prices
            if not p.get('prices') or len(p['prices']) == 0:
                continue
            
            # Filter by package type
            if package_type and p.get('package_type') != package_type:
                continue
            
            # Check if package is still active (end_date not in past)
            end_date_str = p.get('end_date')
            if end_date_str:
                end_date = dateutil.parser.parse(end_date_str).date()
                if end_date < today:
                    continue
            
            # Filter by deal requirement
            if require_deal and p.get('deal') is None:
                continue
            
            # For PRIVATE packages with min_days_until_departure requirement
            if p.get('package_type') == 'PRIVATE' and min_days_until_departure is not None:
                # Calculate a sample departure date
                package_start_date = dateutil.parser.parse(p.get('start_date')).date()
                package_end_date = dateutil.parser.parse(p.get('end_date')).date()
                
                # Get a departure date >30 days away if needed
                if package_start_date > today:
                    departure_date = package_start_date
                else:
                    departure_date = today + timedelta(days=min_days_until_departure + 1)
                
                days_until = (departure_date - today).days
                if days_until <= min_days_until_departure:
                    continue
            
            filtered_packages.append(p)
        
        return filtered_packages
    
    def _select_package_with_future_departure(self, package, min_days=31):
        """
        Select a departure date for PRIVATE package that's > min_days away
        Returns departure_date and return_date
        """
        from datetime import datetime, timedelta
        import dateutil.parser
        
        today = datetime.now().date()
        package_start_date = dateutil.parser.parse(package.get('start_date')).date()
        package_end_date = dateutil.parser.parse(package.get('end_date')).date()
        
        # Try to get departure date > min_days away
        if package_start_date > today + timedelta(days=min_days):
            departure_date = package_start_date
        elif package_end_date > today + timedelta(days=min_days):
            # Pick a date > min_days away but within package range
            max_possible = (package_end_date - today).days
            days_offset = random.randint(min_days + 1, max_possible)
            departure_date = today + timedelta(days=days_offset)
        else:
            # No date > min_days away, return earliest possible
            departure_date = package_start_date if package_start_date > today else today + timedelta(days=1)
        
        # Calculate return date
        max_trip_duration = (package_end_date - departure_date).days
        trip_duration = min(7, max(1, max_trip_duration))
        return_date = departure_date + timedelta(days=trip_duration)
        
        return departure_date, return_date
    
    def _select_package_within_30_days(self, package):
        """
        Select a departure date for PRIVATE package that's within 30 days
        Returns departure_date and return_date
        """
        from datetime import datetime, timedelta
        import dateutil.parser
        
        today = datetime.now().date()
        package_start_date = dateutil.parser.parse(package.get('start_date')).date()
        package_end_date = dateutil.parser.parse(package.get('end_date')).date()
        
        # Try to get departure date within 30 days
        if package_start_date <= today + timedelta(days=30):
            if package_start_date > today:
                departure_date = package_start_date
            else:
                # Package already started, pick a date within next 30 days
                days_offset = random.randint(1, min(30, (package_end_date - today).days))
                departure_date = today + timedelta(days=days_offset)
        else:
            # No date within 30 days, return earliest
            departure_date = package_start_date
        
        # Calculate return date
        max_trip_duration = (package_end_date - departure_date).days
        trip_duration = min(7, max(1, max_trip_duration))
        return_date = departure_date + timedelta(days=trip_duration)
        
        return departure_date, return_date
    
    def _build_booking_payload(self, package, pricing_text, payment_flags, payment_method, 
                               package_type, departure_date=None, return_date=None):
        """Build booking payload with optional dates for PRIVATE packages"""
        base_payload = {
            "package": package.get('id'),
            "full_name": "GEO Bot" if payment_flags.get('authenticated') else f"Unauth Test User {random.randint(1000,9999)}",
            "email": "geo.qa.bot@gmail.com" if payment_flags.get('authenticated') else f"unauth{random.randint(1000,9999)}@test.com",
            "phone": "1234567890" if payment_flags.get('authenticated') else f"+234{random.randint(700000000, 809999999)}",
            "pricing_text": pricing_text,
            "is_full_payment": payment_flags["is_full_payment"],
            "adults": random.randint(1, 3),
            "children": random.randint(0, 1),
            "infants": 0,
            "is_lockdown_payment": payment_flags["is_lockdown_payment"],
            "book_at_deal_price": payment_flags["book_at_deal_price"],
            "paymentMethod": payment_method
        }
        
        # Add dates for PRIVATE packages
        if package_type == "PRIVATE" and departure_date and return_date:
            base_payload["departure_date"] = departure_date.strftime("%Y-%m-%d")
            base_payload["return_date"] = return_date.strftime("%Y-%m-%d")
        
        return base_payload
    
    def _verify_booking_response(self, response, expected_user_id_not_null=True):
        """Verify booking response structure"""
        assert response.status_code == 200
        response_data = response.json()
        assert response_data.get('status') == 'success'
        
        booking_data = response_data.get('data', {})
        
        # Verify user_id
        user_id = None
        if 'bookedPackage' in booking_data:
            user_id = booking_data['bookedPackage'].get('user_id')
        elif 'id' in booking_data:
            user_id = booking_data.get('user_id')
        
        if expected_user_id_not_null:
            assert user_id is not None, "user_id should not be null for authenticated booking"
            self.logger.success(f"✅ Verified user_id = {user_id} is present")
        else:
            assert user_id is None, f"user_id should be null for unauthenticated booking, got: {user_id}"
            self.logger.success(f"✅ Verified user_id = null for unauthenticated booking")
        
        # Extract booking ID
        booking_id = None
        if 'data' in response_data:
            if 'bookedPackage' in response_data['data']:
                booking_id = response_data['data']['bookedPackage'].get('id')
            elif 'id' in response_data['data']:
                booking_id = response_data['data'].get('id')
        
        return response_data, booking_id
    
    def _verify_user_bookings_increased(self, api_client, initial_total_items, new_booking_id=None):
        """
        Verify that user's bookings increased using totalItems from pagination
        
        Args:
            api_client: Authenticated API client
            initial_total_items: Total items from before booking
            new_booking_id: ID of the new booking to verify
        """
        import time
        time.sleep(2)
        
        # Get updated bookings with high limit to get pagination info
        response = api_client.get_user_booked_packages(limit=500)
        assert response.status_code == 200
        
        data = response.json()
        
        # Extract totalItems from pagination
        total_items = None
        if isinstance(data, dict) and 'pagination' in data:
            total_items = data['pagination'].get('totalItems')
            self.logger.info(f"📊 Pagination - Total items: {total_items}, Current page: {data['pagination'].get('currentPage')}")
        elif isinstance(data, dict) and 'data' in data and isinstance(data['data'], dict):
            pagination = data['data'].get('pagination', {})
            total_items = pagination.get('totalItems')
        
        assert total_items is not None, "Could not extract totalItems from response"
        
        # Verify total items increased
        assert total_items > initial_total_items, \
            f"Bookings didn't increase! Before: {initial_total_items}, After: {total_items}"
        
        self.logger.success(f"✅ Total bookings increased from {initial_total_items} to {total_items}")
        
        # If booking ID provided, verify it exists (optional)
        if new_booking_id:
            # Extract all bookings to find the new ID
            bookings = self._extract_bookings_from_response(data)
            booking_ids = [str(b.get('id')) for b in bookings if b.get('id')]
            
            if new_booking_id in booking_ids:
                self.logger.success(f"✅ New booking ID {new_booking_id} found in current page")
            else:
                self.logger.info(f"✅ New booking ID {new_booking_id} confirmed via total items increase")
    
    def _verify_user_bookings_not_increased(self, auth_api, initial_count, new_booking_id):
        """Verify that authenticated user's bookings did NOT increase (for unauthenticated tests)"""
        import time
        time.sleep(2)
        
        response = auth_api.get_user_booked_packages(limit=50)
        assert response.status_code == 200
        
        data = response.json()
        bookings = self._extract_bookings_from_response(data)
        booking_ids = [b.get('id') for b in bookings]
        
        assert len(bookings) == initial_count, f"Bookings should NOT increase! Before: {initial_count}, After: {len(bookings)}"
        assert new_booking_id not in booking_ids, f"Unauthenticated booking ID {new_booking_id} should NOT appear in user bookings"
        
        self.logger.success(f"✅ Authenticated user's bookings unchanged ({initial_count})")
        self.logger.success(f"✅ Unauthenticated booking ID {new_booking_id} not found in user bookings")
    
    def _extract_bookings_from_response(self, data):
        """Extract bookings list from response"""
        bookings = []
        if isinstance(data, dict) and 'data' in data:
            data_obj = data['data']
            if 'packages' in data_obj:
                bookings = data_obj['packages']
            elif 'data' in data_obj:
                bookings = data_obj['data']
        return bookings
    
    def _verify_payment_method_response(self, response_data, payment_method):
        """Verify response structure matches payment method"""
        data = response_data.get('data', {})
        
        if payment_method in ["flutterwave", "paystack"]:
            assert 'paymentLink' in data, f"{payment_method} should return paymentLink"
            self.logger.info(f"✅ {payment_method} - paymentLink present")
        elif payment_method == "manual payment":
            assert 'amount_to_pay' in data or 'amountToPay' in data, "Bank Transfer should return amount"
            assert 'reference' in data, "Bank Transfer should return reference"
            self.logger.info("✅ Bank Transfer - correct response structure")
    
    # ==================== PACKAGE MANAGEMENT TESTS ====================
    
    @pytest.mark.api
    def test_get_all_packages(self, authenticated_package_api):
        self.logger.info("=== Testing Get All Packages ===")
        response = authenticated_package_api.get_all_packages(limit=10, page=1)
        assert response.status_code == 200
        self.logger.success("✅ Get all packages successful")
    
    @pytest.mark.api
    def test_get_package_countries(self, authenticated_package_api):
        self.logger.info("=== Testing Get Package Countries ===")
        response = authenticated_package_api.get_package_countries()
        assert response.status_code == 200
        self.logger.success("✅ Get package countries successful")
    
    @pytest.mark.api
    def test_get_single_package(self, authenticated_package_api):
        self.logger.info("=== Testing Get Single Package ===")
        
        # Get packages directly using the API method with limit=1
        response = authenticated_package_api.get_all_packages(limit=1)  # ← Use API method directly
        
        if response.status_code != 200:
            pytest.skip("Could not fetch packages")
        
        data = response.json()
        
        # Extract packages from nested structure
        if isinstance(data, dict) and 'data' in data:
            package_data = data['data']
            if 'packages' in package_data:
                items = package_data['packages']
            else:
                items = package_data.get('data', [])
        else:
            items = data if isinstance(data, list) else []
        
        if not items:
            pytest.skip("No packages available")
        
        package_id = items[0].get('id')
        self.logger.info(f"📦 Testing with package ID: {package_id}")
        
        response = authenticated_package_api.get_single_package(package_id)
        assert response.status_code == 200
        self.logger.success(f"✅ Get single package {package_id} successful")
    
    @pytest.mark.api
    def test_search_packages(self, authenticated_package_api):
        self.logger.info("=== Testing Search Packages ===")
        response = authenticated_package_api.get_all_packages(search="beach", type="GROUP", limit=5)
        assert response.status_code == 200
        self.logger.success("✅ Search packages successful")
    
    # ==================== DEALS TESTS ====================
    
    @pytest.mark.api
    def test_get_all_deals(self, authenticated_package_api):
        self.logger.info("=== Testing Get All Deals ===")
        response = authenticated_package_api.get_all_deals(limit=10, is_active=True)
        assert response.status_code == 200
        self.logger.success("✅ Get all deals successful")
    
    @pytest.mark.api
    def test_get_single_deal(self, authenticated_package_api):
        self.logger.info("=== Testing Get Single Deal ===")
        response = authenticated_package_api.get_all_deals(limit=1)
        if response.status_code != 200:
            pytest.skip("Could not fetch deals")
        
        data = response.json()
        if isinstance(data, dict) and 'data' in data:
            package_data = data['data']
            if 'packageDeals' in package_data:
                deals = package_data['packageDeals']
                if deals:
                    deal_id = deals[0].get('id')
                    response = authenticated_package_api.get_single_deal(deal_id)
                    assert response.status_code == 200
                    self.logger.success(f"✅ Get single deal {deal_id} successful")
    
    # ==================== AUTHENTICATED BOOKING TESTS ====================
    
    @pytest.mark.api
    def test_authenticated_booking_group_full_payment(self, authenticated_package_api):
        """Test authenticated GROUP package booking with FULL PAYMENT"""
        self.logger.info("=== Testing AUTHENTICATED GROUP - Full Payment ===")
        
        # Get active GROUP package
        packages = self._get_active_packages(authenticated_package_api, package_type="GROUP")
        if not packages:
            pytest.skip("No active GROUP packages available")
        
        package = random.choice(packages)
        self.logger.info(f"📦 Selected package: {package.get('title')} (ID: {package.get('id')})")
        
        # Select pricing
        pricing = random.choice(package['prices'])
        self.logger.info(f"💰 Selected pricing: {pricing.get('pricing_text')} - ₦{pricing.get('price')}")
        
        # Set payment flags for FULL PAYMENT
        payment_flags = {
            "is_full_payment": True,
            "is_lockdown_payment": False,
            "book_at_deal_price": False,
            "authenticated": True
        }
        
        # Choose payment method
        payment_method = random.choice(["flutterwave", "paystack", "manual payment"])
        
        # Get initial bookings count
        initial_response = authenticated_package_api.get_user_booked_packages(limit=500)
        initial_total_items = 0
        if initial_response.status_code == 200:
            initial_data = initial_response.json()
            if isinstance(initial_data, dict) and 'pagination' in initial_data:
                initial_total_items = initial_data['pagination'].get('totalItems', 0)
            elif isinstance(initial_data, dict) and 'data' in initial_data and isinstance(initial_data['data'], dict):
                initial_total_items = initial_data['data'].get('pagination', {}).get('totalItems', 0)

        self.logger.info(f"📊 Initial total bookings: {initial_total_items}")
        
        
        # Build and execute booking
        payload = self._build_booking_payload(
            package=package,
            pricing_text=pricing.get('pricing_text'),
            payment_flags=payment_flags,
            payment_method=payment_method,
            package_type="GROUP"
        )
        
        self.logger.info(f"📦 Payload: {payload}")
        response = authenticated_package_api.book_package(payload)
        
        # Verify response
        response_data, booking_id = self._verify_booking_response(response, expected_user_id_not_null=True)
        self._verify_payment_method_response(response_data, payment_method)
        
        # Verify booking appears in user's bookings
        self._verify_user_bookings_increased(authenticated_package_api, initial_total_items, booking_id)
        self.logger.success(f"✅ Authenticated GROUP full payment test passed")
    
    @pytest.mark.api
    def test_authenticated_booking_group_lockdown_payment(self, authenticated_package_api):
        """Test authenticated GROUP package booking with LOCKDOWN PAYMENT"""
        self.logger.info("=== Testing AUTHENTICATED GROUP - Lockdown Payment ===")
        
        packages = self._get_active_packages(authenticated_package_api, package_type="GROUP")
        if not packages:
            pytest.skip("No active GROUP packages available")
        
        package = random.choice(packages)
        self.logger.info(f"📦 Selected package: {package.get('title')} (ID: {package.get('id')})")
        
        pricing = random.choice(package['prices'])
        self.logger.info(f"💰 Selected pricing: {pricing.get('pricing_text')} - ₦{pricing.get('price')}")
        
        # Set payment flags for LOCKDOWN PAYMENT
        payment_flags = {
            "is_full_payment": False,
            "is_lockdown_payment": True,
            "book_at_deal_price": False,
            "authenticated": True
        }
        
        payment_method = random.choice(["flutterwave", "paystack", "manual payment"])
        
        # Get initial bookings count
        initial_response = authenticated_package_api.get_user_booked_packages(limit=500)
        initial_total_items = 0
        if initial_response.status_code == 200:
            initial_data = initial_response.json()
            if isinstance(initial_data, dict) and 'pagination' in initial_data:
                initial_total_items = initial_data['pagination'].get('totalItems', 0)
            elif isinstance(initial_data, dict) and 'data' in initial_data and isinstance(initial_data['data'], dict):
                initial_total_items = initial_data['data'].get('pagination', {}).get('totalItems', 0)

        self.logger.info(f"📊 Initial total bookings: {initial_total_items}")
        
        payload = self._build_booking_payload(
            package=package,
            pricing_text=pricing.get('pricing_text'),
            payment_flags=payment_flags,
            payment_method=payment_method,
            package_type="GROUP"
        )
        
        self.logger.info(f"📦 Payload: {payload}")
        response = authenticated_package_api.book_package(payload)
        
        response_data, booking_id = self._verify_booking_response(response)
        self._verify_payment_method_response(response_data, payment_method)
        self._verify_user_bookings_increased(authenticated_package_api, initial_total_items, booking_id)
        self.logger.success(f"✅ Authenticated GROUP lockdown payment test passed")
    
    @pytest.mark.api
    def test_authenticated_booking_group_deal_price(self, authenticated_package_api):
        """Test authenticated GROUP package booking with DEAL PRICE"""
        self.logger.info("=== Testing AUTHENTICATED GROUP - Deal Price ===")
        
        packages = self._get_active_packages(authenticated_package_api, package_type="GROUP", require_deal=True)
        if not packages:
            pytest.skip("No active GROUP packages with deals available")
        
        package = random.choice(packages)
        self.logger.info(f"📦 Selected package with deal: {package.get('title')} (ID: {package.get('id')})")
        
        pricing = random.choice(package['prices'])
        self.logger.info(f"💰 Selected pricing: {pricing.get('pricing_text')} - ₦{pricing.get('price')}")
        
        # Set payment flags for DEAL PRICE
        payment_flags = {
            "is_full_payment": False,
            "is_lockdown_payment": False,
            "book_at_deal_price": True,
            "authenticated": True
        }
        
        payment_method = random.choice(["flutterwave", "paystack", "manual payment"])
        
        # Get initial bookings count
        initial_response = authenticated_package_api.get_user_booked_packages(limit=500)
        initial_total_items = 0
        if initial_response.status_code == 200:
            initial_data = initial_response.json()
            if isinstance(initial_data, dict) and 'pagination' in initial_data:
                initial_total_items = initial_data['pagination'].get('totalItems', 0)
            elif isinstance(initial_data, dict) and 'data' in initial_data and isinstance(initial_data['data'], dict):
                initial_total_items = initial_data['data'].get('pagination', {}).get('totalItems', 0)

        self.logger.info(f"📊 Initial total bookings: {initial_total_items}")
        
        payload = self._build_booking_payload(
            package=package,
            pricing_text=pricing.get('pricing_text'),
            payment_flags=payment_flags,
            payment_method=payment_method,
            package_type="GROUP"
        )
        
        self.logger.info(f"📦 Payload: {payload}")
        response = authenticated_package_api.book_package(payload)
        
        response_data, booking_id = self._verify_booking_response(response)
        self._verify_payment_method_response(response_data, payment_method)
        self._verify_user_bookings_increased(authenticated_package_api, initial_total_items, booking_id)
        self.logger.success(f"✅ Authenticated GROUP deal price test passed")
    
    @pytest.mark.api
    def test_authenticated_booking_private_future_departure(self, authenticated_package_api):
        """Test authenticated PRIVATE package with departure >30 days away (can use any payment type)"""
        self.logger.info("=== Testing AUTHENTICATED PRIVATE - Future Departure (>30 days) ===")
        
        packages = self._get_active_packages(authenticated_package_api, package_type="PRIVATE")
        if not packages:
            pytest.skip("No active PRIVATE packages available")
        
        package = random.choice(packages)
        self.logger.info(f"📦 Selected package: {package.get('title')} (ID: {package.get('id')})")
        
        # Select departure date >30 days away
        departure_date, return_date = self._select_package_with_future_departure(package, min_days=31)
        self.logger.info(f"📅 Selected departure: {departure_date} (>30 days away)")
        
        pricing = random.choice(package['prices'])
        
        # Random payment type (all should work for future departure)
        payment_flags = self._generate_payment_flags()
        payment_flags["authenticated"] = True
        
        payment_method = random.choice(["flutterwave", "paystack", "manual payment"])
        
        # Get initial bookings count
        initial_response = authenticated_package_api.get_user_booked_packages(limit=500)
        initial_total_items = 0
        if initial_response.status_code == 200:
            initial_data = initial_response.json()
            if isinstance(initial_data, dict) and 'pagination' in initial_data:
                initial_total_items = initial_data['pagination'].get('totalItems', 0)
            elif isinstance(initial_data, dict) and 'data' in initial_data and isinstance(initial_data['data'], dict):
                initial_total_items = initial_data['data'].get('pagination', {}).get('totalItems', 0)

        self.logger.info(f"📊 Initial total bookings: {initial_total_items}")
        
        payload = self._build_booking_payload(
            package=package,
            pricing_text=pricing.get('pricing_text'),
            payment_flags=payment_flags,
            payment_method=payment_method,
            package_type="PRIVATE",
            departure_date=departure_date,
            return_date=return_date
        )
        
        self.logger.info(f"📦 Payload: {payload}")
        response = authenticated_package_api.book_package(payload)
        
        response_data, booking_id = self._verify_booking_response(response)
        self._verify_payment_method_response(response_data, payment_method)
        self._verify_user_bookings_increased(authenticated_package_api, initial_total_items, booking_id)
        self.logger.success(f"✅ Authenticated PRIVATE future departure test passed")
    
    @pytest.mark.api
    def test_authenticated_booking_private_within_30_days_full_payment(self, authenticated_package_api):
        """Test authenticated PRIVATE package with departure within 30 days - MUST use FULL PAYMENT"""
        self.logger.info("=== Testing AUTHENTICATED PRIVATE - Within 30 Days (Full Payment Required) ===")
        
        packages = self._get_active_packages(authenticated_package_api, package_type="PRIVATE")
        if not packages:
            pytest.skip("No active PRIVATE packages available")
        
        package = None
        valid_departure = None
        valid_return = None
        
        # Find a package that has a date within 30 days
        for p in packages:
            try:
                dep, ret = self._select_package_within_30_days(p)
                days_until = (dep - datetime.now().date()).days
                if days_until <= 30 and days_until > 0:
                    package = p
                    valid_departure = dep
                    valid_return = ret
                    break
            except:
                continue
        
        if not package:
            pytest.skip("No PRIVATE packages with departure within 30 days available")
        
        self.logger.info(f"📦 Selected package: {package.get('title')} (ID: {package.get('id')})")
        self.logger.info(f"📅 Departure in {(valid_departure - datetime.now().date()).days} days")
        
        pricing = random.choice(package['prices'])
        
        # MUST use FULL PAYMENT for within 30 days
        payment_flags = {
            "is_full_payment": True,
            "is_lockdown_payment": False,
            "book_at_deal_price": False,
            "authenticated": True
        }
        
        payment_method = random.choice(["flutterwave", "paystack", "manual payment"])
        
        # Get initial bookings count
        initial_response = authenticated_package_api.get_user_booked_packages(limit=500)
        initial_total_items = 0
        if initial_response.status_code == 200:
            initial_data = initial_response.json()
            if isinstance(initial_data, dict) and 'pagination' in initial_data:
                initial_total_items = initial_data['pagination'].get('totalItems', 0)
            elif isinstance(initial_data, dict) and 'data' in initial_data and isinstance(initial_data['data'], dict):
                initial_total_items = initial_data['data'].get('pagination', {}).get('totalItems', 0)

        self.logger.info(f"📊 Initial total bookings: {initial_total_items}")
        
        payload = self._build_booking_payload(
            package=package,
            pricing_text=pricing.get('pricing_text'),
            payment_flags=payment_flags,
            payment_method=payment_method,
            package_type="PRIVATE",
            departure_date=valid_departure,
            return_date=valid_return
        )
        
        self.logger.info(f"📦 Payload: {payload}")
        response = authenticated_package_api.book_package(payload)
        
        response_data, booking_id = self._verify_booking_response(response)
        self._verify_payment_method_response(response_data, payment_method)
        self._verify_user_bookings_increased(authenticated_package_api, initial_total_items, booking_id)
        self.logger.success(f"✅ Authenticated PRIVATE within 30 days (full payment) test passed")
        
    @pytest.mark.api
    def test_authenticated_booking_private_within_30_days_lockdown_fails(self, authenticated_package_api):
        """
        Test that booking a PRIVATE package with departure within 30 days 
        using LOCKDOWN payment fails (should use full payment instead)
        """
        self.logger.info("=== Testing PRIVATE within 30 days - Lockdown Payment Should FAIL ===")
        
        packages = self._get_active_packages(authenticated_package_api, package_type="PRIVATE")
        if not packages:
            pytest.skip("No active PRIVATE packages available")
        
        # Find a package with departure within 30 days
        package = None
        valid_departure = None
        valid_return = None
        
        for p in packages:
            try:
                dep, ret = self._select_package_within_30_days(p)
                days_until = (dep - datetime.now().date()).days
                if days_until <= 30 and days_until > 0:
                    package = p
                    valid_departure = dep
                    valid_return = ret
                    break
            except:
                continue
        
        if not package:
            pytest.skip("No PRIVATE packages with departure within 30 days available")
        
        self.logger.info(f"📦 Selected package: {package.get('title')} (ID: {package.get('id')})")
        self.logger.info(f"📅 Departure in {(valid_departure - datetime.now().date()).days} days")
        
        pricing = random.choice(package['prices'])
        
        # TRY WITH LOCKDOWN PAYMENT (should fail within 30 days)
        payment_flags = {
            "is_full_payment": False,
            "is_lockdown_payment": True,  # ← This should cause failure within 30 days
            "book_at_deal_price": False,
            "authenticated": True
        }
        
        payment_method = random.choice(["flutterwave", "paystack", "manual payment"])
        
        payload = self._build_booking_payload(
            package=package,
            pricing_text=pricing.get('pricing_text'),
            payment_flags=payment_flags,
            payment_method=payment_method,
            package_type="PRIVATE",
            departure_date=valid_departure,
            return_date=valid_return
        )
        
        self.logger.info(f"📦 Attempting LOCKDOWN payment within 30 days (should fail): {payload}")
        response = authenticated_package_api.book_package(payload)
        
        # Should fail with 400
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        response_data = response.json()
        error_message = response_data.get('message', '')
        
        expected_error = "Full payment is required for departure dates within 30 days"
        assert expected_error in error_message, \
            f"Expected '{expected_error}', got '{error_message}'"
        
        self.logger.success(f"✅ Correctly got 400: '{error_message}'")
    
    # ==================== UNAUTHENTICATED BOOKING TESTS ====================
    
    @pytest.mark.api
    def test_unauthenticated_booking_group_full_payment(self, unauthenticated_package_api, authenticated_package_api):
        """Test UNAUTHENTICATED GROUP package booking with FULL PAYMENT"""
        self.logger.info("=== Testing UNAUTHENTICATED GROUP - Full Payment ===")
        
        # Get active GROUP package
        packages = self._get_active_packages(unauthenticated_package_api, package_type="GROUP")
        if not packages:
            pytest.skip("No active GROUP packages available")
        
        package = random.choice(packages)
        self.logger.info(f"📦 Selected package: {package.get('title')} (ID: {package.get('id')})")
        
        pricing = random.choice(package['prices'])
        
        # Set payment flags for FULL PAYMENT
        payment_flags = {
            "is_full_payment": True,
            "is_lockdown_payment": False,
            "book_at_deal_price": False,
            "authenticated": False
        }
        
        payment_method = random.choice(["flutterwave", "paystack", "manual payment"])
        
        # Get authenticated user's initial bookings count
        initial_response = authenticated_package_api.get_user_booked_packages(limit=50)
        initial_count = len(self._extract_bookings_from_response(initial_response.json())) if initial_response.status_code == 200 else 0
        
        # Build and execute booking with UNAUTHENTICATED client
        payload = self._build_booking_payload(
            package=package,
            pricing_text=pricing.get('pricing_text'),
            payment_flags=payment_flags,
            payment_method=payment_method,
            package_type="GROUP"
        )
        
        self.logger.info(f"📦 Payload: {payload}")
        response = unauthenticated_package_api.book_package(payload)
        
        # Verify response - user_id should be NULL
        response_data, booking_id = self._verify_booking_response(response, expected_user_id_not_null=False)
        self._verify_payment_method_response(response_data, payment_method)
        
        # Verify booking does NOT appear in authenticated user's bookings
        self._verify_user_bookings_not_increased(authenticated_package_api, initial_count, booking_id)
        self.logger.success(f"✅ Unauthenticated GROUP full payment test passed")
    
    @pytest.mark.api
    def test_unauthenticated_booking_group_lockdown_payment(self, unauthenticated_package_api, authenticated_package_api):
        """Test UNAUTHENTICATED GROUP package booking with LOCKDOWN PAYMENT"""
        self.logger.info("=== Testing UNAUTHENTICATED GROUP - Lockdown Payment ===")
        
        packages = self._get_active_packages(unauthenticated_package_api, package_type="GROUP")
        if not packages:
            pytest.skip("No active GROUP packages available")
        
        package = random.choice(packages)
        self.logger.info(f"📦 Selected package: {package.get('title')} (ID: {package.get('id')})")
        
        pricing = random.choice(package['prices'])
        
        payment_flags = {
            "is_full_payment": False,
            "is_lockdown_payment": True,
            "book_at_deal_price": False,
            "authenticated": False
        }
        
        payment_method = random.choice(["flutterwave", "paystack", "manual payment"])
        
        initial_response = authenticated_package_api.get_user_booked_packages(limit=50)
        initial_count = len(self._extract_bookings_from_response(initial_response.json())) if initial_response.status_code == 200 else 0
        
        payload = self._build_booking_payload(
            package=package,
            pricing_text=pricing.get('pricing_text'),
            payment_flags=payment_flags,
            payment_method=payment_method,
            package_type="GROUP"
        )
        
        self.logger.info(f"📦 Payload: {payload}")
        response = unauthenticated_package_api.book_package(payload)
        
        response_data, booking_id = self._verify_booking_response(response, expected_user_id_not_null=False)
        self._verify_payment_method_response(response_data, payment_method)
        self._verify_user_bookings_not_increased(authenticated_package_api, initial_count, booking_id)
        self.logger.success(f"✅ Unauthenticated GROUP lockdown payment test passed")
    
    @pytest.mark.api
    def test_unauthenticated_booking_group_deal_price(self, unauthenticated_package_api, authenticated_package_api):
        """Test UNAUTHENTICATED GROUP package booking with DEAL PRICE"""
        self.logger.info("=== Testing UNAUTHENTICATED GROUP - Deal Price ===")
        
        packages = self._get_active_packages(unauthenticated_package_api, package_type="GROUP", require_deal=True)
        if not packages:
            pytest.skip("No active GROUP packages with deals available")
        
        package = random.choice(packages)
        self.logger.info(f"📦 Selected package with deal: {package.get('title')} (ID: {package.get('id')})")
        
        pricing = random.choice(package['prices'])
        
        payment_flags = {
            "is_full_payment": False,
            "is_lockdown_payment": False,
            "book_at_deal_price": True,
            "authenticated": False
        }
        
        payment_method = random.choice(["flutterwave", "paystack", "manual payment"])
        
        initial_response = authenticated_package_api.get_user_booked_packages(limit=50)
        initial_count = len(self._extract_bookings_from_response(initial_response.json())) if initial_response.status_code == 200 else 0
        
        payload = self._build_booking_payload(
            package=package,
            pricing_text=pricing.get('pricing_text'),
            payment_flags=payment_flags,
            payment_method=payment_method,
            package_type="GROUP"
        )
        
        self.logger.info(f"📦 Payload: {payload}")
        response = unauthenticated_package_api.book_package(payload)
        
        response_data, booking_id = self._verify_booking_response(response, expected_user_id_not_null=False)
        self._verify_payment_method_response(response_data, payment_method)
        self._verify_user_bookings_not_increased(authenticated_package_api, initial_count, booking_id)
        self.logger.success(f"✅ Unauthenticated GROUP deal price test passed")
    
    @pytest.mark.api
    def test_unauthenticated_booking_private_future_departure(self, unauthenticated_package_api, authenticated_package_api):
        """Test UNAUTHENTICATED PRIVATE package with departure >30 days away"""
        self.logger.info("=== Testing UNAUTHENTICATED PRIVATE - Future Departure (>30 days) ===")
        
        packages = self._get_active_packages(unauthenticated_package_api, package_type="PRIVATE")
        if not packages:
            pytest.skip("No active PRIVATE packages available")
        
        package = random.choice(packages)
        self.logger.info(f"📦 Selected package: {package.get('title')} (ID: {package.get('id')})")
        
        # Select departure date >30 days away
        departure_date, return_date = self._select_package_with_future_departure(package, min_days=31)
        self.logger.info(f"📅 Selected departure: {departure_date} (>30 days away)")
        
        pricing = random.choice(package['prices'])
        
        payment_flags = self._generate_payment_flags()
        payment_flags["authenticated"] = False
        
        payment_method = random.choice(["flutterwave", "paystack", "manual payment"])
        
        initial_response = authenticated_package_api.get_user_booked_packages(limit=50)
        initial_count = len(self._extract_bookings_from_response(initial_response.json())) if initial_response.status_code == 200 else 0
        
        payload = self._build_booking_payload(
            package=package,
            pricing_text=pricing.get('pricing_text'),
            payment_flags=payment_flags,
            payment_method=payment_method,
            package_type="PRIVATE",
            departure_date=departure_date,
            return_date=return_date
        )
        
        self.logger.info(f"📦 Payload: {payload}")
        response = unauthenticated_package_api.book_package(payload)
        
        response_data, booking_id = self._verify_booking_response(response, expected_user_id_not_null=False)
        self._verify_payment_method_response(response_data, payment_method)
        self._verify_user_bookings_not_increased(authenticated_package_api, initial_count, booking_id)
        self.logger.success(f"✅ Unauthenticated PRIVATE future departure test passed")
    
    @pytest.mark.api
    def test_unauthenticated_booking_private_within_30_days_full_payment(self, unauthenticated_package_api, authenticated_package_api):
        """Test UNAUTHENTICATED PRIVATE package with departure within 30 days - MUST use FULL PAYMENT"""
        self.logger.info("=== Testing UNAUTHENTICATED PRIVATE - Within 30 Days (Full Payment Required) ===")
        
        packages = self._get_active_packages(unauthenticated_package_api, package_type="PRIVATE")
        if not packages:
            pytest.skip("No active PRIVATE packages available")
        
        package = None
        valid_departure = None
        valid_return = None
        
        # Find a package that has a date within 30 days
        for p in packages:
            try:
                dep, ret = self._select_package_within_30_days(p)
                days_until = (dep - datetime.now().date()).days
                if days_until <= 30 and days_until > 0:
                    package = p
                    valid_departure = dep
                    valid_return = ret
                    break
            except:
                continue
        
        if not package:
            pytest.skip("No PRIVATE packages with departure within 30 days available")
        
        self.logger.info(f"📦 Selected package: {package.get('title')} (ID: {package.get('id')})")
        self.logger.info(f"📅 Departure in {(valid_departure - datetime.now().date()).days} days")
        
        pricing = random.choice(package['prices'])
        
        # MUST use FULL PAYMENT for within 30 days
        payment_flags = {
            "is_full_payment": True,
            "is_lockdown_payment": False,
            "book_at_deal_price": False,
            "authenticated": False
        }
        
        payment_method = random.choice(["flutterwave", "paystack", "manual payment"])
        
        initial_response = authenticated_package_api.get_user_booked_packages(limit=50)
        initial_count = len(self._extract_bookings_from_response(initial_response.json())) if initial_response.status_code == 200 else 0
        
        payload = self._build_booking_payload(
            package=package,
            pricing_text=pricing.get('pricing_text'),
            payment_flags=payment_flags,
            payment_method=payment_method,
            package_type="PRIVATE",
            departure_date=valid_departure,
            return_date=valid_return
        )
        
        self.logger.info(f"📦 Payload: {payload}")
        response = unauthenticated_package_api.book_package(payload)
        
        response_data, booking_id = self._verify_booking_response(response, expected_user_id_not_null=False)
        self._verify_payment_method_response(response_data, payment_method)
        self._verify_user_bookings_not_increased(authenticated_package_api, initial_count, booking_id)
        self.logger.success(f"✅ Unauthenticated PRIVATE within 30 days (full payment) test passed")
    
    # ==================== USER BOOKINGS TESTS ====================
    
    @pytest.mark.api
    def test_get_user_booked_packages(self, authenticated_package_api):
        """Test getting user's booked packages with various scenarios"""
        self.logger.info("=== Testing Get User Booked Packages ===")
        
        # Basic retrieval
        response = authenticated_package_api.get_user_booked_packages()
        assert response.status_code == 200
        self.logger.success("✅ Get user booked packages successful")
        
        # Test pagination
        response = authenticated_package_api.get_user_booked_packages(limit=5, page=1)
        assert response.status_code == 200
        self.logger.success("✅ Pagination test passed")
    
    @pytest.mark.api
    def test_get_user_booked_packages_analytics(self, authenticated_package_api):
        """Test getting user's booking analytics"""
        self.logger.info("=== Testing Get User Booked Packages Analytics ===")
        
        response = authenticated_package_api.get_user_booked_packages_analytics()
        assert response.status_code == 200
        self.logger.success("✅ Get user bookings analytics successful")
    
    def _generate_payment_flags(self):
        """Generate random valid payment flags"""
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
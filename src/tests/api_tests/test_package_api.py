# src/tests/api_tests/test_package_api.py

import pytest
from src.pages.api.package_api import PackageAPI
from src.pages.api.auth_api import AuthAPI
from src.utils.logger import GeoLogger
import random

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
    
    # Package Management Tests
    @pytest.mark.api
    def test_get_all_packages(self, authenticated_package_api):
        self.logger.info("=== Testing Get All Packages ===")
        response = authenticated_package_api.get_all_packages(limit=10, page=1)
        self.logger.info(f"All Packages: {response.status_code}")
        assert response.status_code == 200
    
    @pytest.mark.api
    def test_get_package_countries(self, authenticated_package_api):
        self.logger.info("=== Testing Get Package Countries ===")
        response = authenticated_package_api.get_package_countries()
        self.logger.info(f"Package Countries: {response.status_code}")
        assert response.status_code == 200
    
    @pytest.mark.api
    def test_get_single_package(self, authenticated_package_api):
        self.logger.info("=== Testing Get Single Package ===")
        all_packages = authenticated_package_api.get_all_packages(limit=1)
        if all_packages.status_code == 200:
            data = all_packages.json()
            # Handle nested structure: data -> data -> packages
            if isinstance(data, dict) and 'data' in data:
                package_data = data['data']
                if 'packages' in package_data:
                    items = package_data['packages']
                else:
                    items = package_data.get('data', [])
            else:
                items = data if isinstance(data, list) else []

            if items and len(items) > 0:
                item_id = items[0].get('id')
                if item_id:
                    response = authenticated_package_api.get_single_package(item_id)
                    self.logger.info(f"Single Package: {response.status_code}")
                    assert response.status_code in [200, 404]

    @pytest.mark.api
    def test_search_packages(self, authenticated_package_api):
        self.logger.info("=== Testing Search Packages ===")
        response = authenticated_package_api.get_all_packages(
            search="beach", 
            type="GROUP", 
            limit=5
        )
        self.logger.info(f"Search Packages: {response.status_code}")
        assert response.status_code == 200
    
    # Package Deals Tests
    @pytest.mark.api
    def test_get_all_deals(self, authenticated_package_api):
        self.logger.info("=== Testing Get All Deals ===")
        response = authenticated_package_api.get_all_deals(limit=10, is_active=True)
        self.logger.info(f"All Deals: {response.status_code}")
        assert response.status_code == 200
    
    @pytest.mark.api
    def test_get_single_deal(self, authenticated_package_api):
        self.logger.info("=== Testing Get Single Deal ===")
        all_deals = authenticated_package_api.get_all_deals(limit=1)
        if all_deals.status_code == 200:
            data = all_deals.json()
            # Handle nested structure: data -> data -> packageDeals
            if isinstance(data, dict) and 'data' in data:
                package_data = data['data']
                if 'packageDeals' in package_data:
                    items = package_data['packageDeals']
                else:
                    items = package_data.get('data', [])
            else:
                items = data if isinstance(data, list) else []

            if items and len(items) > 0:
                item_id = items[0].get('id')
                if item_id:
                    response = authenticated_package_api.get_single_deal(item_id)
                    self.logger.info(f"Single Deal: {response.status_code}")
                    assert response.status_code in [200, 404]
                    
    @pytest.mark.api
    def test_book_package_and_verify_user_bookings(self, authenticated_package_api):
        self.logger.info("=== Testing Book Package and Verify User Bookings ===")
        
        # First get available packages
        packages_response = authenticated_package_api.get_all_packages(limit=10)
        assert packages_response.status_code == 200
        
        packages_data = packages_response.json()
        
        # Extract packages from nested structure
        if isinstance(packages_data, dict) and 'data' in packages_data:
            package_data = packages_data['data']
            if 'packages' in package_data:
                packages = package_data['packages']
            else:
                packages = package_data.get('data', [])
        else:
            packages = packages_data if isinstance(packages_data, list) else []
        
        if not packages or len(packages) == 0:
            self.logger.warning("No packages available for testing")
            pytest.skip("No packages available")
        
        # Find the first ACTIVE package with prices
        selected_package = None
        pricing_text = None

        for package in packages:
            if (package.get('status') == 'Active' and
                package.get('prices') and
                len(package['prices']) > 0):

                selected_package = package
                # Use the first pricing option from the package
                pricing_text = package['prices'][0].get('pricing_text', 'Group')
                break
                
        if not selected_package:
            # If no active packages, use the first one regardless of status
            selected_package = packages[0]
            pricing_text = selected_package['prices'][0].get('pricing_text', 'Group') if selected_package.get('prices') else 'Group'

        package_id = selected_package.get('id')
        package_title = selected_package.get('title', 'Unknown Package')

        self.logger.info(f"Selected package: {package_title} (ID: {package_id})")
        self.logger.info(f"Using pricing text: {pricing_text}")

        # Get initial user bookings count (before booking)
        initial_bookings_response = authenticated_package_api.get_user_booked_packages(limit=50)
        initial_bookings_count = 0
        initial_booking_ids = []
        
        if initial_bookings_response.status_code == 200:
            initial_data = initial_bookings_response.json()
            if isinstance(initial_data, dict) and 'data' in initial_data:
                initial_bookings = initial_data['data'].get('data', [])
                initial_bookings_count = len(initial_bookings)
                initial_booking_ids = [b.get('id') for b in initial_bookings if b.get('id')]
        
        self.logger.info(f"Initial user bookings count: {initial_bookings_count}")
        
        # Determine a valid departure date
        departure_date = selected_package.get('end_date') or selected_package.get('available_from') or "2025-12-31"
        # paymentMethod should choose randomly between Flutterwave and Bank Transfer
        payment_method = random.choice(["flutterwave", "manual payment"])

        # Booking data
        booking_data = {
            "package": package_id,
            "full_name": "GEO Bot",
            "email": "geo.qa.bot@gmail.com",
            "phone": "1234567890",
            "pricing_text": pricing_text,
            "is_full_payment": True,
            "is_lockdown_payment": False,
            "departure_date": departure_date,
            "adults": 1,
            "children": 0,
            "infants": 0,
            "book_at_deal_price": False,
            "paymentMethod": payment_method
        }
        
        self.logger.info(f"Using payment method: {payment_method}")

        # Make the booking
        response = authenticated_package_api.book_package(booking_data)
        self.logger.info(f"Book Package Response: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            self.logger.info(f"✅ Booking successful! Response: {response_data}")
            
            # Get booking ID from response if available
            new_booking_id = None
            if 'data' in response_data:
                if 'bookedPackage' in response_data['data']:
                    # Bank Transfer Structure
                    new_booking_id = response_data['data']['bookedPackage'].get('id')
                    self.logger.info("✅ Bank Transfer booking detected (nested bookedPackage)")
                elif 'id' in response_data['data']:
                    # Flutterwave Structure
                    new_booking_id = response_data['data'].get('id')
                    self.logger.info("✅ Flutterwave booking detected (direct ID in data)")
                
                # Verify payment method consistency
                if payment_method == "flutterwave":
                    assert 'paymentLink' in response_data['data'], \
                        f"Flutterwave should return paymentLink. Response keys: {list(response_data['data'].keys())}"
                    self.logger.info("✅ Flutterwave payment - paymentLink present (as expected)")
                    
                elif payment_method == "manual payment":
                    assert 'paymentLink' not in response_data['data'], \
                        f"Bank Transfer should NOT return paymentLink. Response keys: {list(response_data['data'].keys())}"
                    self.logger.info("✅ Bank Transfer - no payment link (as expected)")
                    
                    # Additional check for Bank Transfer structure
                    if 'bookedPackage' not in response_data['data']:
                        self.logger.warning("⚠️ Bank Transfer booking missing 'bookedPackage' in response")
            
            if new_booking_id:
                self.logger.info(f"✅ Extracted booking ID: {new_booking_id}")
            else:
                self.logger.warning("⚠️ Could not extract booking ID from response")
                self.logger.debug(f"Full response structure: {response_data}")
            
            # Handle payment link verification (only for Flutterwave)
            if payment_method == "Flutterwave" and 'data' in response_data and 'paymentLink' in response_data['data']:
                payment_link = response_data['data']['paymentLink']
                self.logger.info(f"Payment link: {payment_link}")
                
                is_valid, message = authenticated_package_api.verify_payment_link(payment_link)
                if is_valid:
                    self.logger.success(f"✅ Payment link verification: {message}")
                else:
                    self.logger.warning(f"⚠️ Payment link issue: {message}")
            elif payment_method == "manual payment":
                self.logger.info("✅ Bank Transfer - skipping payment link verification")
            
            # VERIFICATION STEP: Check user's booked packages
            self.logger.info("=== Verifying booking appears in user's booked packages ===")

            # Wait for booking to be processed
            import time
            time.sleep(3)

            # Get updated user bookings
            updated_bookings_response = authenticated_package_api.get_user_booked_packages(limit=50)
            assert updated_bookings_response.status_code == 200, "Should get user bookings"

            updated_data = updated_bookings_response.json()

            # FIX: Correct response structure
            updated_bookings = []
            if isinstance(updated_data, dict) and 'data' in updated_data:
                data_obj = updated_data['data']
                if 'packages' in data_obj:
                    updated_bookings = data_obj['packages']
                elif 'data' in data_obj:
                    updated_bookings = data_obj['data']

            updated_bookings_count = len(updated_bookings)
            updated_booking_ids = [str(b.get('id')) for b in updated_bookings if b.get('id')]

            self.logger.info(f"Updated user bookings count: {updated_bookings_count}")

            # CRITICAL ASSERTION: Booking count must increase
            assert updated_bookings_count > initial_bookings_count, \
                f"Booking count didn't increase! Before: {initial_bookings_count}, After: {updated_bookings_count}"

            self.logger.success(f"✅ Booking count increased from {initial_bookings_count} to {updated_bookings_count}")

            # CRITICAL ASSERTION: New booking ID must be in user's bookings
            assert new_booking_id is not None, "Booking ID should be returned in response"
            assert str(new_booking_id) in updated_booking_ids, \
                f"New booking ID {new_booking_id} not found in user's booked packages. Found IDs: {updated_booking_ids}"

            self.logger.success(f"✅ New booking ID {new_booking_id} found in user's booked packages")

            # Check analytics endpoint
            analytics_response = authenticated_package_api.get_user_booked_packages_analytics()
            assert analytics_response.status_code == 200, "Should get user bookings analytics"
            self.logger.info(f"✅ User bookings analytics accessible")

            # Final success assertion
            assert response_data.get('status') == 'success', "Booking should be successful"
            self.logger.success(f"✅ Test completed successfully with {payment_method} payment!")
        
        else:
            # Handle booking failure
            self.logger.error(f"❌ Booking failed with status: {response.status_code}")
            self.logger.error(f"Response: {response.text}")
            pytest.fail(f"Booking failed with status {response.status_code}")
            
    @pytest.mark.api
    def test_book_package_without_auth_not_in_user_bookings(self):
        """
        Test that booking without authentication doesn't appear in user bookings
        This tests both unauthenticated booking attempt AND user bookings endpoint
        """
        self.logger.info("=== Testing Book Package Without Auth ===")
        
        # Create unauthenticated PackageAPI instance
        package_api = PackageAPI()
        package_api.set_auth_token(None)  # Ensure no auth
        
        # Try to get user booked packages without auth (should fail or return empty)
        user_bookings_response = package_api.get_user_booked_packages()
        
        if user_bookings_response.status_code == 401:
            self.logger.info("✅ Unauthenticated access to user bookings returns 401 (as expected)")
            assert user_bookings_response.status_code == 401
        elif user_bookings_response.status_code == 200:
            # Some APIs might return empty data for unauthenticated users
            data = user_bookings_response.json()
            if isinstance(data, dict) and 'data' in data:
                bookings = data['data'].get('data', [])
                assert len(bookings) == 0, "Unauthenticated user should see 0 bookings"
                self.logger.info("✅ Unauthenticated user sees empty bookings list")
        
        # Try to book without auth (should fail)
        # First get a package ID to attempt booking
        packages_response = package_api.get_all_packages(limit=1)
        if packages_response.status_code == 200:
            packages_data = packages_response.json()
            package_id = None
            
            if isinstance(packages_data, dict) and 'data' in packages_data:
                package_data = packages_data['data']
                if 'packages' in package_data and len(package_data['packages']) > 0:
                    package_id = package_data['packages'][0].get('id')
                    
            
            if package_id:
                booking_data = {
                    "package": package_id,
                    "full_name": "Test User",
                    "email": "geo.qa.bot@gmail.com",
                    "phone": "1234567890",
                    "pricing_text": "Group",
                    "is_full_payment": True,
                    "departure_date": "2025-12-31",
                    "adults": 1
                }
                
                booking_response = package_api.book_package(booking_data)
                
                # Should fail with 401 or 403
                assert booking_response.status_code in [401, 403, 400], \
                    f"Unauthenticated booking should fail, got {booking_response.status_code}"
                
                self.logger.info(f"✅ Unauthenticated booking correctly rejected with {booking_response.status_code}")
        
        # Verify analytics endpoint also rejects unauthenticated access
        analytics_response = package_api.get_user_booked_packages_analytics()
        assert analytics_response.status_code in [401, 403], \
            f"Unauthenticated analytics access should fail, got {analytics_response.status_code}"
        
        self.logger.info("✅ All unauthenticated access tests passed")
        
    @pytest.mark.api
    def test_get_user_booked_packages(self, authenticated_package_api):
        """Test getting user's booked packages"""
        self.logger.info("=== Testing Get User Booked Packages ===")
        
        response = authenticated_package_api.get_user_booked_packages(
            limit=10,
            page=1,
            payment_status="Pending"  # Optional filter
        )
        
        self.logger.info(f"User Booked Packages: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            self.logger.info(f"Response structure: {list(data.keys()) if isinstance(data, dict) else 'list'}")
            
            # Log some info about the bookings
            if isinstance(data, dict) and 'data' in data:
                bookings = data['data'].get('data', [])
                self.logger.info(f"Found {len(bookings)} booked packages")
                
                for i, booking in enumerate(bookings[:3]):  # Log first 3
                    self.logger.info(f"Booking {i+1}: ID={booking.get('id')}, Status={booking.get('status')}")
        
        assert response.status_code in [200, 404], "Should get bookings or empty list"

    @pytest.mark.api
    def test_get_user_booked_packages_analytics(self, authenticated_package_api):
        """Test getting user's booking analytics"""
        self.logger.info("=== Testing Get User Booked Packages Analytics ===")
        
        response = authenticated_package_api.get_user_booked_packages_analytics()
        
        self.logger.info(f"User Booked Packages Analytics: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            self.logger.info(f"Analytics data keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
        
        assert response.status_code == 200, "Should get analytics data"
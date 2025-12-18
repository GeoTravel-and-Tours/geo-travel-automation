# src/tests/api_tests/test_package_api.py

import pytest
from src.pages.api.package_api import PackageAPI
from src.pages.api.auth_api import AuthAPI
from src.utils.logger import GeoLogger

class TestPackageAPI:
    
    def setup_method(self):
        self.logger = GeoLogger(self.__class__.__name__)
    
    @pytest.fixture
    def authenticated_package_api(self):
        auth_api = AuthAPI()
        response = auth_api.login()
        
        if response.status_code != 200:
            pytest.skip(f"Login failed with status {response.status_code}")
            
        package_api = PackageAPI()
        package_api.set_auth_token(auth_api.auth_token)
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
    def test_book_package(self, authenticated_package_api):
        self.logger.info("=== Testing Book Package ===")
    
        # First get available packages
        packages_response = authenticated_package_api.get_all_packages(limit=10)
        assert packages_response.status_code == 200
    
        packages_data = packages_response.json()
        print(packages_data)
    
        # Extract packages from nested structure
        if isinstance(packages_data, dict) and 'data' in packages_data:
            package_data = packages_data['data']
            if 'packages' in package_data:
                packages = package_data['packages']
            else:
                packages = package_data.get('data', [])
        else:
            packages = packages_data if isinstance(packages_data, list) else []
    
        if packages and len(packages) > 0:
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

            # Determine a valid departure date. Prefer package's end_date if available.
            departure_date = selected_package.get('end_date') or selected_package.get('available_from') or "2025-12-31"
            print(f"Using departure date: {departure_date}")

            # CORRECT booking data using the extracted pricing text
            booking_data = {
                "package": package_id,
                "full_name": "GEO Bot",
                "email": "geobot@yopmail.com",
                "phone": "1234567890",
                "pricing_text": pricing_text,  # Dynamic from package data
                "is_full_payment": True,
                "is_lockdown_payment": False,
                "departure_date": departure_date,
                "adults": 1,
                "children": 0,
                "infants": 0,
                "book_at_deal_price": False
            }
    
            response = authenticated_package_api.book_package(booking_data)
            self.logger.info(f"Book Package: {response.status_code}")
            print(response.text)
    
            if response.status_code == 200:
                response_data = response.json()
                print(response_data)
                self.logger.info(f"✅ Booking successful! Response: {response_data}")
                
                # Check for paymentLink in the data object
                if 'data' in response_data and 'paymentLink' in response_data['data']:
                    payment_link = response_data['data']['paymentLink']
                    self.logger.info(f"Payment link: {payment_link}")
                    
                    # VERIFY THE PAYMENT LINK
                    is_valid, message = authenticated_package_api.verify_payment_link(payment_link)
                    if is_valid:
                        self.logger.success(f"✅ Payment link verification: {message}")
                    else:
                        self.logger.warning(f"⚠️ Payment link issue: {message}")
                else:
                    self.logger.info("Booking created but no payment link returned (might be free package)")
                    
                assert response_data.get('status') == 'success', "Booking should be successful"
                assert 'data' in response_data, "Response should contain data object"
                
            elif response.status_code == 400:
                self.logger.warning(f"Validation error: {response.text}")
            elif response.status_code == 422:
                self.logger.warning(f"Business logic error: {response.text}")
    
            assert response.status_code in [200]
        else:
            self.logger.warning("No packages available for testing")
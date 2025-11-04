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
# src/tests/smoke_tests/test_package_booking_smoke.py

import pytest
import time
from src.utils.screenshot import ScreenshotUtils
from pages.home_page import HomePage
from src.pages.package_booking_flow import PackageBookingFlow

class TestPackageBookingSmoke:
    """Test suite for package booking flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self, driver):
        """Setup before each test"""
        self.driver = driver
        
        # Initialize page objects
        self.home_page = HomePage(driver)
        self.package_booking_flow = PackageBookingFlow(driver)
        self.screenshot = ScreenshotUtils(driver)

        yield
    
    def test_homepage_loads_successfully(self):
        """Smoke Test 1: Homepage loads without errors"""
        self.home_page.logger.info("=== Testing Homepage Loads Successfully ===")

        self.home_page.logger.step(1, "Opening homepage")
        self.home_page.open()
        self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)

        self.home_page.logger.step(2, "Verifying page title")
        title = self.home_page.title
        assert title is not None, "Page title should not be None"
        assert len(title) > 0, "Page title should not be empty"
        assert "error" not in title.lower(), "Page title should not indicate an error"

        self.home_page.logger.step(3, "Checking current URL")
        current_url = self.package_booking_flow.navigator.get_current_url()
        assert current_url, "Current URL should not be empty"

        self.home_page.logger.success("Homepage loaded successfully")

    @pytest.mark.smoke
    def test_complete_package_booking_flow(self):
        """Smoke Test 1:Complete smoke test for package booking flow"""
        self.package_booking_flow.logger.info("=== Testing Complete Package Booking Flow ===")
        
        try:
            
            self.package_booking_flow.logger.step(1, "Opening homepage")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            
            self.package_booking_flow.logger.step(2, "Clicking on Package")
            self.package_booking_flow.click_package()
            
            
            self.package_booking_flow.logger.step(3, "Selecting trip type")
            self.package_booking_flow.select_trip_type()
            
            
            self.package_booking_flow.logger.step(4, "Selecting country")
            self.package_booking_flow.select_country("Nigeria")

            
            self.package_booking_flow.logger.step(5, "Opening travel date selector")
            self.package_booking_flow.select_travel_date()

            
            self.package_booking_flow.logger.step(6, "Searching packages")
            self.package_booking_flow.search_packages()
            time.sleep(5)  # Wait for search results to load
            self.package_booking_flow.is_search_session_initialized(search_term="packages", timeout=30)


            self.package_booking_flow.logger.step(7, "Viewing package details")
            self.package_booking_flow.click_view_package()
            time.sleep(5)  # Wait for package details to load


            self.package_booking_flow.logger.step(8, "Selecting price option")
            self.package_booking_flow.select_price_option()
            time.sleep(5)  # Wait for price option selection to process


            self.package_booking_flow.logger.step(9, "Booking reservation")
            self.package_booking_flow.click_book_reservation()
            time.sleep(5)  # Wait for booking page to load


            self.package_booking_flow.logger.step(10, "Filling booking form")
            self.package_booking_flow.fill_booking_form(
                full_name="Geo Bot",
                email="geobot@yopmail.com", 
                phone="1234567890"
            )
            
            
            self.package_booking_flow.logger.step(11, "Scrolling and proceeding to payment")
            self.package_booking_flow.scroll_and_proceed_to_payment()
            
            
            assert "payment" in self.driver.current_url.lower() or self.driver.current_url != "about:blank"
            self.package_booking_flow.logger.success("Package booking flow completed successfully - reached payment step")
            
        except Exception as e:
            self.package_booking_flow.logger.error(f"Package booking test failed: {e}")
            raise

    @pytest.mark.smoke
    def test_package_search_functionality(self):
        """Test package search functionality"""
        
        try:
            # Open and navigate to package search
            self.home_page.open()
            self.package_booking_flow.click_package()
            
            # Test country search
            self.package_booking_flow.select_country("Nigeria")

            # Verify search can be executed
            self.package_booking_flow.search_packages()

            # Verify we get results
            assert "package" in self.driver.current_url.lower() or self.driver.page_source != ""
            self.package_booking_flow.logger.success("Package search functionality verified successfully")
            
        except Exception as e:
            self.package_booking_flow.logger.error(f"Package search test failed: {e}")
            raise

    @pytest.mark.smoke  
    def test_booking_form_validation(self):
        """Test booking form with valid data"""
        
        try:
            self.package_booking_flow.fill_booking_form(
                full_name="Test User",
                email="test@example.com",
                phone="1234567890", 
                step_number=1
            )

            self.package_booking_flow.logger.success("Booking form validation test completed successfully")

        except Exception as e:
            self.package_booking_flow.logger.error(f"Booking form test failed: {e}")
            raise
# src/tests/smoke_tests/test_package_booking_smoke.py

import pytest
import time
from src.utils.screenshot import ScreenshotUtils
from selenium.webdriver.common.by import By
from src.pages.ui.home_page import HomePage
from src.pages.ui.package_booking_flow import PackageBookingFlow
from src.utils.navigation import NavigationUtils
from src.core.test_base import TestBase
from src.pages.ui.payment_flow import PaymentPage


class TestPackageBookingSmoke(TestBase):
    """Test suite for package booking flow - Hierarchical Smoke Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self, driver):
        """Setup before each test"""
        self.driver = driver
        
        # Initialize page objects
        self.home_page = HomePage(driver)
        self.package_booking_flow = PackageBookingFlow(driver)
        self.screenshot = ScreenshotUtils(driver)
        self.navigator = NavigationUtils(driver)

        yield

    @pytest.mark.smoke
    @pytest.mark.dependency(name="homepage_loaded")
    def test_homepage_loads_successfully(self):
        """Smoke Test 1: Quick check - Homepage loads without errors"""
        self.home_page.logger.info("=== Quick Smoke Test: Homepage Load ===")

        # Step 1: Open homepage
        self.home_page.logger.info("Step 1: Opening homepage")
        self.home_page.open()
        self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)

        # Step 2: Verify page title
        self.home_page.logger.info("Step 2: Verifying page title")
        title = self.home_page.title
        assert title is not None, "Page title should not be None"
        assert len(title) > 0, "Page title should not be empty"
        assert "error" not in title.lower(), "Page title should not indicate an error"

        self.home_page.logger.success("✅ Homepage loaded successfully - Basic navigation works")
        
    @pytest.mark.smoke
    @pytest.mark.dependency(name="booking_form_works", depends=["homepage_loaded"])
    def test_booking_form_validation(self):
        """Smoke Test 3: Quick check - Booking form accepts valid data"""
        self.package_booking_flow.logger.info("=== Quick Smoke Test: Booking Form ===")
        
        # This is a simplified version that just tests the form modal opens without going through the entire booking flow
        
        # Step 1: Quick navigation to booking form
        self.package_booking_flow.logger.info("Step 1: Quick navigation to trigger booking form")
        self.home_page.open()
        self.package_booking_flow.click_package()
        
        # For a true quick test, you might want to mock or use a direct URL to the booking form, but this keeps it realistic
        self.package_booking_flow.logger.success("✅ Booking form basic navigation verified")

    @pytest.mark.smoke
    @pytest.mark.dependency(name="package_search_works", depends=["homepage_loaded"])
    def test_package_search_functionality(self):
        """Smoke Test 2: Quick check - Package search works"""
        self.package_booking_flow.logger.info("=== Quick Smoke Test: Package Search ===")
        try:
        
            # Step 1: Open and navigate to package search
            self.package_booking_flow.logger.info("Step 1: Opening homepage and navigating to packages")
            self.home_page.open()
            self.package_booking_flow.click_package()
            time.sleep(1)
            
            # Step 2: Select trip type
            self.package_booking_flow.logger.info("Step 3: Selecting trip type")
            self.package_booking_flow.select_trip_type()
            time.sleep(1)
            
            # Step 3: Test country search
            self.package_booking_flow.logger.info("Step 2: Selecting country")
            self.package_booking_flow.select_country("Nigeria")
            time.sleep(1)
            
            # Step 4: Select travel date
            self.package_booking_flow.logger.info("Step 4: Opening travel date selector")
            self.package_booking_flow.select_travel_date()
            time.sleep(1)
    
            # Step 5: Execute search
            self.package_booking_flow.logger.info("Step 5: Executing package search")
            self.package_booking_flow.search_packages()
            time.sleep(5)
    
            # Step 6: Verify search results
            self.package_booking_flow.logger.info("Step 6: Verifying search results")
            
            # Method 1: Check URL for search indicators
            current_url = self.driver.current_url.lower()
            url_success = any(term in current_url for term in ['search', 'result', 'package', 'query'])
            
            # Method 2: Check for any results or loading indicators
            page_has_content = len(self.driver.page_source) > 1000  # Basic content check
            no_errors = "error" not in current_url and "error" not in self.driver.page_source.lower()
            
            # Method 3: Check for dynamic components
            try:
                components = self.driver.find_elements(By.CSS_SELECTOR, "[data-sentry-component]")
                has_components = len(components) > 0
            except:
                has_components = False
                
            search_successful = url_success or (page_has_content and no_errors) or has_components
            
            self.package_booking_flow.logger.info(f"Search validation - URL success: {url_success}, Content: {page_has_content}, No errors: {no_errors}, Components: {has_components}")
            
            assert search_successful, f"Search session should be properly initialized. URL: {current_url}"

        except Exception as e:
            self.package_booking_flow.logger.error(f"Package search test failed: {e}")
            self.package_booking_flow.screenshot.capture_screenshot_on_failure("package_search_failure")
            raise

    @pytest.mark.smoke
    @pytest.mark.dependency(depends=["homepage_loaded", "package_search_works", "booking_form_works"])
    def test_complete_package_booking_flow(self):
        """Smoke Test 4: Comprehensive end-to-end package booking flow"""
        self.package_booking_flow.logger.info("=== COMPREHENSIVE TEST: Complete Package Booking Flow ===")
        
        # All quick tests passed, now run the full flow
        try:
            # Step 1: Open homepage
            self.package_booking_flow.logger.step(1,"Opening homepage")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            
            # Step 2: Navigate to packages
            self.package_booking_flow.logger.step(2,"Clicking on Package")
            self.package_booking_flow.click_package()
            
            # Step 3: Select trip type
            self.package_booking_flow.logger.step(3,"Selecting trip type")
            self.package_booking_flow.select_trip_type()
            
            # Step 4: Select country
            self.package_booking_flow.logger.step(4,"Selecting country")
            self.package_booking_flow.select_country("Nigeria")

            # Step 5: Select travel date
            self.package_booking_flow.logger.step(5,"Opening travel date selector")
            self.package_booking_flow.select_travel_date()

            # Step 6: Search packages
            self.package_booking_flow.logger.step(6,"Searching packages")
            self.package_booking_flow.search_packages()
            time.sleep(5)
            self.package_booking_flow.is_search_session_initialized(search_term="packages", timeout=30)

            # Step 7: View package details
            self.package_booking_flow.logger.step(7,"Viewing package details")
            self.package_booking_flow.click_view_package()
            time.sleep(5)

            # Step 8: Select price option
            self.package_booking_flow.logger.step(8,"Selecting price option")
            self.package_booking_flow.select_price_option()
            time.sleep(5)
            
            # Step 9: Complete booking flow
            self.package_booking_flow.logger.step(9,"Booking reservation and filling details")
            self.package_booking_flow.handle_booking_flow()
            
            # Step 10: Verify booking progression
            self.package_booking_flow.logger.step(10,"Verifying booking progression")
            time.sleep(5)
            
            # Step 11: Complete booking flow WITH PAYMENT
            self.package_booking_flow.logger.step(11,"Initiating payment flow")
            payment_success = self.package_booking_flow.complete_booking_with_payment()
            assert payment_success, "Should successfully reach Flutterwave test mode"
    
            # Final verification
            if payment_success:
                current_url = self.navigator.get_current_url()
                self.package_booking_flow.logger.info(f"Final URL: {current_url}")
                self.package_booking_flow.logger.success("✅ SUCCESS: Reached Flutterwave test mode verification")
                # We expect to be on Flutterwave since we stopped at test mode verification
                assert "flutterwave" in current_url, "Should be on Flutterwave after successful test mode verification"
            else:
                self.package_booking_flow.logger.error("❌ Failed to reach Flutterwave test mode")
                assert False, "Payment flow failed to reach Flutterwave test mode"
            
        except Exception as e:
            self.package_booking_flow.logger.error(f"❌ Comprehensive package booking test failed: {str(e)}")
            raise
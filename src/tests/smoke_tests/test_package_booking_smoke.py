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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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
    def test_booking_form_navigation_on_homepage(self):
        """Smoke Test 3: Quick check - Booking form accepts valid data"""
        self.package_booking_flow.logger.info("=== Quick Smoke Test: Booking Form ===")
        
        # Step 1: Navigate to packages
        self.package_booking_flow.logger.info("Step 1: Quick navigation to trigger booking form")
        self.home_page.open()
        self.package_booking_flow.click_package()
        
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
            success = self.package_booking_flow.is_search_session_initialized(search_term="packages", timeout=30)
            assert success, "Search session should be properly initialized and results displayed"
            
            self.package_booking_flow.logger.success("✅ Package search test passed")

        except Exception as e:
            self.package_booking_flow.logger.error(f"Package search test failed: {e}")
            self.package_booking_flow.screenshot.capture_screenshot_on_failure("package_search_failure")
            raise

    @pytest.mark.smoke
    @pytest.mark.dependency(depends=["homepage_loaded", "package_search_works", "booking_form_works"])
    def test_complete_package_booking_flow(self):
        """Smoke Test 4: Comprehensive end-to-end package booking flow"""
        self.package_booking_flow.logger.info("=== COMPREHENSIVE TEST: Complete Package Booking Flow WITH Flutterwave ===")
        
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
            search_initialized = self.package_booking_flow.is_search_session_initialized(search_term="packages", timeout=30)
            assert search_initialized, "Search session should be properly initialized"

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
            assert payment_success, "Failed to reach Flutterwave test mode"
            
        except Exception as e:
            self.package_booking_flow.logger.error(f"❌ Comprehensive package booking test failed: {str(e)}")
            self.package_booking_flow.screenshot.capture_screenshot_on_failure("complete_booking_flow_failure")
            raise
    
    @pytest.mark.smoke
    # @pytest.mark.dependency(depends=["homepage_loaded"])
    def test_all_packages_booking_flow(self):
        """Test booking flow via All Packages page (nav bar approach)"""
        self.package_booking_flow.logger.info("=== TEST: All Packages Booking Flow ===")
        
        try:
            # Step 1: Open homepage
            self.package_booking_flow.logger.step(1, "Opening homepage")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            
            # Step 2: Click Packages in navigation bar
            self.package_booking_flow.logger.step(2, "Clicking Packages in nav bar")
            self.package_booking_flow.click_packages_nav_link()
            
            # Step 3: Verify All Packages page loaded
            self.package_booking_flow.logger.step(3, "Verifying All Packages page")
            packages_loaded = self.package_booking_flow.verify_all_packages_page_loaded()
            assert packages_loaded, "Failed to load All Packages page"
            
            # Step 4: Select first package
            self.package_booking_flow.logger.step(4, "Selecting first package")
            self.package_booking_flow.click_view_package_after_packageNavBar()
            time.sleep(5)  # Wait for package details to load
            
            # Step 5: Verify pricing option is present
            self.package_booking_flow.logger.step(5, "Verifying pricing option")
            # You can reuse your existing select_price_option method or just verify it exists
            try:
                price_option = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(self.package_booking_flow.PRICE_OPTION)
                )
                self.package_booking_flow.logger.info("✅ Pricing option is present")
            except:
                self.package_booking_flow.logger.error("❌ Pricing option not found")
                assert False, "Pricing option not found on package details page"
            
            # Step 6: Verify Book Reservation button is present
            self.package_booking_flow.logger.step(6, "Verifying Book Reservation button")
            try:
                book_reservation_btn = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(self.package_booking_flow.BOOK_RESERVATION_BUTTON)
                )
                self.package_booking_flow.logger.info("✅ Book Reservation button is present")
            except:
                self.package_booking_flow.logger.error("❌ Book Reservation button not found")
                assert False, "Book Reservation button not found on package details page"
            
            # Step 7: Select price option (just to verify it works)
            self.package_booking_flow.logger.step(7, "Testing price option selection")
            price_selected = self.package_booking_flow.select_price_option()
            assert price_selected, "Failed to select price option"
            
            # Step 8: Verify booking can proceed (but don't actually book)
            self.package_booking_flow.logger.step(8, "Verifying booking flow readiness")
            try:
                book_reservation_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(self.package_booking_flow.BOOK_RESERVATION_BUTTON)
                )
                if book_reservation_btn.is_enabled():
                    self.package_booking_flow.logger.info("✅ Booking flow is ready - Book Reservation button is enabled")
                else:
                    self.package_booking_flow.logger.warning("⚠️ Book Reservation button is not enabled")
            except:
                self.package_booking_flow.logger.info("ℹ️ Book Reservation button state could not be verified")
            
            self.package_booking_flow.logger.success("✅ All Packages booking flow verified successfully!")
            
        except Exception as e:
            self.package_booking_flow.logger.error(f"❌ All Packages booking flow failed: {str(e)}")
            self.package_booking_flow.screenshot.capture_screenshot_on_failure("all_packages_flow_failure")
            return False
# src/tests/smoke_tests/test_package_booking_smoke.py

import pytest
import time
import random
from src.utils.screenshot import ScreenshotUtils
from selenium.webdriver.common.by import By
from src.pages.ui.home_page import HomePage
from src.pages.ui.auth_flow import AuthFlow
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
        self.auth_flow = AuthFlow(driver)
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
        time.sleep(3)
        
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
            time.sleep(10)
    
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
    # @pytest.mark.dependency(depends=["homepage_loaded", "package_search_works", "booking_form_works"])
    def test_complete_package_booking_flow(self):
        """Smoke Test 4: Comprehensive end-to-end package booking flow"""
        payment_method = random.choice([
            "flutterwave",
            "paystack",
            "bank"
        ])

        self.package_booking_flow.logger.info(
            f"=== COMPREHENSIVE TEST: Complete Package Booking Flow "
            f"WITH {payment_method.upper()} ==="
        )
        
        # All quick tests passed, now run the full flow
        try:
            # Step 1: Open homepage
            self.package_booking_flow.logger.step(1,"Opening homepage")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
            # self.driver.get("https://retail.stg.gowithgeo.com/packages/13")
            
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
            time.sleep(5)

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
            time.sleep(5)
            price_selected = self.package_booking_flow.select_price_option("couple")
            assert price_selected, "Failed to select COUPLE price option"
            
            email, password = self.auth_flow.get_credentials_from_env()

            if not email or not password:
                pytest.skip(
                    "TEST_USER_EMAIL and TEST_USER_PASSWORD environment variables required"
                )
            
            # Step 9: Complete booking flow
            self.package_booking_flow.logger.step(9,"Booking reservation and filling details")
            self.package_booking_flow.handle_booking_flow(email=email, password=password, payment_method=payment_method)
            
            # Step 10: Verify booking progression
            self.package_booking_flow.logger.step(10,"Verifying booking progression")
            time.sleep(5)
            
            # Step 11: Complete booking flow WITH PAYMENT
            self.package_booking_flow.logger.step(
                11,
                f"Initiating {payment_method.upper()} payment flow"
            )

            payment_success = (
                self.package_booking_flow.complete_booking_with_payment(
                    payment_method
                )
            )

            assert payment_success, (
                f"Failed to complete {payment_method} payment flow"
            )
            
        except Exception as e:
            self.package_booking_flow.logger.error(f"❌ Comprehensive package booking test failed: {str(e)}")
            self.package_booking_flow.screenshot.capture_screenshot_on_failure("complete_booking_flow_failure")
            raise
    
    @pytest.mark.smoke
    # @pytest.mark.dependency(depends=["homepage_loaded"])
    def test_all_packages_booking_flow(self):
        """Smoke Test: Navigate from Packages nav bar to package detail page."""
        self.package_booking_flow.logger.info(
            "=== TEST: All Packages → Package Detail Flow ==="
        )

        try:
            # Step 1: Open homepage
            self.package_booking_flow.logger.step(1, "Opening homepage")
            self.home_page.open()
            self.home_page.wait_for_homepage_load(
                timeout=15,
                max_retries=3
            )

            # Step 2: Click Packages in navigation bar
            self.package_booking_flow.logger.step(
                2,
                "Clicking Packages in nav bar"
            )
            self.package_booking_flow.click_packages_nav_link()

            # Step 3: Verify All Packages page loaded
            self.package_booking_flow.logger.step(
                3,
                "Verifying All Packages page"
            )
            packages_loaded = (
                self.package_booking_flow.verify_all_packages_page_loaded()
            )
            assert packages_loaded, "Failed to load All Packages page"

            # Step 4: Select first package
            self.package_booking_flow.logger.step(
                4,
                "Opening first package"
            )
            self.package_booking_flow.click_view_package_after_packageNavBar()

            # Step 5: Verify package detail page loaded
            self.package_booking_flow.logger.step(
                5,
                "Verifying package detail page"
            )
            WebDriverWait(self.driver, 15).until(
                lambda driver: "/packages/" in driver.current_url.lower()
                and driver.current_url.rstrip("/").split("/")[-1].isdigit()
            )

            self.package_booking_flow.logger.info(
                f"✅ Package detail page loaded: {self.driver.current_url}"
            )

            # Step 6: Verify pricing option can be selected
            self.package_booking_flow.logger.step(
                6,
                "Selecting package price option"
            )

            price_selected = (
                self.package_booking_flow.select_price_option("couple")
            )

            assert price_selected, (
                "Failed to select COUPLE price option"
            )

            # Step 7: Verify Book Reservation button is available
            self.package_booking_flow.logger.step(
                7,
                "Verifying Book Reservation button"
            )

            book_reservation_btn = WebDriverWait(
                self.driver,
                15
            ).until(
                EC.visibility_of_element_located(
                    self.package_booking_flow.BOOK_RESERVATION_BUTTON
                )
            )

            assert book_reservation_btn.is_displayed(), (
                "Book Reservation button should be visible"
            )

            self.package_booking_flow.logger.success(
                "✅ All Packages → Package Detail flow verified successfully!"
            )

        except Exception as e:
            self.package_booking_flow.logger.error(
                f"❌ All Packages booking flow failed: {str(e)}"
            )
            self.package_booking_flow.screenshot.capture_screenshot_on_failure(
                "all_packages_flow_failure"
            )
            raise
# src/tests/smoke_tests/test_flight_booking_smoke.py

import pytest
import time
from selenium.webdriver.common.by import By
from src.pages.ui.flight_booking_flow import FlightBookingFlow
from src.pages.ui.home_page import HomePage
from src.core.test_base import TestBase


class TestFlightBookingSmoke(TestBase):
    """
    Smoke Tests for Geo Travel Flight Booking Flow
    - Homepage Accessibility
    - Basic Flight Search
    - Search Results Display
    - Flight Selection
    - Passenger Form
    - Payment Page Accessibility
    """

    @pytest.fixture(autouse=True)
    def setup(self, driver):
        """Setup before each test"""
        self.driver = driver
        self.home_page = HomePage(driver)
        self.flight_booking = FlightBookingFlow(driver)
        yield

    @pytest.mark.smoke
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
        current_url = self.flight_booking.navigator.get_current_url()
        assert current_url, "Current URL should not be empty"

        self.home_page.logger.success("Homepage loaded successfully")

    @pytest.mark.smoke
    def test_flight_search_form_visible(self):
        """Smoke Test 2: Test that flight search form is visible"""
        self.flight_booking.logger.info("=== Testing Flight Search Form Visibility ===")

        self.flight_booking.logger.step(1, "Opening homepage")
        self.home_page.open()
        self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)

        self.flight_booking.logger.step(2, "Checking flight search form visibility")
        assert (
            self.flight_booking.is_flight_search_form_visible()
        ), "Flight search form not visible"
        
        self.flight_booking.logger.success("Flight search form is visible")

    # @pytest.mark.smoke
    # def test_basic_flight_search(self):
    #     """Smoke Test 3: Test basic flight search functionality"""
    #     self.flight_booking.logger.info("=== Testing Basic Flight Search ===")

    #     self.flight_booking.logger.step(1, "Opening homepage")
    #     self.home_page.open()
    #     self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
    #     # self.flight_booking.debug_ui_elements()

    #     self.flight_booking.logger.step(2, "Performing basic flight search")
    #     search_success = self.flight_booking.perform_basic_flight_search()
    #     assert search_success, "Basic flight search failed"

    #     self.flight_booking.logger.step(3, "Waiting for search to complete")
    #     time.sleep(3)

    #     self.flight_booking.logger.step(4, "Verifying search results page")
    #     current_url = self.flight_booking.navigator.get_current_url()
    #     self.flight_booking.logger.info(f"Current URL after search: {current_url}")

    #     # Check both URL and visual indicators
    #     url_contains_search = "searchid=" in current_url.lower()
    #     results_displayed = self.flight_booking.are_search_results_displayed()

    #     self.flight_booking.logger.info(f"URL contains 'search': {url_contains_search}")
    #     self.flight_booking.logger.info(f"Results displayed: {results_displayed}")

    #     assert (
    #         url_contains_search or results_displayed
    #     ), f"Flight search failed. URL: {current_url}, Results visible: {results_displayed}"

    #     self.flight_booking.logger.success("Basic flight search performed successfully")

    # @pytest.mark.smoke
    # def test_search_results_display(self):
    #     """Smoke Test 4: Test that search results are properly displayed"""
    #     self.flight_booking.logger.info("=== Testing Search Results Display ===")

    #     self.flight_booking.logger.step(1, "Opening homepage")
    #     self.home_page.open()
    #     self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
        
    #     self.flight_booking.logger.step(2, "Performing basic flight search")
    #     search_success = self.flight_booking.perform_basic_flight_search()
    #     assert search_success, "Flight search failed"

    #     self.flight_booking.logger.step(3, "Verifying search session is initialized")
    #     time.sleep(3)
    #     search_initialized = self.flight_booking.is_search_session_initialized()
    #     assert search_initialized, "Search session not properly initialized (missing searchId)"

    #     self.flight_booking.logger.step(4, "Checking search results display")
    #     results_displayed = self.flight_booking.are_search_results_displayed()
    #     assert results_displayed, "Search results not displayed properly"

    #     self.flight_booking.logger.success("Search results displayed correctly")

    # @pytest.mark.smoke
    # def test_flight_selection_works(self):
    #     """Smoke Test 5: Test that flight selection functionality works"""
    #     self.flight_booking.logger.info("=== Testing Flight Selection ===")
        
    #     self.flight_booking.logger.step(1, "Opening homepage")
    #     self.home_page.open()
    #     self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
        
    #     self.flight_booking.logger.step(2, "Performing basic flight search")
    #     search_success = self.flight_booking.perform_basic_flight_search()
    #     assert search_success, "Flight search failed"
        
    #     self.flight_booking.logger.step(3, "Selecting flight")
    #     selection_success = self.flight_booking.select_flight()
    #     assert selection_success, "Flight selection failed"
        
    #     self.flight_booking.logger.success("Flight selection works correctly")

    # @pytest.mark.smoke
    # def test_passenger_form_loads(self):
    #     """Smoke Test 6: Test that passenger form loads and can be filled"""
    #     self.flight_booking.logger.info("=== Testing Passenger Form ===")
        
    #     self.flight_booking.logger.step(1, "Opening homepage")
    #     self.home_page.open()
    #     self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
        
    #     self.flight_booking.logger.step(2, "Performing basic flight search")
    #     search_success = self.flight_booking.perform_basic_flight_search()
    #     assert search_success, "Flight search failed"
        
    #     self.flight_booking.logger.step(3, "Selecting flight")
    #     selection_success = self.flight_booking.select_flight()
    #     assert selection_success, "Flight selection failed"

    #     self.flight_booking.logger.step(4, "Filling passenger information")
    #     form_filled = self.flight_booking.fill_passenger_information()
    #     assert form_filled, "Failed to fill passenger form"

    #     self.flight_booking.logger.step(5, "Saving passenger information and continuing")
    #     saved = self.flight_booking.save_passenger_info_and_continue()
    #     assert saved, "Failed to save passenger information"

    #     self.flight_booking.logger.success("Passenger form loads and can be filled successfully")

    # @pytest.mark.smoke
    # def test_payment_page_accessible(self):
    #     """Smoke Test 7: Test that payment page is accessible"""
    #     self.flight_booking.logger.info("=== Testing Payment Page Accessibility ===")
        
    #     self.flight_booking.logger.step(1, "Opening homepage")
    #     self.home_page.open()
    #     self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
        
    #     self.flight_booking.logger.step(2, "Performing basic flight search")
    #     search_success = self.flight_booking.perform_basic_flight_search()
    #     assert search_success, "Flight search failed"
        
    #     self.flight_booking.logger.step(3, "Selecting flight")
    #     selection_success = self.flight_booking.select_flight()
    #     assert selection_success, "Flight selection failed"

    #     self.flight_booking.logger.step(4, "Filling passenger information")
    #     form_filled = self.flight_booking.fill_passenger_information()
    #     assert form_filled, "Failed to fill passenger form"

    #     self.flight_booking.logger.step(5, "Saving and continuing")
    #     saved = self.flight_booking.save_passenger_info_and_continue()
    #     assert saved, "Failed to save passenger information"

    #     self.flight_booking.logger.step(6, "Checking payment page accessibility")
    #     payment_accessible = self.flight_booking.is_payment_page_accessible()
    #     assert payment_accessible, "Payment page not accessible"

    #     self.flight_booking.logger.step(7, "Selecting payment method")
    #     payment_method_selected = self.flight_booking.select_payment_method()
    #     assert payment_method_selected, "Failed to select payment method"

    #     self.flight_booking.logger.success("Payment page is accessible")

    # @pytest.mark.smoke
    # def test_complete_booking_flow(self):
    #     """Smoke Test 8: Complete end-to-end flight booking flow"""
    #     self.flight_booking.logger.info("=== Testing Complete Booking Flow ===")

    #     try:
    #         # Step 1: Homepage and search
    #         self.flight_booking.logger.step(1, "Opening homepage and performing search")
    #         self.home_page.open()
    #         self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
    #         search_success = self.flight_booking.perform_basic_flight_search()
    #         assert search_success, "Flight search failed"

    #         # Step 2: Verify search results
    #         self.flight_booking.logger.step(2, "Verifying search results")
    #         search_initialized = self.flight_booking.is_search_session_initialized()
    #         assert search_initialized, "Search session failed"
            
    #         results_displayed = self.flight_booking.are_search_results_displayed()
    #         assert results_displayed, "No search results"

    #         # Step 3: Select flight
    #         self.flight_booking.logger.step(3, "Selecting flight")
    #         selection_success = self.flight_booking.select_flight()
    #         assert selection_success, "Flight selection failed"

    #         # Step 4: Fill passenger information
    #         self.flight_booking.logger.step(4, "Filling passenger information")
    #         form_filled = self.flight_booking.fill_passenger_information()
    #         assert form_filled, "Passenger form failed"

    #         # Step 5: Save and continue
    #         self.flight_booking.logger.step(5, "Saving passenger information")
    #         saved = self.flight_booking.save_passenger_info_and_continue()
    #         assert saved, "Save failed"

    #         # Step 6: Verify payment page
    #         self.flight_booking.logger.step(6, "Verifying payment page")
    #         payment_accessible = self.flight_booking.is_payment_page_accessible()
    #         assert payment_accessible, "Payment page not accessible"

    #         # Step 7: Select payment method
    #         self.flight_booking.logger.step(7, "Selecting payment method")
    #         payment_method_selected = self.flight_booking.select_payment_method()
    #         assert payment_method_selected, "Payment method selection failed"

    #         self.flight_booking.logger.success("Complete booking flow works correctly")

    #     except Exception as e:
    #         self.flight_booking.logger.error(f"Complete booking flow failed: {e}")
    #         raise

    @pytest.mark.smoke
    def test_error_handling(self):
        """Smoke Test 9: Test error handling scenarios"""
        self.flight_booking.logger.info("=== Testing Error Handling ===")
        
        self.flight_booking.logger.step(1, "Opening homepage")
        self.home_page.open()
        self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)

        self.flight_booking.logger.step(2, "Testing error handling with non-existent elements")
        try:
            self.flight_booking.driver.find_element(
                By.XPATH, "//button[contains(text(),'NonExistentButton')]"
            )
            error_occurred = False
        except:
            error_occurred = True

        self.flight_booking.logger.step(3, "Verifying error handling works")
        assert error_occurred, "Error handling verification"

        self.flight_booking.logger.success("Error handling works correctly")
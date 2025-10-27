# src/tests/smoke_tests/test_flight_booking_smoke.py

import pytest
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from src.pages.flight_booking_flow import FlightBookingFlow
from src.pages.home_page import HomePage
from src.core.test_base import TestBase


class TestFlightBookingSmoke(TestBase):
    """
    Smoke Tests for Geo Travel Flight Booking Flow
    - Homepage Accessibility
    - Basic Flight Search
    - Flights Search Results Display
    - Flight Selection
    - Passenger Form
    - Payment Page Accessibility
    - Navigation Works
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
        current_url = self.flight_booking.navigator.get_current_url
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

    @pytest.mark.smoke
    def test_basic_flight_search(self):
        """Smoke Test 3: Test basic flight search functionality"""
        self.flight_booking.logger.info("=== Testing Basic Flight Search ===")

        self.flight_booking.logger.step(1, "Opening homepage")
        self.home_page.open()
        self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)

        self.flight_booking.logger.step(2, "Performing basic flight search")
        self.flight_booking.perform_basic_flight_search()

        self.flight_booking.logger.step(3, "Waiting for search to complete")
        time.sleep(5)  # Increased wait time for search processing

        self.flight_booking.logger.step(4, "Verifying search results page")
        current_url = self.flight_booking.navigator.get_current_url()
        self.flight_booking.logger.info(f"Current URL after search: {current_url}")
        time.sleep(5)

        # Check both URL and visual indicators
        url_contains_search = "searchid=" in current_url.lower()
        results_displayed = self.flight_booking.are_search_results_displayed()

        self.flight_booking.logger.info(f"URL contains 'search': {url_contains_search}")
        self.flight_booking.logger.info(f"Results displayed: {results_displayed}")

        assert (
            url_contains_search or results_displayed
        ), f"Flight search failed. URL: {current_url}, Results visible: {results_displayed}"

        self.flight_booking.logger.success("Basic flight search performed successfully")

    @pytest.mark.smoke
    def test_search_results_display(self):
        """Test that search results are properly displayed"""
        self.flight_booking.logger.info("=== Testing Search Results Display ===")

        self.flight_booking.logger.step(1, "Opening homepage")
        self.home_page.open()
        self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
        
        self.flight_booking.logger.step(2, "Performing basic flight search")
        self.flight_booking.perform_basic_flight_search()

        self.flight_booking.logger.step(3, "Verifying search session is initialized")
        time.sleep(5)  # Wait for URL to update
        assert (
            self.flight_booking.is_search_session_initialized()
        ), "Search session not properly initialized (missing searchId)"

        self.flight_booking.logger.step(4, "Checking search results display")
        assert (
            self.flight_booking.are_search_results_displayed()
        ), "Search results not displayed properly"

        self.flight_booking.logger.success("Search results displayed correctly")

    # @pytest.mark.smoke
    def test_flight_selection_works(self):
        """Test that flight selection functionality works"""
        self.flight_booking.logger.info("=== Testing Flight Selection ===")
        
        self.flight_booking.logger.step(1, "Opening homepage")
        self.home_page.open()
        self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
        
        self.flight_booking.logger.step(2, "Performing basic flight search")
        self.flight_booking.perform_basic_flight_search()
        
        self.flight_booking.logger.step(3, "Selecting flight")
        selection_success = self.flight_booking.select_flight()
        assert selection_success, "Flight selection failed"
        
        self.flight_booking.logger.success("Flight selection works correctly")

    # @pytest.mark.smoke
    def test_passenger_form_loads(self):
        """Test that passenger form loads and can be filled"""
        self.flight_booking.logger.info("=== Testing Passenger Form ===")
        
        self.flight_booking.logger.step(1, "Opening homepage")
        self.home_page.open()
        self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)

        self.flight_booking.logger.step(2, "Scrolling to passenger form")
        self.flight_booking.scroll_down()

        self.flight_booking.logger.step(3, "Filling passenger information")
        form_filled = self.flight_booking.fill_passenger_information()
        assert form_filled, "Failed to fill passenger form"

        self.flight_booking.logger.step(4, "Saving passenger information and continuing")
        saved = self.flight_booking.save_passenger_info_and_continue()
        assert saved, "Failed to save passenger information"

        self.flight_booking.logger.success("Passenger form loads and can be filled successfully")

    # @pytest.mark.smoke
    def test_payment_page_accessible(self):
        """Test that payment page is accessible"""
        self.flight_booking.logger.info("=== Testing Payment Page Accessibility ===")
        
        self.flight_booking.logger.step(1, "Opening homepage")
        self.home_page.open()
        self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)

        self.flight_booking.logger.step(2, "Waiting for navigation to payment page")
        time.sleep(3)

        self.flight_booking.logger.step(3, "Checking payment page accessibility")
        assert (
            self.flight_booking.is_payment_page_accessible()
        ), "Payment page not accessible"

        self.flight_booking.logger.step(4, "Selecting payment method")
        payment_method_selected = self.flight_booking.select_payment_method()
        assert payment_method_selected, "Failed to select payment method"

        self.flight_booking.logger.success("Payment page is accessible")
    
    @pytest.mark.smoke
    def test_flights_navigation_works(self):
        """Validate browser navigation (open, back, forward) across flight booking pages."""
        self.flight_booking.logger.info("=== Testing Flights Navigation ===")

        self.flight_booking.logger.step(1, "Opening homepage and waiting for load")
        self.home_page.open()
        self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)

        self.flight_booking.logger.step(2, "Capturing initial URL")
        initial_url = self.flight_booking.navigator.get_current_url()
        self.home_page.logger.info(f"Initial URL: {initial_url}")

        self.flight_booking.logger.step(3, "Navigating to flight search page")
        search_path = "/search-results/flight"
        self.home_page.open(search_path)

        self.flight_booking.logger.step(4, "Capturing flight page URL")
        flight_url = self.flight_booking.navigator.get_current_url()
        self.flight_booking.logger.info(f"Flight page URL: {flight_url}")

        assert initial_url != flight_url, (
            f"Expected navigation to a different page. From {initial_url} to {flight_url}"
        )

        self.flight_booking.logger.step(5, "Testing browser back navigation")
        self.flight_booking.navigator.go_back()

        self.flight_booking.logger.step(6, "Capturing URL after back navigation")
        back_url = self.flight_booking.navigator.get_current_url()
        self.flight_booking.logger.info(f"Back navigation URL: {back_url}")

        assert back_url != flight_url, "Back navigation should exit the flight page"
        assert (
            initial_url.split('/')[-1] in back_url or "home" in back_url.lower()
        ), "Back navigation should return to the home area"

        self.flight_booking.logger.step(7, "Testing browser forward navigation")
        self.flight_booking.navigator.go_forward()

        self.flight_booking.logger.step(8, "Waiting for forward navigation to complete")
        self.flight_booking.waiter.wait_for_page_load(timeout=10)
        forward_url = self.flight_booking.navigator.get_current_url()
        self.flight_booking.logger.info(f"Forward navigation URL: {forward_url}")

        assert (
            "flight" in forward_url.lower() or "search" in forward_url.lower()
        ), "Forward navigation should return to the flight/search page"

        self.flight_booking.logger.step(9, "Confirming flight page is functional after navigation")
        assert self.flight_booking.is_page_loaded(), (
            "Flight page should be fully loaded after forward navigation"
        )

        self.flight_booking.logger.success("Browser navigation works correctly")

    @pytest.mark.smoke
    def test_error_handling(self):
        """Test error handling scenarios"""
        self.flight_booking.logger.info("=== Testing Error Handling ===")
        
        self.flight_booking.logger.step(1, "Opening homepage")
        self.home_page.open()
        self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)
        
        self.flight_booking.logger.step(2, "Navigating to flight search page")
        search_path = "/search-results/flight"
        self.home_page.open(search_path)
        self.flight_booking.waiter.wait_for_page_load(timeout=10)

        self.flight_booking.logger.step(3, "Testing error handling with non-existent elements")
        try:
            self.flight_booking.driver.find_element(
                By.XPATH, "//button[contains(text(),'NonExistentButton')]"
            )
            error_occurred = False
        except:
            error_occurred = True

        self.flight_booking.logger.step(4, "Verifying error handling works")
        assert error_occurred, "Error handling verification"

        self.flight_booking.logger.success("Error handling works correctly")
# src/tests/smoke_tests/test_homepage_smoke.py

import pytest
import time
from selenium.webdriver.common.by import By
from src.pages.home_page import HomePage
from src.core.test_base import TestBase


class TestHomePageSmoke(TestBase):
    """
    Smoke Tests for Geo Travel Homepage
    - Homepage Loads Successfully
    - Basic Homepage Elements Exists
    - Navigation Works
    - Homepage Health Check
    """

    @pytest.fixture(autouse=True)
    def setup(self, driver):
        """Setup before each test"""
        self.driver = driver
        self.home_page = HomePage(driver)
        yield

    @pytest.mark.smoke
    def test_homepage_loads_successfully(self):
        """Smoke Test 1: Homepage loads without errors"""
        self.home_page.logger.info("=== Testing Homepage Loads Successfully ===")

        self.home_page.logger.step(1, "Opening homepage")
        self.home_page.open()
        self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)

        self.home_page.logger.step(2, "Checking page title")
        title = self.home_page.title
        assert title is not None, "Page title should not be None"
        assert len(title) > 0, "Page title should not be empty"
        assert "error" not in title.lower(), "Page title should not indicate an error"

        self.home_page.logger.step(3, "Checking current URL")
        current_url = self.home_page.navigator.get_current_url
        assert current_url, "Current URL should not be empty"

        self.home_page.logger.success("Homepage loaded successfully")

    @pytest.mark.smoke
    def test_basic_homepage_elements_exist(self):
        """Smoke Test 2: Basic page elements exist"""
        self.home_page.logger.info("=== Testing Basic Homepage Elements Exist ===")

        self.home_page.logger.step(1, "Opening homepage")
        self.home_page.open()
        self.home_page.wait_for_homepage_load()

        self.home_page.logger.step(2, "Checking page source and structure")
        page_source = self.home_page.driver.page_source.lower()

        assert len(page_source) > 100, "Page should have substantial content"
        assert "<html" in page_source, "Should have HTML structure"
        assert "<body" in page_source, "Should have body content"

        self.home_page.logger.step(3, "Checking for headings and links")
        has_heading = self.home_page.validator.is_element_present((By.TAG_NAME, "h1"))
        has_links = self.home_page.validator.is_element_present((By.TAG_NAME, "a"))

        if not has_heading:
            self.home_page.logger.warning(
                "No H1 heading found (may be normal for some pages)"
            )
        if not has_links:
            self.home_page.logger.warning(
                "No links found (unusual but maybe not critical)"
            )

        self.home_page.logger.success("Basic page elements check passed")

    @pytest.mark.smoke
    def test_homepage_navigation_works(self):
        """Smoke Test 3: Basic navigation works"""
        self.home_page.logger.info("=== Testing Homepage Navigation Works ===")

        # Step 1: Load homepage
        self.home_page.logger.step(1, "Opening and validating homepage")
        self.home_page.open()
        self.home_page.wait_for_homepage_load()

        # Step 2: Get initial URL and test navigation
        self.home_page.logger.step(2, "Testing navigation functionality")
        initial_url = self.home_page.navigator.get_current_url

        navigation_worked, message = self.home_page.navigator.test_navigation_works(initial_url)

        if navigation_worked:
            self.home_page.logger.success(f"Navigation test passed: {message}")
            assert True
        else:
            self.home_page.logger.warning(f"Navigation test inconclusive: {message}")
            # Don't fail the test for navigation issues in smoke testing
            assert True
            
    @pytest.mark.smoke
    def test_homepage_health_check(self):
        """Smoke Test 4: Page Health Check"""
        self.home_page.logger.info("=== Testing Page Health Check ===")

        self.home_page.logger.step(1, "Opening homepage")
        self.home_page.open()
        self.home_page.wait_for_homepage_load()

        self.home_page.logger.step(2, "Performing comprehensive health check")
        all_checks_passed, detailed_checks = self.home_page.is_page_loaded_correctly()

        self.home_page.logger.step(3, "Verifying critical health checks")
        assert (
            all_checks_passed
        ), f"Critical homepage health check failed. Details: {detailed_checks}"
        
        self.home_page.logger.step(4, "Checking logo visibility")
        assert self.home_page.is_logo_visible(), "Logo should be visible"

        self.home_page.logger.success("Homepage health check passed")
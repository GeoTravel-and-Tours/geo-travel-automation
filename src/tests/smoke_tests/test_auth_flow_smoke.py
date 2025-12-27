# src/tests/smoke_tests/test_auth_flow_smoke.py

import pytest
import time
import os
from src.pages.ui.auth_flow import AuthFlow
from src.pages.ui.home_page import HomePage
from src.core.test_base import TestBase


class TestAuthFlowSmoke(TestBase):
    """
    Smoke Tests for Geo Travel Authentication Flow
    - Login page accessibility
    - Successful Login & Redirect
    - Failed Login with Error Message
    - Logout Functionality
    """

    @pytest.fixture(autouse=True)
    def setup(self, driver):
        """Setup before each test"""
        self.driver = driver
        self.auth_flow = AuthFlow(driver)
        self.home_page = HomePage(driver)
        yield

    @pytest.mark.smoke
    @pytest.mark.auth
    def test_login_page_accessibility(self):
        """Smoke Test 4: Login page is accessible and has required elements"""
        self.auth_flow.logger.info("=== Testing Login Page Accessibility ===")
        
        self.home_page.logger.step(1, "Navigating to homepage")
        self.home_page.open()
        self.home_page.wait_for_homepage_load(timeout=15, max_retries=3)

        self.auth_flow.logger.step(2, "Navigating to login page")
        self.auth_flow.open_login_page()

        self.auth_flow.logger.step(3, "Verifying login page loads")
        assert self.auth_flow.wait_for_login_page(), "Login page should load"

        self.auth_flow.logger.step(4, "Verifying required elements on login page")
        assert self.auth_flow.waiter.wait_for_visible(
            AuthFlow.EMAIL_INPUT, timeout=5
        ), "Email input should be visible"
        assert self.auth_flow.waiter.wait_for_visible(
            AuthFlow.PASSWORD_INPUT, timeout=5
        ), "Password input should be visible"
        assert self.auth_flow.waiter.wait_for_visible(
            AuthFlow.LOGIN_BUTTON, timeout=5
        ), "Login button should be visible"

        self.auth_flow.logger.step(5, "Verifying login page title and content")
        assert self.auth_flow.title is not None, "Login page should have a title"
        assert len(self.auth_flow.title) > 0, "Login page title should not be empty"

        self.auth_flow.logger.success("Login page accessibility test passed")

    @pytest.mark.smoke
    @pytest.mark.auth
    def test_successful_login_and_redirect(self):
        """Smoke Test 1: Successful login with valid credentials redirects to dashboard"""
        self.auth_flow.logger.info("=== Testing Successful Login and Redirect ===")

        email, password = self.auth_flow.get_credentials_from_env()

        if not email or not password:
            self.auth_flow.logger.warning(
                "No test credentials - skipping successful login test"
            )
            pytest.skip(
                "TEST_USER_EMAIL and TEST_USER_PASSWORD environment variables required"
            )

        self.auth_flow.logger.step(1, "Navigating to login page")
        self.auth_flow.open_login_page()
        assert self.auth_flow.wait_for_login_page(), "Login page should load"

        self.auth_flow.logger.step(2, "Attempting login with valid credentials")
        login_success = self.auth_flow.login(email, password)

        assert login_success, "Login should be successful with valid credentials"
        
        self.auth_flow.logger.step(3, "Verifying user is redirected to dashboard")
        assert self.auth_flow.wait_until_on_dashboard(
            timeout=10
        ), "User should be redirected to dashboard after successful login"

        self.auth_flow.logger.success("Successful login & redirect test passed")

    @pytest.mark.smoke
    @pytest.mark.auth
    def test_failed_login_with_error_message(self):
        """Smoke Test 2: Failed login with invalid credentials shows toast error message"""
        self.auth_flow.logger.info("=== Testing Failed Login with Error Message ===")

        self.auth_flow.logger.step(1, "Navigating to login page")
        self.auth_flow.open_login_page()
        assert self.auth_flow.wait_for_login_page(), "Login page should load successfully"

        self.auth_flow.logger.step(2, "Attempting login with invalid credentials")
        login_success = self.auth_flow.login(
            "invalid_user@example.com", "wrong_password_123"
        )

        assert not login_success, "Login should fail with invalid credentials"
        
        # Try to capture toast
        self.auth_flow.logger.step(3, "Fetching error message from toast")
        error_message = (
            self.auth_flow.get_last_toast() 
            or self.auth_flow.get_toast_error_message()
        )
        
        # Fallback: still on login page
        still_on_login_page = self.auth_flow.navigator.current_url_contains("/auth/login")

        assert (
            error_message or still_on_login_page
        ), (
            "Failed login was not confirmed: "
            "no error toast captured and user not on login page"
        )
        
        if error_message:
            self.auth_flow.logger.success(
                f"Failed login confirmed via toast: {error_message}"
            )
        else:
            self.auth_flow.logger.success(
                "Failed login confirmed — user remained on login page"
            )

    @pytest.mark.smoke
    @pytest.mark.auth
    def test_logout_functionality(self):
        """Smoke Test 3: Logout successfully terminates session and redirects to login"""
        self.auth_flow.logger.info("=== Testing Logout Functionality ===")

        username, password = self.auth_flow.get_credentials_from_env()

        if not username or not password:
            self.auth_flow.logger.warning(
                "No test credentials - skipping logout test"
            )
            pytest.skip(
                "TEST_USER_EMAIL and TEST_USER_PASSWORD environment variables required"
            )

        self.auth_flow.logger.step(1, "Logging in with valid credentials")
        self.auth_flow.open_login_page()
        self.auth_flow.wait_for_login_page()
        login_success = self.auth_flow.login(username, password)

        if not login_success:
            self.auth_flow.logger.warning("Login failed - cannot test logout")
            pytest.skip("Login failed - cannot proceed with logout test")

        self.auth_flow.logger.step(2, "Verifying user is on dashboard after login")
        assert (
            self.auth_flow.is_user_on_dashboard()
        ), "Should be on dashboard after login"

        self.auth_flow.logger.step(3, "Performing logout")
        logout_success = self.auth_flow.logout()
        assert logout_success, "Logout action should be successful"
        
        assert self.auth_flow.wait_until_logged_out(
            timeout=10
        ), "User should be logged out and redirected from dashboard"
        self.auth_flow.logger.success("Logout functionality test passed")
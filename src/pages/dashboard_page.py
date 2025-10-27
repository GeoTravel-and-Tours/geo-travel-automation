# src/pages/dashboard_page.py

from selenium.webdriver.common.by import By
from src.core.base_page import BasePage
from src.pages.auth_flow import AuthFlow


class DashboardPage(BasePage):
    """
    Geo Travel Dashboard Page (after successful login)
    """

    # ===== DASHBOARD LOCATORS =====
    LOGOUT_BUTTON = (
        By.CSS_SELECTOR,
        "[href*='logout'], .logout-btn, button:contains('Logout')",
    )
    BOOK_FLIGHT_BUTTON = (By.XPATH, ".//button[normalize-space()='Book new flight']")
    DASHBOARD_LOGO = (By.CSS_SELECTOR, "img[alt='Full Logo']")

    def __init__(self, driver):
        super().__init__(driver)
        self.auth_flow = AuthFlow(driver)

    def wait_for_dashboard_load(self, timeout=10):
        """Wait for dashboard to load after login"""
        self.logger.info("Waiting for dashboard to load...")

        try:
            # Wait for dashboard indicators
            self.waiter.wait_for_visible(
                self.auth_flow.DASHBOARD_INDICATORS, timeout=10
            )

            # Check for user-specific elements
            if (
                self.validator.is_element_present(self.auth_flow.DASHBOARD_INDICATORS)
                or self.validator.is_element_present(self.DASHBOARD_LOGO)
                or self.validator.is_element_present(self.BOOK_FLIGHT_BUTTON)
            ):
                self.logger.info("Dashboard loaded successfully")
                return True
            else:
                self.logger.warning("Dashboard loaded but user elements not found")
                return True

        except Exception as e:
            self.logger.error(f"Dashboard failed to load: {e}")
            return False

    def is_user_on_dashboard(self):
        """Check if user is on the bookings dashboard"""
        try:
            # Primary indicators (must have at least one)
            primary_indicators = [
                self.pageinfo._page_contains_silent("Bookings"),
                self.pageinfo._page_contains_silent("Upcoming Trips"),
                self.pageinfo._page_contains_silent(
                    "Manage your flights and travel plans"
                ),
            ]

            # Secondary indicators (nice to have)
            secondary_indicators = [
                self.pageinfo._page_contains_silent("Past Trips"),
                self.pageinfo._page_contains_silent("Book flight"),
                self.pageinfo._page_contains_silent("Visa Applications"),
            ]

            # Must have at least 1 primary AND 1 secondary indicator
            has_primary = any(primary_indicators)
            has_secondary = any(secondary_indicators)

            if has_primary and has_secondary:
                self.logger.info("User is on bookings dashboard")
                return True

            self.logger.error("User is not on bookings dashboard")
            return False

        except Exception as e:
            self.logger.debug(f"Dashboard check failed: {e}")
            return False

"""
src/pages/ui/dashboard_page.py

Page Object for the Geo Travel user dashboard, i.e. the page users land
on after a successful login (see ``AuthFlow.login`` in auth_flow.py).

Covers:
    1. Load confirmation - wait for the dashboard to render and check for
       either the shared dashboard indicators, the site logo, or the
       "Book new flight" button.
    2. Dashboard identity check - a text-content-based check
       (``is_user_on_dashboard``) confirming the page is actually the
       bookings dashboard rather than some other logged-in page.

This page object is intentionally coupled to ``AuthFlow``
(src/pages/ui/auth_flow.py): its constructor creates an ``AuthFlow``
instance purely to reuse ``AuthFlow.DASHBOARD_INDICATORS`` (the list of
locators AuthFlow itself uses to confirm a successful login). Tests
typically reach this page via ``AuthFlow.login()`` and then use
``wait_for_dashboard_load`` / ``is_user_on_dashboard`` to assert on it.
"""

from selenium.webdriver.common.by import By
from src.core.base_page import BasePage
from src.pages.ui.auth_flow import AuthFlow


class DashboardPage(BasePage):
    """
    Geo Travel Dashboard Page (after successful login).

    Locators cover the dashboard's own elements (logout, "Book new
    flight", site logo); the dashboard-content indicators themselves are
    borrowed from ``AuthFlow.DASHBOARD_INDICATORS`` via ``self.auth_flow``
    rather than being redefined here.
    """

    # ===== DASHBOARD LOCATORS =====
    # NOTE: ":contains('Logout')" is a jQuery/Sizzle pseudo-class, not valid
    # native CSS - browsers reject it as an invalid selector. Since it's one
    # branch of a comma-separated selector list, this likely makes the whole
    # LOGOUT_BUTTON selector throw rather than gracefully falling back to the
    # first two branches. It also isn't referenced by any method below.
    LOGOUT_BUTTON = (
        By.CSS_SELECTOR,
        "[href*='logout'], .logout-btn, button:contains('Logout')",
    )
    BOOK_FLIGHT_BUTTON = (By.XPATH, ".//button[normalize-space()='Book new flight']")
    DASHBOARD_LOGO = (By.CSS_SELECTOR, "img[alt='Full Logo']")

    def __init__(self, driver):
        """Initialize the page object and wire up a companion AuthFlow instance.

        Args:
            driver (WebDriver): Active Selenium WebDriver instance, passed
                through to ``BasePage``. Also used to construct
                ``self.auth_flow`` so its ``DASHBOARD_INDICATORS`` locator
                list can be reused here.
        """
        super().__init__(driver)
        self.auth_flow = AuthFlow(driver)

    def wait_for_dashboard_load(self, timeout=10):
        """Wait for the dashboard to render after login.

        FIXME: ``self.auth_flow.DASHBOARD_INDICATORS`` is a *list* of
        locator tuples, but both ``self.waiter.wait_for_visible(...)`` and
        ``self.validator.is_element_present(...)`` are written to accept a
        single ``(By, value)`` locator tuple (they pass it straight into
        ``EC.visibility_of_element_located`` / ``driver.find_element(*locator)``).
        Passing the whole list here is very likely a bug that raises at
        runtime instead of checking each indicator - contrast with
        ``AuthFlow._wait_for_any_dashboard_indicator``, which correctly
        iterates over the list one locator at a time.

        Args:
            timeout (int): Accepted for interface consistency, but note
                the inner waits below use their own hardcoded values
                rather than this parameter.

        Returns:
            bool: True once the dashboard is considered loaded (even if
                the user-specific elements aren't found, this still
                returns True with a warning logged); False if an
                exception occurred while checking.
        """
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
        """Check if the current page is the bookings dashboard, via page text.

        Duplicates the same primary/secondary phrase-matching logic as
        ``AuthFlow._fallback_dashboard_check`` (see the NOTE there about
        the redundant has_primary/has_secondary computation) rather than
        delegating to it.

        Returns:
            bool: True if at least one primary AND one secondary
                dashboard-related phrase are found on the page, False
                otherwise (including on error).
        """
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

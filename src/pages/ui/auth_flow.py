"""
src/pages/ui/auth_flow.py

Page Object for the Geo Travel authentication flow: login and logout.

Covers:
    1. Login       - open the login page, wait for it to render, fill in
                      email/password, submit, and confirm the app landed
                      on the dashboard (by URL and by dashboard UI
                      indicators).
    2. Toast/error - capture any "invalid credentials" style toast shown
                      after a failed login attempt.
    3. Logout      - locate and click the logout control (desktop or
                      mobile layout), then confirm the app redirected
                      away from the dashboard back to login/auth.

Tests typically call ``open_login_page`` -> ``login`` (which internally
waits for the request to settle and checks for the dashboard), and later
``logout`` to end the session. ``DashboardPage`` (src/pages/ui/dashboard_page.py)
also holds a reference to this class and reuses its ``DASHBOARD_INDICATORS``
locator list to detect a loaded dashboard - see the NOTE there.
"""

from selenium.webdriver.common.by import By
from src.core.base_page import BasePage
import time
import os
from selenium.webdriver.support.ui import WebDriverWait


class AuthFlow(BasePage):
    """
    Page Object Model combining the login and logout flows for Geo Travel.

    Locators are grouped into login-page elements (email/password inputs,
    sign-in button, error toast) and dashboard/logout elements
    (``DASHBOARD_INDICATORS`` - a list of alternative locators used to
    confirm the dashboard rendered, and ``LOGOUT_BUTTON`` - a list of
    alternative locators for the logout control, since the icon can be
    matched a couple of different ways).

    Unlike most other page objects in this package, ``DASHBOARD_INDICATORS``
    and ``LOGOUT_BUTTON`` are *lists* of ``(By, value)`` tuples rather than
    a single tuple - callers are expected to iterate over them and try each
    in turn (see ``_wait_for_any_dashboard_indicator`` and ``logout``).
    ``DashboardPage`` (dashboard_page.py) holds an instance of this class
    and reads ``DASHBOARD_INDICATORS`` directly off it.
    """

    # ===== LOGIN LOCATORS =====
    EMAIL_INPUT = (
        By.CSS_SELECTOR,
        "input[type='email'], input[name='email'], #email, #username, [data-testid='email']",
    )
    PASSWORD_INPUT = (
        By.CSS_SELECTOR,
        "input[type='password'], input[name='password'], #password, [data-testid='password']",
    )
    LOGIN_BUTTON = (By.XPATH, "//button[normalize-space()='Sign in']")
    TOAST_MESSAGE = (By.ID, "_rht_toaster")

    # ===== DASHBOARD / LOGOUT LOCATORS =====
    DASHBOARD_INDICATORS = [
        (By.XPATH, "//span[contains(text(),'Bookings')]"),
        (By.XPATH, "//span[contains(text(),'Packages')]"),
        (By.XPATH, "//span[contains(text(),'Visa Applications')]"),
        (By.XPATH, "//span[contains(text(),'Transactions')]"),
        (By.XPATH, "//span[contains(text(),'Rewards')]"),
        (By.XPATH, "//span[contains(text(),'Notifications')]"),
        (By.XPATH, "//span[contains(text(),'Account Management')]"),
    ]
    
    LOGOUT_BUTTON = [
        (By.XPATH, "//button[.//*[contains(@class, 'lucide-log-out')]]"),
        (By.CSS_SELECTOR, ".lucide-log-out"),
    ]

    def __init__(self, driver):
        """Initialize the page object and set the login route/last-toast cache.

        Args:
            driver (WebDriver): Active Selenium WebDriver instance, passed
                through to ``BasePage``.
        """
        super().__init__(driver)
        self.login_path = "auth/login"
        self.last_toast = None

    def open_login_page(self):
        """Navigate to the login page (``<base_url>/auth/login``).

        Returns:
            AuthFlow: ``self``, for method chaining.
        """
        self.open(self.login_path)
        self.logger.info("🔐 Navigated to login page")
        return self

    def wait_for_login_page(self, timeout=10):
        """Wait for the email and password inputs to become visible.

        Args:
            timeout (int): Seconds to wait for each input. Defaults to 10.

        Returns:
            bool: True if both fields became visible in time, False on
                any error/timeout (logged rather than raised).
        """
        self.logger.info("⏳ Waiting for login page to load...")

        try:
            self.waiter.wait_for_visible(self.EMAIL_INPUT, timeout)
            self.waiter.wait_for_visible(self.PASSWORD_INPUT, timeout)
            self.logger.info("Login page loaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Login page failed to load: {e}")
            return False

    def login(self, username, password):
        """
        Complete login flow: type credentials, submit, wait to settle, verify.

        Fills the email/password fields, clicks the sign-in button, waits
        for the request to settle (``wait_for_login_to_settle``), then
        delegates the actual success check to ``is_login_successful``.

        Args:
            username (str): User email/username.
            password (str): User password.

        Returns:
            bool: True if login succeeded (dashboard reached and
                confirmed), False on any failure (including exceptions,
                which are logged and swallowed rather than raised).
        """
        self.logger.info(f"Attempting login for user: {username}")
        login_btn = None

        try:
            self.element.type(self.EMAIL_INPUT, username)
            self.element.type(self.PASSWORD_INPUT, password)
            login_btn = self.element.click(self.LOGIN_BUTTON)
            self.logger.info("Login attempt completed")
            
            self.wait_for_login_to_settle(timeout=30)

            return self.is_login_successful()

        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            self._last_interacted_element = login_btn
            return False

    def _wait_for_any_dashboard_indicator(self, timeout=15):
        """Poll each locator in ``DASHBOARD_INDICATORS`` until one is visible.

        Splits the overall timeout budget across the remaining indicators
        (capped at 5s per indicator) so the whole check still respects the
        caller's total ``timeout`` even though several locators may need
        to be tried in sequence.

        Args:
            timeout (int): Total seconds allowed across all indicators.
                Defaults to 15.

        Returns:
            bool: True as soon as any indicator becomes visible, False if
                the whole list is exhausted (or time runs out) with no
                match.
        """
        self.logger.info(f"Looking for dashboard indicators...")

        start_time = time.time()
        for i, locator in enumerate(self.DASHBOARD_INDICATORS):
            try:
                time_remaining = timeout - (time.time() - start_time)
                if time_remaining <= 0:
                    break

                self.logger.info(f"  Trying indicator {i+1}: {locator}")
                self.waiter.wait_for_visible(locator, timeout=min(5, time_remaining))
                self.logger.info(f"Dashboard found with indicator {i+1}: {locator}")
                return True

            except Exception as e:
                self.logger.debug(f"  Indicator {i+1} failed: {e}")
                continue

        self.logger.error(f"All {len(self.DASHBOARD_INDICATORS)} dashboard indicators failed")
        return False

    def is_login_successful(self, timeout=30):
        """Confirm login succeeded by URL and by dashboard UI indicators.

        First waits for the URL to contain "/dashboard", then requires at
        least one of ``DASHBOARD_INDICATORS`` to become visible before
        declaring success - reaching the dashboard URL alone isn't treated
        as sufficient in case the SPA is still rendering.

        Args:
            timeout (int): Seconds to wait for the URL redirect. The
                dashboard-indicator check afterwards uses its own fixed
                20s budget regardless of this value.

        Returns:
            bool: True if both the URL and a dashboard indicator were
                confirmed, False otherwise.
        """
        self.logger.info("🔍 Verifying login status...")

        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: "/dashboard" in d.current_url.lower()
            )

            current_url = self.navigator.get_current_url().lower()
            self.logger.info(f"Redirected to: {current_url}")

            if self._wait_for_any_dashboard_indicator(timeout=20):
                self.logger.success("Login confirmed – Dashboard detected.")
                return True

            self.logger.error("Dashboard URL reached but UI not loaded.")
            return False

        except Exception as e:
            self.logger.error(f"Login did not reach dashboard: {e}")
            return False
        
    def get_last_toast(self):
        """Return the last captured toast message (if any).

        Returns:
            str or None: The most recent toast text captured by
                ``get_toast_error_message``, or None if nothing was
                captured yet.
        """
        return self.last_toast

    def get_toast_error_message(self, max_wait=10):
        """Poll for a toast error message and return its text once found.

        Only accepts a toast whose text is longer than 5 characters and
        contains "invalid" (case-insensitive), to filter out unrelated or
        transient toasts. If the toast has already disappeared by the
        time polling ends, still returns the last valid text seen rather
        than treating it as a miss - the toast tends to be short-lived.

        Args:
            max_wait (int): Max seconds to poll for the toast. Defaults
                to 10.

        Returns:
            str or None: The captured toast text, or None if no matching
                toast appeared within ``max_wait``.
        """
        try:
            start_time = time.time()
            last_valid_error = None

            while time.time() - start_time < max_wait:
                try:
                    error_element = self.driver.find_element(*self.TOAST_MESSAGE)
                    if error_element.is_displayed():
                        error_text = error_element.text.strip()

                        if (
                            error_text
                            and len(error_text) > 5
                            and "invalid" in error_text.lower()
                        ):
                            self.logger.info(f"Valid toast captured: {error_text}")
                            last_valid_error = error_text
                            self.last_toast = error_text

                            return error_text

                except Exception:
                    pass

                time.sleep(1.5)

            if last_valid_error:
                self.logger.info(f"Returning captured toast (now disappeared): {last_valid_error}")
                self.last_toast = last_valid_error
                return last_valid_error

            self.logger.debug("No valid toast error message found")
            return None

        except Exception as e:
            self.logger.debug(f"Toast capture failed: {e}")
            return None
        
    def logout(self):
        """Locate and click the logout control, then verify the session ended.

        Tries each locator in ``LOGOUT_BUTTON`` in turn, falling back to a
        JS-driven click if a plain Selenium click fails (e.g. the icon is
        obscured). Success is confirmed either by the URL moving to a
        login/auth route or by the login button becoming visible again.

        Returns:
            bool: True once logout is confirmed via URL or UI, False if
                no logout locator could be found/clicked or logout
                couldn't be confirmed.

        Raises:
            AssertionError: If the user isn't on the dashboard when this
                is called (logout only makes sense from there).
        """
        self.logger.info("Attempting logout...")

        assert self.is_user_on_dashboard(), "User must be on dashboard to logout"
        time.sleep(5)

        logout_btn = None
        logout_locators = self.LOGOUT_BUTTON

        for locator in logout_locators:
            try:
                element = self.pageinfo.find_element(locator, timeout=5)
                if not element:
                    continue

                self.javascript.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)

                try:
                    element.click()
                    logout_btn = element
                    self.logger.info(f"Clicked logout via normal click: {locator}")
                except Exception as e:
                    self.logger.warning(f"Normal click failed ({e}), trying JS click...")
                    self.javascript.execute_script("arguments[0].click();", element)
                    logout_btn = element
                    self.logger.info("Clicked logout via JavaScript")

                time.sleep(3)

                current_url = self.navigator.get_current_url().lower()
                if any(x in current_url for x in ["login", "auth"]):
                    self.logger.success("Successfully logged out and redirected.")
                    return True

                if self.waiter.wait_for_visible(self.LOGIN_BUTTON, timeout=5):
                    self.logger.success("Successfully logged out — login button visible.")
                    return True

            except Exception as e:
                self.logger.debug(f"Logout attempt failed for {locator}: {e}")
                self._last_interacted_element = logout_btn
                continue

        self.logger.error("No logout button found or clickable.")
        return False

    def is_user_on_dashboard(self):
        """Check if the user is currently on the dashboard.

        Tries each ``DASHBOARD_INDICATORS`` locator first; if none are
        visible, falls back to ``_fallback_dashboard_check`` which looks
        for dashboard-related text in the page instead.

        Returns:
            bool: True if a dashboard UI element or fallback text
                combination is found, False otherwise.
        """
        try:
            for ind in self.DASHBOARD_INDICATORS:
                element = self.waiter.wait_for_visible(ind, timeout=5)
                if element:
                    self.logger.info(f"Dashboard verified via UI element: {ind}")
                    return True

            self.logger.warning("No dashboard UI elements found, using text check")
            return self._fallback_dashboard_check()

        except Exception as e:
            self.logger.error(f"Dashboard check failed: {e}")
            return False

    def _fallback_dashboard_check(self):
        """Check for the dashboard via page text when UI locators fail.

        Requires at least one "primary" phrase (e.g. "Bookings") AND at
        least one "secondary" phrase (e.g. "Past Trips") to both be
        present, to reduce false positives from a single generic word
        appearing elsewhere on the page.

        Returns:
            bool: True if both a primary and a secondary indicator phrase
                are found, False otherwise.
        """
        try:
            primary_indicators = [
                self.pageinfo._page_contains_silent("Bookings"),
                self.pageinfo._page_contains_silent("Upcoming Trips"),
                self.pageinfo._page_contains_silent("Manage your flights and travel plans"),
            ]

            secondary_indicators = [
                self.pageinfo._page_contains_silent("Past Trips"),
                self.pageinfo._page_contains_silent("Book flight"),
                self.pageinfo._page_contains_silent("Visa Applications"),
            ]

            # NOTE: has_primary/has_secondary are computed but not reused below -
            # the condition recomputes any(...) on both lists again. Harmless
            # (same result) but redundant.
            has_primary = any(primary_indicators)
            has_secondary = any(secondary_indicators)

            if any(primary_indicators) and any(secondary_indicators):
                self.logger.info("User is on bookings dashboard (text-based check)")
                return True

            self.logger.error("User is not on bookings dashboard")
            return False

        except Exception as e:
            self.logger.debug(f"Fallback dashboard check failed: {e}")
            return False

    def get_credentials_from_env(self):
        """Read test login credentials from environment variables.

        Returns:
            tuple[str or None, str or None]: ``(email, password)`` read
                from ``TEST_USER_EMAIL`` / ``TEST_USER_PASSWORD``; either
                may be None if not set (a warning is logged in that case,
                but nothing is raised).
        """
        email = os.getenv("TEST_USER_EMAIL")
        password = os.getenv("TEST_USER_PASSWORD")

        if not email or not password:
            self.logger.warning("Test credentials not found in environment")

        return email, password
    
    def wait_until_on_dashboard(self, timeout=15):
        """Wait until the user reaches the dashboard, refreshing once if stuck.

        If the initial wait times out and the app appears stuck on the
        login/auth route, refreshes the page once and gives it one more
        (shorter) chance to reach the dashboard - works around occasional
        stalled client-side navigation after login.

        Args:
            timeout (int): Seconds for the initial wait. Defaults to 15.

        Returns:
            bool: True if the dashboard was reached (before or after the
                refresh), False otherwise.
        """
        try:
            # First, try the normal wait
            WebDriverWait(self.driver, timeout).until(
                lambda d: self.is_user_on_dashboard()
            )
            return True
        except Exception:
            # If that fails, check if we're stuck on login page
            current_url = self.driver.current_url.lower()
            if "login" in current_url or "auth" in current_url:
                self.logger.info("🔄 Page seems stuck on login, refreshing...")
                
                # Refresh the page
                self.driver.refresh()
                
                # Wait for page to be in ready state
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                
                # Try one more time after refresh
                try:
                    WebDriverWait(self.driver, 5).until(
                        lambda d: self.is_user_on_dashboard()
                    )
                    return True
                except Exception:
                    pass
            
            return False
        
    def wait_until_logged_out(self, timeout=10):
        """Wait until the URL leaves login/auth or the dashboard check fails.

        Args:
            timeout (int): Seconds to wait. Defaults to 10.

        Returns:
            bool: True if any of the logged-out conditions was met in
                time, False on timeout.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: (
                    "login" in d.current_url.lower()
                    or "/auth" in d.current_url.lower()
                    or not self.is_user_on_dashboard()
                )
            )
            return True
        except Exception:
            return False
    
    def wait_for_login_to_settle(self, timeout=15):
        """
        Wait until the in-flight login request appears to have finished.

        Considers the request settled once ANY of these holds: the login
        button is no longer visible, the login button is no longer
        enabled, or the URL has moved away from "login".

        NOTE: the "login button enabled again" wording in earlier
        versions of this docstring didn't match the code - the condition
        actually fires when the button becomes *disabled* (not enabled),
        which is what you'd expect while a submit spinner is showing.

        Args:
            timeout (int): Seconds to wait. Defaults to 15.

        Returns:
            bool: True once one of the settle conditions is met, False on
                timeout.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: (
                    not self.element.is_visible(self.LOGIN_BUTTON)
                    or not self.element.is_enabled(self.LOGIN_BUTTON)
                    or "login" not in d.current_url.lower()
                )
            )
            return True
        except Exception:
            return False

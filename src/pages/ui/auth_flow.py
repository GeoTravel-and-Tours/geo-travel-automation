# src/pages/auth_flow.py

from selenium.webdriver.common.by import By
from src.core.base_page import BasePage
import time
import os
from selenium.webdriver.support.ui import WebDriverWait


class AuthFlow(BasePage):
    """
    Combined authentication flow - Login and Logout
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
        super().__init__(driver)
        self.login_path = "auth/login"
        self.last_toast = None

    def open_login_page(self):
        """Navigate to login page"""
        self.open(self.login_path)
        self.logger.info("🔐 Navigated to login page")
        return self

    def wait_for_login_page(self, timeout=10):
        """Wait for login page to load"""
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
        Complete login flow

        Args:
            username: User email/username
            password: User password

        Returns:
            bool: True if login successful, False otherwise
        """
        self.logger.info(f"Attempting login for user: {username}")
        login_btn = None

        try:
            self.element.type(self.EMAIL_INPUT, username)
            self.element.type(self.PASSWORD_INPUT, password)
            login_btn = self.element.click(self.LOGIN_BUTTON)
            self.logger.info("Login attempt completed")
            
            self.wait_for_login_to_settle(timeout=20)

            return self.is_login_successful()

        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            self._last_interacted_element = login_btn
            return False

    def _wait_for_any_dashboard_indicator(self, timeout=15):
        """Wait for ANY of the dashboard indicators to appear"""
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

    def is_login_successful(self, timeout=25):
        self.logger.info("🔍 Verifying login status...")

        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: "/dashboard" in d.current_url.lower()
            )

            current_url = self.navigator.get_current_url().lower()
            self.logger.info(f"Redirected to: {current_url}")

            if self._wait_for_any_dashboard_indicator(timeout=10):
                self.logger.success("Login confirmed – Dashboard detected.")
                return True

            self.logger.error("Dashboard URL reached but UI not loaded.")
            return False

        except Exception as e:
            self.logger.error(f"Login did not reach dashboard: {e}")
            return False
        
    def get_last_toast(self):
        """Return the last captured toast message (if any)."""
        return self.last_toast

    def get_toast_error_message(self, max_wait=10):
        """Capture toast error message with better filtering"""
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
        """Perform logout action and verify success"""
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
        """Check if user is on dashboard by verifying ANY of the dashboard indicators"""
        try:
            for indicator in self.DASHBOARD_INDICATORS:
                try:
                    if self.element.is_visible(indicator):
                        self.logger.info(f"Dashboard verified by: {indicator}")
                        return True
                except:
                    continue
                
            self.logger.warning("No dashboard UI elements found, falling back to text check")
            return self._fallback_dashboard_check()

        except Exception as e:
            self.logger.error(f"Dashboard check failed: {e}")
            return False

    def _fallback_dashboard_check(self):
        """Fallback method to check dashboard by page content"""
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

            has_primary = any(primary_indicators)
            has_secondary = any(secondary_indicators)

            if has_primary and has_secondary:
                self.logger.info("User is on bookings dashboard (text-based check)")
                return True

            self.logger.error("User is not on bookings dashboard")
            return False

        except Exception as e:
            self.logger.debug(f"Fallback dashboard check failed: {e}")
            return False

    def get_credentials_from_env(self):
        """Get test credentials from environment variables"""
        email = os.getenv("TEST_USER_EMAIL")
        password = os.getenv("TEST_USER_PASSWORD")

        if not email or not password:
            self.logger.warning("Test credentials not found in environment")

        return email, password
    
    def wait_until_on_dashboard(self, timeout=10):
        """Wait until user is on dashboard after login"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: self.is_user_on_dashboard()
            )
            return True
        except Exception:
            return False
        
    def wait_until_logged_out(self, timeout=10):
        """Wait until user is logged out and redirected from dashboard"""
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
        Wait until login request finishes:
        - login button enabled again OR
        - spinner disappears OR
        - URL changes away from login
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

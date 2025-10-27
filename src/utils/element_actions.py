# src/utils/element_actions.py

import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils.logger import GeoLogger


class ElementActions:
    """Unified element finding and interaction utility"""

    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
        self.logger = GeoLogger(name="ElementActions")

    # Finding methods
    def find(self, locator, timeout=None):
        """Find element with wait"""
        wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_element_located(locator))

    def find_all(self, locator, timeout=None):
        """Find all matching elements"""
        wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_all_elements_located(locator))

    def find_visible(self, locator, timeout=None):
        """Find visible element with proper locator handling"""
        try:
            # Debug: print what we're actually receiving
            self.logger.debug(f"Looking for element with locator: {locator}, type: {type(locator)}")

            # Ensure locator is properly formatted
            if not isinstance(locator, tuple) or len(locator) != 2:
                raise ValueError(f"Invalid locator format: {locator}. Expected tuple (by, value)")

            wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
            return wait.until(EC.visibility_of_element_located(locator))
        except Exception as e:
            self.logger.error(f"Element not found: {locator} - Error: {e}")
            raise

    # Interaction methods
    def click(self, locator, timeout=None):
        """Click element"""
        element = self.find_visible(locator, timeout)
        element.click()

    def type(self, locator, text, clear_first=True, timeout=None):
        """Type text into field with proper locator handling"""
        try:
            # Ensure locator is passed as a single argument
            element = self.find_visible(locator, timeout)
            if clear_first:
                element.clear()
                time.sleep(0.1)
            element.send_keys(text)
            return True
        except Exception as e:
            self.logger.error(f"Failed to type into {locator}: {e}")
            raise

    def get_text(self, locator, timeout=None):
        """Get element text"""
        return self.find(locator, timeout).text.strip()

    def get_attribute(self, locator, attribute, timeout=None):
        """Get element attribute"""
        return self.find(locator, timeout).get_attribute(attribute)

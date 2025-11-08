# src/utils/wait_strategy.py

import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from src.utils.logger import GeoLogger


class WaitStrategy:
    """Dedicated class for wait conditions methods"""

    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
        self.logger = GeoLogger(name="WaitStrategy")
        
    def wait(self, seconds):
        """Simple time.sleep wrapper for explicit waits"""
        self.logger.debug(f"Waiting for {seconds} seconds")
        time.sleep(seconds)

    def wait_for_visible(self, locator, timeout=None):
        """Wait for element to be visible with proper locator handling"""
        try:
            # Debug the locator
            self.logger.debug(f"Waiting for element: {locator}")

            timeout = timeout
            wait = WebDriverWait(self.driver, timeout)

            # Ensure locator is passed as single argument
            element = wait.until(EC.visibility_of_element_located(locator))
            return element
        except TimeoutException:
            self.logger.warning(f"Element not visible within {timeout}s: {locator}")
            raise

    def wait_for_invisible(self, locator, timeout=None):
        """Wait for element to be invisible"""
        wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
        return wait.until(EC.invisibility_of_element_located(locator))

    def wait_for_clickable(self, locator, timeout=None):
        """Wait for element to be clickable"""
        wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
        return wait.until(EC.element_to_be_clickable(locator))

    def wait_for_text_present(self, locator, text, timeout=None):
        """Wait for text to be present in element"""
        wait = self.wait if timeout is None else WebDriverWait(self.driver, timeout)
        return wait.until(EC.text_to_be_present_in_element(locator, text))

    def wait_for_present(self, locator, timeout=10):
        """Wait for element to be present in DOM (not necessarily visible/clickable)"""
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_element_located(locator))
    
    def wait_for_page_load(self, timeout=10):
        """Wait for page to finish loading"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            self.logger.debug("Page loaded completely")
        except TimeoutException:
            self.logger.warning("Page load timeout, but continuing")

    def wait_for_element(self, locator, element_name, timeout=10):
        """Robust helper to wait for and get element with detailed logging"""
        self.logger.info(f"Waiting for {element_name} (timeout: {timeout}s)...")

        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            self.logger.info(f"✓ {element_name} found, waiting for it to be visible...")

            element = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            self.logger.info(f"✓ {element_name} is visible, waiting for it to be clickable...")

            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            self.logger.info(f"✓ {element_name} is clickable")

            return element

        except TimeoutException:
            self.logger.error(f"⏰ Timeout waiting for {element_name} after {timeout} seconds")
            raise
        except Exception as e:
            self.logger.error(f"❌ Error getting {element_name}: {str(e)}")
            raise
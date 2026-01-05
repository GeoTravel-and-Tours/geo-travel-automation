# src/utils/validation.py

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from src.utils.logger import GeoLogger
from src.utils.wait_strategy import WaitStrategy


class ValidationUtils:
    """Dedicated class for validation and UI verification methods."""

    def __init__(self, element_finder):
        self.finder = element_finder
        self.logger = GeoLogger(name="ValidationUtils")

    def _safe_find(self, locator, timeout=None):
        """Safely find element using tuple or string locator with optional timeout."""
        try:
            if timeout:
                waiter = WaitStrategy(self.finder, timeout)
                return waiter.wait_for_present(locator, timeout)

            if isinstance(locator, tuple):
                return self.finder.find_element(*locator)

            return self.finder.find_element(locator)

        except (NoSuchElementException, TimeoutException) as e:
            self.logger.debug(f"Element not found: {locator} | {e}")
            return None

    def is_element_present(self, locator, timeout=None):
        """Return True if element is present in DOM."""
        element = self._safe_find(locator, timeout)
        present = element is not None
        self.logger.info(f"Element present ({locator}): {present}")
        return present

    def is_element_visible(self, locator, timeout=None):
        """Return True if element is visible to the user."""
        try:
            element = self._safe_find(locator, timeout)
            visible = element.is_displayed() if element else False
            self.logger.info(f"Element visible ({locator}): {visible}")
            return visible
        except Exception as e:
            self.logger.error(f"Error checking visibility for {locator}: {e}")
            return False

    def is_element_enabled(self, locator, timeout=None):
        """Return True if element is enabled and interactable."""
        element = self._safe_find(locator, timeout)
        enabled = element.is_enabled() if element else False
        self.logger.info(f"Element enabled ({locator}): {enabled}")
        return enabled

    def verify_text_present(self, locator, expected_text, timeout=None):
        """Return True if expected text is found within the element."""
        try:
            element = self._safe_find(locator, timeout)
            text_present = expected_text in element.text if element else False
            self.logger.info(f"Text '{expected_text}' present in ({locator}): {text_present}")
            return text_present
        except Exception as e:
            self.logger.error(f"Error verifying text for {locator}: {e}")
            return False

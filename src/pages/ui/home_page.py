# src/pages/home_page.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from src.core.base_page import BasePage
from datetime import datetime
import pytest
import time

class HomePage(BasePage):
    """
    Geo Travel Home Page
    """

    # ===== GEO TRAVEL SPECIFIC LOCATORS =====
    LOGO_PRIMARY = (By.XPATH,"//div[contains(@class,'w-28') and contains(@class,'h-12') and contains(@class,'relative')]//img[@alt='GeoTravel']")
    LOGO_FALLBACK = (By.XPATH, "//img[@alt='GeoTravel']")
    SEARCH_INPUT = (
        By.CSS_SELECTOR,
        'input[type="search"], input[name*="search"], #search',
    )
    SEARCH_BUTTON = (
        By.CSS_SELECTOR,
        'button[type*="submit"], .search-btn, #search-btn',
    )
    NAVIGATION = (By.TAG_NAME, "nav")
    HEADER = (By.TAG_NAME, "header")
    FOOTER = (By.TAG_NAME, "footer")

    # Geo Travel specific content identifiers
    GEO_TRAVEL_KEYWORDS = [
        "geo",
        "travel",
        "destination",
        "booking",
        "tour",
        "package",
        "vacation",
        "adventure",
        "hotel",
        "flight",
        "trip",
        "journey",
        "explore",
        "discover",
        "holiday",
    ]

    def warm_up_site(self):
        """Ping the site once to wake up a sleeping Heroku dyno."""
        self.logger.info("🏁 Warming up site before homepage load...")
        try:
            self.open()
            self.logger.info("Warm-up page opened successfully.")
            time.sleep(5)  # give the app a few seconds to boot
        except Exception as e:
            self.logger.warning(f"Warm-up page failed: {e}")
            
    def wait_for_homepage_load(self, timeout=15, max_retries=3):
        """Wait for homepage to load with retries, keyword validation, and automatic error capturing"""
        
        # First, warm up the site
        self.warm_up_site()
        
        self.logger.info(f"🏠 Waiting for homepage to load (max retries: {max_retries})")

        for attempt in range(1, max_retries + 1):
            self.logger.info(f"Attempt {attempt}/{max_retries}")

            try:
                self.javascript.wait_for_page_load(timeout)
                self.waiter.wait_for_visible((By.TAG_NAME, "body"), timeout)
                self.logger.info("Page body loaded")
                
                # Check for Heroku sleeping error
                if "Application Error" in self.driver.page_source:
                    self.logger.warning("Heroku app might be sleeping. Waiting before retrying...")
                    time.sleep(5 * attempt)
                    continue
                
                # Validate page content as Geo Travel page
                self.logger.info("Validating Geo Travel page...")
                validation_results = self.pageinfo.validate_geo_travel_page()
                confidence_score = validation_results["confidence_score"]
                validation_passed = confidence_score >= 60.0

                if validation_passed:
                    self.logger.info(f"Homepage validation passed! Confidence: {confidence_score:.1f}%")
                    return True
                else:
                    self.logger.warning(f"Page validation failed on attempt {attempt}. Confidence: {confidence_score:.1f}%")

                    if attempt == max_retries:
                        self.logger.error("FINAL ATTEMPT FAILED - Capturing validation failure...")
                        result = self.screenshot.capture_validation_failure(
                            test_name="homepage_validation",
                            validation_results=validation_results,
                            error_message=f"Validation confidence too low: {confidence_score:.1f}%",
                        )

                        if result["screenshot"]:
                            self.logger.error(f"🖼️  Screenshot saved: {result['screenshot']}")
                        if result["html"]:
                            self.logger.error(f"📄 Error report saved: {result['html']}")

                        raise AssertionError(f"Homepage failed after {max_retries} attempts: {e}")

                    time.sleep(5 * attempt)
                    continue

            except Exception as e:
                self.logger.error(f"Homepage load failed on attempt {attempt}: {str(e)}")

                if attempt == max_retries:
                    self.logger.error("FINAL ATTEMPT FAILED - Capturing load failure...")
                    result = self.screenshot.capture_page_load_failure(
                        test_name="homepage_load", error_message=str(e)
                    )

                    if result["screenshot"]:
                        self.logger.error(f"🖼️  Screenshot saved: {result['screenshot']}")
                    if result["html"]:
                        self.logger.error(f"📄 Error report saved: {result['html']}")

                    pytest.fail(f"Homepage failed to load after {max_retries} attempts. Error: {str(e)}")

                time.sleep(5 * attempt)
                continue

        return False

    def is_logo_visible(self):
        """
        Verify the logo is visible on the page.
        Optional full-page screenshot is taken only on failure for reporting.
        """
        for name, locator in [("Primary", self.LOGO_PRIMARY), ("Fallback", self.LOGO_FALLBACK)]:
            try:
                # Wait for the logo element to be visible
                logo_element = self.waiter.wait_for_visible(locator, timeout=15)
                self.driver.execute_script("arguments[0].scrollIntoView(true);", logo_element)

                visible = logo_element is not None
                self.logger.info(f"Logo visible ({name}): {visible}")

                # Logo is present — no need for screenshot
                if visible:
                    return True

            except Exception as e:
                self.logger.warning(f"{name} logo selector failed, trying next option... | {e}")

        # Logo not found — capture full-page screenshot for reporting
        self.logger.error("Logo visibility check failed on both selectors")
        full_screenshot_path = self.screenshot.capture_screenshot(
            filename="Logo_NotFound_FullPage", subfolder="elements"
        )
        self.logger.info(f"Full-page screenshot captured for failure analysis: {full_screenshot_path}")

        return False

    def is_page_loaded_correctly(self):
        """Check if homepage loaded properly - FIXED FOR REACT/Next.js"""
        self.logger.info("Performing page health check")

        try:
            WebDriverWait(self.driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            WebDriverWait(self.driver, 10).until(
                lambda d: d.find_elements(By.TAG_NAME, "body")
                and len(d.find_elements(By.TAG_NAME, "div")) > 0
            )
        except Exception as e:
            self.logger.warning(f"Page load wait failed: {e}")

        checks = {
            "page_has_title": bool(self.driver.title and self.driver.title.strip()),
            "page_has_body": self._check_react_page_structure(),
            "not_error_page": self._check_not_error_page(),
        }

        optional_checks = {
            "has_react_content": self._check_react_content(),
            "has_interactive_elements": self._check_interactive_elements(),
            "has_navigation": self._check_navigation(),
        }

        checks.update(optional_checks)

        for check_name, result in checks.items():
            status = "PASS" if result else "❌ FAIL"
            self.logger.info(f"Health check - {check_name}: {status}")

        critical_checks = ["page_has_title", "page_has_body", "not_error_page"]
        critical_passed = all(checks[check] for check in critical_checks)

        overall_status = "PASS" if critical_passed else "❌ FAIL"
        self.logger.info(f"Page health check overall: {overall_status}")

        return critical_passed, checks

    def _check_react_page_structure(self):
        """Check React/Next.js page structure"""
        try:
            nextjs_indicators = [
                len(self.driver.find_elements(By.TAG_NAME, "body")) > 0,
                len(self.driver.find_elements(By.TAG_NAME, "html")) > 0,
                len(self.driver.find_elements(By.CSS_SELECTOR, "[data-sentry-component]")) > 0,
                len(self.driver.find_elements(By.TAG_NAME, "div")) > 0,
                len(self.driver.page_source) > 1000,
            ]

            visible_checks = [
                self.javascript.execute_script("return document.body != null"),
                self.javascript.execute_script("return document.body.children.length > 0"),
                self.javascript.execute_script("return document.querySelector('*') != null"),
            ]

            return any(nextjs_indicators) and any(visible_checks)
        except Exception as e:
            self.logger.warning(f"React structure check failed: {e}")
            return False

    def _check_react_content(self):
        """Check for React-specific content"""
        try:
            react_components = self.driver.find_elements(By.CSS_SELECTOR, "[data-sentry-component]")
            if len(react_components) > 0:
                return True

            nextjs_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-nextjs]")
            if len(nextjs_elements) > 0:
                return True

            common_elements = [
                (By.TAG_NAME, "h1"),
                (By.TAG_NAME, "h2"),
                (By.TAG_NAME, "a"),
                (By.CSS_SELECTOR, "button"),
                (By.CSS_SELECTOR, "img"),
                (By.CSS_SELECTOR, "input"),
            ]

            for locator in common_elements:
                if len(self.driver.find_elements(*locator)) > 0:
                    return True

            return False
        except:
            return False

    def _check_interactive_elements(self):
        """Check for interactive elements in React app"""
        try:
            interactive_elements = [
                (By.TAG_NAME, "button"),
                (By.TAG_NAME, "a"),
                (By.CSS_SELECTOR, "[role='button']"),
                (By.CSS_SELECTOR, "input"),
                (By.CSS_SELECTOR, "select"),
            ]

            for locator in interactive_elements:
                elements = self.driver.find_elements(*locator)
                if len(elements) > 0:
                    return True
            return False
        except:
            return False

    def _check_navigation(self):
        """Check for navigation elements"""
        try:
            nav_indicators = [
                (By.TAG_NAME, "a"),
                (By.CSS_SELECTOR, "[role='navigation']"),
                (By.CSS_SELECTOR, "nav"),
                (By.CSS_SELECTOR, "[href]"),
            ]

            for locator in nav_indicators:
                if len(self.driver.find_elements(*locator)) > 0:
                    return True
            return False
        except:
            return False

    def _check_not_error_page(self):
        """Enhanced error page check"""
        try:
            # Check for common error keywords in the page title
            title = self.driver.title.lower()
            obvious_errors = ["404", "500", "page not found", "server error"]
            if any(error in title for error in obvious_errors):
                self.logger.error(f"Error detected in page title: {title}")
                return False

            # Check for specific error elements on the page
            error_indicators = [
                ("css selector", ".error-banner"),
                ("css selector", ".error-message"),
                ("xpath", "//*[contains(text(), 'Error')]"),
            ]

            for by, value in error_indicators:
                if len(self.driver.find_elements(by, value)) > 0:
                    self.logger.error(f"Error element detected: {by}={value}")
                    return False

            # Optional: Check HTTP status code if available
            if hasattr(self.driver, "get_status_code"):
                status_code = self.driver.get_status_code()
                if status_code >= 400:
                    self.logger.error(f"HTTP error detected: Status code {status_code}")
                    return False

            return True
        except Exception as e:
            self.logger.error(f"Error during error page check: {e}")
            return True

    def validate_as_geo_travel_page(self, min_confidence=60.0):
        """Validate that this is actually a Geo Travel page"""
        validation_results = self.pageinfo.validate_geo_travel_page()
        is_valid = validation_results["confidence_score"] >= min_confidence
        
        self.logger.info(
            f"Geo Travel page validation: {'VALID' if is_valid else '❌ INVALID'} "
            f"(Confidence: {validation_results['confidence_score']:.1f}%)"
        )

        return is_valid, validation_results
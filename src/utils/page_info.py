from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils.logger import GeoLogger


class PageInfoUtils:
    """Dedicated class for extracting and validating page information"""

    def __init__(self, driver, logger=None):
        self.driver = driver
        self.logger = logger or GeoLogger(name="PageInfoUtils")

    def get_page_html(self, driver=None):
        """Get the entire page HTML content"""
        driver = driver or self.driver
        return driver.page_source

    def get_body_html(self, driver=None):
        """Get the body HTML content specifically"""
        driver = driver or self.driver
        try:
            body_element = driver.find_element(By.TAG_NAME, "body")
            return body_element.get_attribute("innerHTML")
        except:
            return self.get_page_html(driver)  # Fallback to full page source

    def get_body_text(self, driver=None):
        """Get all visible text from the body"""
        driver = driver or self.driver
        try:
            body_element = driver.find_element(By.TAG_NAME, "body")
            return body_element.text.strip()
        except:
            return ""

    def find_element(self, locator, timeout=10, driver=None):
        """Find element with timeout (basic implementation)"""
        driver = driver or self.driver

        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_element_located(locator))

    def assert_page_contains(
        self, expected_text, element_locator=None, timeout=10, driver=None
    ):
        """Assert that page contains expected text"""
        driver = driver or self.driver
        try:
            if element_locator:
                # Check specific element
                element = self.find_element(element_locator, timeout, driver)
                actual_text = element.text
            else:
                # Check entire page
                actual_text = self.get_body_text(driver)

            assert (
                expected_text.lower() in actual_text.lower()
            ), f"Expected text '{expected_text}' not found. Actual content: {actual_text[:200]}..."
            self.logger.success(f"Page contains expected text: '{expected_text}'")
            return True

        except Exception as e:
            self.logger.error(f"Text assertion failed: {e}")
            raise

    def _page_contains_silent(self, text, element_locator=None, timeout=3):
        """Check if page contains text without raising exceptions"""
        try:
            driver = self.driver
            if element_locator:
                element = self.find_element(element_locator, timeout, driver)
                actual_text = element.text
            else:
                actual_text = self.get_body_text(driver)

            return text.lower() in actual_text.lower()
        except Exception:
            return False

    def assert_page_contains_keywords(
        self, keywords, element_locator=None, timeout=10, driver=None
    ):
        """Assert that page contains all specified keywords"""
        driver = driver or self.driver
        try:
            if element_locator:
                element = self.find_element(element_locator, timeout, driver)
                content = element.text.lower()
            else:
                content = self.get_body_text(driver).lower()

            missing_keywords = []
            for keyword in keywords:
                if keyword.lower() not in content:
                    missing_keywords.append(keyword)

            assert (
                len(missing_keywords) == 0
            ), f"Missing keywords: {missing_keywords}. Content: {content[:300]}..."
            self.logger.success(f"Page contains all keywords: {keywords}")
            return True

        except Exception as e:
            self.logger.error(f"Keywords assertion failed: {e}")
            raise

    def validate_geo_travel_page(
        self, expected_elements=None, expected_keywords=None, driver=None
    ):
        """
        Comprehensive validation that this is a genuine Geo Travel page
        """
        driver = driver or self.driver
        validation_results = {}

        # Default expected elements for Geo Travel pages
        if expected_elements is None:
            expected_elements = [
                (By.TAG_NAME, "html"),
                (By.TAG_NAME, "body"),
                (By.TAG_NAME, "head"),
            ]

        # Default expected keywords for Geo Travel
        if expected_keywords is None:
            expected_keywords = [
                "geo",
                "travel",
                "destination",
                "book",
                "tour",
                "package",
                "hotel",
                "flight",
                "vacation",
                "adventure",
            ]

        # Validate HTML structure
        self.logger.info("Validating page HTML structure...")
        for element_type, selector in expected_elements:
            try:
                self.find_element((element_type, selector), driver=driver)
                validation_results[f"element_{selector}"] = True
                self.logger.debug(f"✅ Found {selector} element")
            except:
                validation_results[f"element_{selector}"] = False
                self.logger.warning(f"⚠️ Missing {selector} element")

        # Validate content keywords
        self.logger.info("Validating page content keywords...")
        body_text = self.get_body_text(driver).lower()
        page_source = self.get_page_html(driver).lower()

        found_keywords = []
        missing_keywords = []

        for keyword in expected_keywords:
            if keyword.lower() in body_text or keyword.lower() in page_source:
                found_keywords.append(keyword)
                validation_results[f"keyword_{keyword}"] = True
            else:
                missing_keywords.append(keyword)
                validation_results[f"keyword_{keyword}"] = False

        # Calculate confidence score
        total_checks = len(expected_elements) + len(expected_keywords)
        passed_checks = sum(validation_results.values())
        confidence_score = (
            (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        )

        validation_results["confidence_score"] = confidence_score
        validation_results["found_keywords"] = found_keywords
        validation_results["missing_keywords"] = missing_keywords

        # Log validation results
        self.logger.info(f"Page validation confidence: {confidence_score:.1f}%")
        self.logger.info(f"Found keywords: {found_keywords}")
        if missing_keywords:
            self.logger.warning(f"Missing keywords: {missing_keywords}")

        return validation_results

    def is_geo_travel_page(self, min_confidence=60.0, driver=None):
        """Check if this is likely a Geo Travel page"""
        driver = driver or self.driver
        validation = self.validate_geo_travel_page(driver=driver)
        return validation["confidence_score"] >= min_confidence

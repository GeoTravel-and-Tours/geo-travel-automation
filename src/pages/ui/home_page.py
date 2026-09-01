"""
src/pages/ui/home_page.py

Page Object for the Geo Travel homepage.

Covers:
    1. Warm-up & load    - ping the site once to wake a sleeping Heroku
                            dyno, then wait (with retries) for the
                            homepage to load and validate its content.
    2. Logo check        - verify the site logo is visible, with a
                            fallback locator and failure screenshot.
    3. Health check       - a broader "is this actually a working
                            React/Next.js page and not an error page"
                            check, used as a general smoke check.
    4. Geo Travel identity - confirm the loaded page is genuinely a Geo
                            Travel page via a confidence-score heuristic
                            (delegated to ``PageInfoUtils.validate_geo_travel_page``).

Tests typically call ``wait_for_homepage_load()`` first (which itself
calls ``warm_up_site()``), then ``is_logo_visible()`` and/or
``is_page_loaded_correctly()`` / ``validate_as_geo_travel_page()`` as
additional assertions.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from src.core.base_page import BasePage
from datetime import datetime
import pytest
import time

class HomePage(BasePage):
    """
    Geo Travel Home Page.

    Locators cover the logo (with a fallback selector), search box, and
    top-level layout landmarks (nav/header/footer). ``GEO_TRAVEL_KEYWORDS``
    is a word list used elsewhere (via ``PageInfoUtils``) for the
    confidence-score content validation referenced throughout this class.

    NOTE: unlike the other page objects in this package, this class calls
    ``pytest.fail(...)`` directly from ``wait_for_homepage_load`` -
    coupling this Page Object to the pytest test framework rather than
    only raising/returning like the rest of the class (and the rest of
    this package) does.
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
        """Ping the site once to wake up a sleeping Heroku dyno.

        Best-effort only: failures are logged as a warning and swallowed
        rather than raised, since this is just a preparatory step before
        the real homepage load check.
        """
        self.logger.info("🏁 Warming up site before homepage load...")
        try:
            self.open()
            self.logger.info("Warm-up page opened successfully.")
            time.sleep(5)  # give the app a few seconds to boot
        except Exception as e:
            self.logger.warning(f"Warm-up page failed: {e}")

    def wait_for_homepage_load(self, timeout=15, max_retries=3):
        """Wait for the homepage to load, retrying on Heroku sleep or low-confidence content.

        On each attempt: waits for page load and a visible ``<body>``,
        checks for the Heroku "Application Error" sleeping-dyno page
        (retrying with backoff if found), then validates the page is
        genuinely a Geo Travel page via
        ``self.pageinfo.validate_geo_travel_page()`` - a confidence score
        of at least 60% is required to pass. On the final failed attempt,
        captures a screenshot/HTML report before failing.

        FIXME: in the final-attempt validation-failure branch (not the
        exception branch), the assertion raised is
        ``AssertionError(f"...: {e}")`` - but ``e`` is never defined
        anywhere in that branch (it only exists in the separate
        ``except Exception as e:`` block below). This raises
        ``NameError: name 'e' is not defined`` instead of the intended
        ``AssertionError`` whenever the homepage loads successfully but
        content validation keeps failing across all retries.

        Args:
            timeout (int): Seconds to wait for page-load conditions per
                attempt. Defaults to 15.
            max_retries (int): Max number of attempts before giving up.
                Defaults to 3.

        Returns:
            bool: True once validation passes; False if the loop
                completes without an explicit return (unreachable in
                practice - every path through the loop either returns
                True, raises, or calls ``pytest.fail``/continues, and the
                final iteration always hits one of those).

        Raises:
            AssertionError: On the final attempt if content validation
                still fails (though see the FIXME above - this currently
                manifests as ``NameError`` instead).
        """
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

                        # FIXME: `e` is not defined in this branch - see the FIXME
                        # in the docstring above. This raises NameError instead of
                        # the intended AssertionError.
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

        Tries ``LOGO_PRIMARY`` first, then falls back to the looser
        ``LOGO_FALLBACK`` locator. A full-page screenshot is captured
        only if both selectors fail, for failure-report purposes.

        Returns:
            bool: True as soon as either locator confirms the logo is
                visible, False if neither does.
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
        """Run a broad health check tailored to React/Next.js pages.

        Combines three "critical" checks (has a title, has a body/React
        structure, isn't an error page) with three "optional" checks
        (React-specific content, interactive elements, navigation) that
        are reported but don't affect the overall pass/fail result.

        Returns:
            tuple[bool, dict]: ``(critical_passed, checks)`` where
                ``critical_passed`` is True only if all three critical
                checks pass, and ``checks`` is a dict of every check name
                (critical and optional) to its bool result.
        """
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
        """Check for basic React/Next.js DOM structure and non-empty body.

        Returns:
            bool: True if at least one structural indicator AND at least
                one JS-based "body is populated" check both pass, False
                otherwise (including on error).
        """
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
        """Check for React/Next.js markers or common content elements.

        Returns:
            bool: True if any Sentry/Next.js data attribute or common
                element (h1/h2/a/button/img/input) is found, False
                otherwise.
        """
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
        """Check for any interactive elements (buttons, links, inputs, etc.).

        Returns:
            bool: True if at least one interactive element is found,
                False otherwise (including on error).
        """
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
        """Check for any navigation-like elements (nav, links, role=navigation).

        Returns:
            bool: True if at least one navigation indicator is found,
                False otherwise (including on error).
        """
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
        """Check the page isn't showing an obvious error state.

        Looks for error keywords in the title, known error-element
        selectors, and (if available) an HTTP status code >= 400.

        NOTE: fails open - if the check itself raises, this returns True
        (i.e. "not an error page") rather than False, so an exception
        here won't block ``is_page_loaded_correctly`` from passing.

        Returns:
            bool: False if any error indicator is found, True otherwise
                (including when the check itself errors).
        """
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
        """Validate that the current page is genuinely a Geo Travel page.

        Delegates the actual scoring to
        ``self.pageinfo.validate_geo_travel_page()`` (see
        ``GEO_TRAVEL_KEYWORDS`` above) and compares against
        ``min_confidence``.

        Args:
            min_confidence (float): Minimum confidence score (0-100)
                required to consider the page valid. Defaults to 60.0.

        Returns:
            tuple[bool, dict]: ``(is_valid, validation_results)`` - the
                pass/fail bool and the full results dict from
                ``validate_geo_travel_page`` (including the confidence
                score and whatever detail it provides).
        """
        validation_results = self.pageinfo.validate_geo_travel_page()
        is_valid = validation_results["confidence_score"] >= min_confidence
        
        self.logger.info(
            f"Geo Travel page validation: {'VALID' if is_valid else '❌ INVALID'} "
            f"(Confidence: {validation_results['confidence_score']:.1f}%)"
        )

        return is_valid, validation_results
# src/core/test_base.py

import time
import pytest
import os
from datetime import datetime
from selenium.common.exceptions import WebDriverException
from utils.notifications import slack_notifier
from utils.reporting import smoke_reporting
from datetime import datetime
from src.utils.screenshot import ScreenshotUtils


class TestBase:
    """Enhanced test base class with comprehensive reporting"""

    def setup_method(self, method):
        """Setup before each test method"""
        self.test_name = method.__name__
        self.test_start_time = time.time()

        print(f"Starting test: {self.test_name}")

        # Store method for later reference
        self.current_method = method

    def teardown_method(self, method):
        """Teardown after each test method"""
        duration = time.time() - self.test_start_time

        # Use pytest's internal test result (most reliable)
        test_status = "PASS"
        error_message = None

        # Access the actual test result from pytest
        try:
            # This gets the actual test result from pytest
            if hasattr(self, "_test_outcome"):
                outcome = self._test_outcome
                if hasattr(outcome, "result"):
                    result = outcome.result
                    if result and hasattr(result, "failed") and result.failed:
                        test_status = "FAIL"
                        if hasattr(result, "exception") and result.exception:
                            error_message = str(result.exception)
        except Exception as e:
            print(f"Error getting test result: {e}")
            # Fallback: if we can't determine, assume pass
            test_status = "PASS"

        # Capture screenshot on failure
        screenshot_path = None
        if test_status == "FAIL":
            screenshot_path = self._capture_screenshot()

        # Add result to reporter
        smoke_reporting.add_test_result(
            test_name=self.test_name,
            status=test_status,
            error_message=error_message,
            screenshot_path=screenshot_path,
            duration=duration,
        )

        print(f"Final Status: {test_status} | Duration: {duration:.2f}s")

    def _capture_screenshot(self, name=None, driver=None):
        """
        Capture screenshot helper used from tests / teardown.
        Returns path to saved screenshot or None.
        Uses ScreenshotUtils to ensure consistent storage and HTML generation.
        """
        try:
            driver = driver or getattr(self, "driver", None)
            if not driver:
                return None

            tester = ScreenshotUtils(driver)
            test_name = name or getattr(self, "test_name", getattr(self, "nodeid", "unnamed_test"))
            result = tester.capture_screenshot_on_failure(
                test_name=test_name,
                error_message="Captured by TestBase._capture_screenshot"
            )
            return result.get("screenshot")
        except Exception as e:
            # don't raise from a screenshot helper
            try:
                print(f"Failed to capture screenshot: {e}")
            except Exception:
                pass
            return None

    def mark_test_failed(self, error_message):
        """Manually mark test as failed"""
        self._test_failed = True
        self._error_message = error_message

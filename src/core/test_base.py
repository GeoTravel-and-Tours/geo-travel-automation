"""Optional mixin base class for pytest test classes needing smoke reporting.

Test classes that inherit from ``TestBase`` (instead of, or in
addition to, subclassing page objects) get automatic per-test timing,
pass/fail detection, failure screenshots, and result recording into
the shared ``smoke_reporting`` reporter - all via pytest's
``setup_method``/``teardown_method`` hooks, so individual test methods
don't need to call any of this explicitly.

Pass/fail status is read from ``self._test_outcome_status`` /
``self._test_outcome_error``, which conftest.py's
``pytest_runtest_makereport`` hookwrapper stashes onto the test
instance once it has computed the real result for the "call" phase
(see that hook for how status/error_message are derived from pytest's
own report). ``mark_test_failed()`` can additionally force a FAIL
regardless of what pytest's own report says, for tests that want to
flag a soft failure without raising.
"""

import time
import pytest
import os
from datetime import datetime
from selenium.common.exceptions import WebDriverException
from src.utils.notifications import slack_notifier
from src.utils.reporting import smoke_reporting
from datetime import datetime
from src.utils.screenshot import ScreenshotUtils


class TestBase:
    """Mixin providing setup/teardown-driven test reporting for pytest.

    Tracks per-test timing (``self.test_name``,
    ``self.test_start_time``, ``self.current_method``) and, at
    teardown, determines pass/fail status, captures a screenshot on
    failure, and records the result via ``smoke_reporting``.

    Relies on ``self._test_outcome_status``/``self._test_outcome_error``
    being set by conftest.py's ``pytest_runtest_makereport`` hook (see
    module docstring) and on ``self.driver`` being set by the
    subclass/fixture for screenshot capture to work.
    """

    def setup_method(self, method):
        """Record the test name and start time before each test method runs.

        Args:
            method (Callable): The test method pytest is about to run
                (injected automatically by pytest).
        """
        self.test_name = method.__name__
        self.test_start_time = time.time()

        print(f"Starting test: {self.test_name}")

        # Store method for later reference
        self.current_method = method

    def teardown_method(self, method):
        """Determine the test's outcome, capture a screenshot on failure, and report it.

        Reads the pass/fail result stashed by conftest.py's
        ``pytest_runtest_makereport`` hook (``self._test_outcome_status``/
        ``self._test_outcome_error``), then lets ``mark_test_failed()``
        override it to FAIL if it was called during the test, takes a
        screenshot if the test failed, and forwards the result to
        ``smoke_reporting.add_test_result``.

        Args:
            method (Callable): The test method pytest just ran
                (injected automatically by pytest; unused here beyond
                pytest's calling convention).
        """
        duration = time.time() - self.test_start_time

        test_status = getattr(self, "_test_outcome_status", "PASS")
        error_message = getattr(self, "_test_outcome_error", None)

        # A manual mark_test_failed() call always wins, since pytest's own
        # report won't show FAIL for a test that didn't raise.
        if getattr(self, "_test_failed", False):
            test_status = "FAIL"
            error_message = getattr(self, "_error_message", error_message)

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
        """Capture a failure screenshot via ``ScreenshotUtils``.

        Args:
            name (str, optional): Name to associate with the
                screenshot. Falls back to ``self.test_name``, then
                ``self.nodeid``, then "unnamed_test".
            driver (WebDriver, optional): Driver to screenshot. Falls
                back to ``self.driver`` if not provided.

        Returns:
            str | None: Path to the saved screenshot, or None if no
            driver was available or the capture failed (errors are
            swallowed and printed rather than raised, since a
            screenshot helper failing shouldn't fail the test itself).
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
        """Manually flag the current test as failed.

        Sets ``self._test_failed``/``self._error_message``, which
        ``teardown_method`` reads and uses to override the reported
        status to FAIL - useful for a test that wants to record a
        failure without raising an exception itself.

        Args:
            error_message (str): Description of why the test is being
                marked as failed.
        """
        self._test_failed = True
        self._error_message = error_message

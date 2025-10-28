# conftest.py

import os
import time
import shutil
from pathlib import Path
import html as html_escape
import pytest
from datetime import datetime
from pytest_html import extras

from src.core.driver_factory import driver_factory
from src.utils.reporting import smoke_reporting
from src.utils.reporting import get_suite_reporter
from src.utils.screenshot import ScreenshotUtils
from configs.environment import EnvironmentConfig
from src.utils.notifications import slack_notifier
from src.utils.logger import GeoLogger

from src.pages.api.auth_api import AuthAPI
from src.pages.api.flight_api import FlightAPI

logger = GeoLogger("conftest")

# NEW: Global flag to track environment status
environment_available = True
environment_skip_info = None

def pytest_addoption(parser):
    """Add command line option to skip environment check"""
    parser.addoption(
        "--skip-env-check",
        action="store_true",
        default=False,
        help="Skip environment availability check"
    )
    
def pytest_configure(config):
    """Check environment availability before test session starts"""
    global environment_available, environment_skip_info
    
    # Check if we should skip environment check
    skip_env_check = config.getoption("--skip-env-check") or False
    
    if not skip_env_check:
        logger.info("Checking environment availability...")
        environment = EnvironmentConfig.TEST_ENV
        base_url = EnvironmentConfig.get_base_url()
        
        if not EnvironmentConfig.is_environment_accessible():
            # Environment is down - set up skipping mechanism
            config.environment_down = True
            environment_available = False
            
            # Store skip info for reporting
            environment_skip_info = {
                'environment': environment,
                'url': base_url,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'check_type': 'UI'  # Default to UI environment check
            }
            
            logger.error(f"Environment {environment} ({base_url}) is not accessible after multiple attempts")
            logger.info("Tests will be skipped due to environment unavailability")
            
        else:
            config.environment_down = False
            environment_available = True
            logger.success("Environment is accessible - proceeding with tests")
    else:
        config.environment_down = False
        environment_available = True
        logger.info("Environment check skipped")


def pytest_collection_modifyitems(config, items):
    """Skip all tests if environment is down with proper reporting"""
    global environment_available, environment_skip_info
    
    if getattr(config, 'environment_down', False) and not environment_available:
        skip_env = pytest.mark.skip(reason=f"Environment {environment_skip_info['environment']} is not accessible")
        
        for item in items:
            item.add_marker(skip_env)
        
        # Store test count for reporting
        config.skipped_tests_count = len(items)
        config.environment_skip_info = environment_skip_info.copy()
        config.environment_skip_info['skipped_tests'] = len(items)
        config.environment_skip_info['test_names'] = [item.nodeid for item in items]
        
        logger.info(f"Marked {len(items)} tests as skipped due to environment unavailability")


def pytest_sessionfinish(session, exitstatus):
    """Handle session finish - only send success report if tests actually ran"""
    global environment_available
    
    # Don't send any success/failure report if all tests were skipped due to environment
    if getattr(session.config, 'environment_down', False) and not environment_available:
        logger.info("All tests skipped due to environment unavailability - no test report sent")
        return
    
    # NEW: Handle cases where some tests might have run despite environment issues
    environment_skip_info = getattr(session.config, 'environment_skip_info', None)
    if environment_skip_info and environment_skip_info.get('skipped_tests', 0) > 0:
        logger.info(f"Session finished with {environment_skip_info['skipped_tests']} tests skipped due to environment")


def pytest_runtest_setup(item):
    """Handle test setup - skip if environment is down"""
    global environment_available
    
    if not environment_available:
        # NEW: Provide detailed skip reason
        pytest.skip(f"Environment {environment_skip_info['environment']} is not accessible - {environment_skip_info['url']}")


# NEW: API-specific environment check
def check_api_environment():
    """Check API environment availability separately"""
    global environment_available, environment_skip_info
    
    logger.info("Checking API environment availability...")
    api_base_url = EnvironmentConfig.get_api_base_url()
    
    if not EnvironmentConfig.is_api_accessible():
        environment_available = False
        environment_skip_info = {
            'environment': EnvironmentConfig.TEST_ENV,
            'url': api_base_url,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'check_type': 'API'
        }
        
        logger.error(f"API Environment ({api_base_url}) is not accessible")
        return False
    
    environment_available = True
    logger.success("API Environment is accessible")
    return True


@pytest.fixture
def driver():
    """Provides WebDriver instance to tests"""
    # NEW: Check environment before creating driver
    global environment_available
    if not environment_available:
        pytest.skip(f"Environment unavailable - skipping test")
    
    driver_instance = driver_factory.create_driver()
    yield driver_instance
    try:
        driver_instance.quit()
    except Exception:
        logger.exception("Error quitting webdriver")


@pytest.fixture
def browser(driver):
    """Provides browser name for cross-browser tests"""
    from configs.environment import EnvironmentConfig
    return EnvironmentConfig.BROWSER


def _handle_skipped_test(item, report):
    """Handle skipped tests from setup phase"""
    # ENHANCED: Better handling of environment-related skips
    nodeid = getattr(item, "nodeid", item.name if hasattr(item, "name") else str(item))
    
    # Extract skip reason
    skip_reason = None
    if hasattr(report, 'wasxfail'):
        skip_reason = f"Expected failure: {report.wasxfail}"
    else:
        skip_reason = str(report.longrepr) if getattr(report, "longrepr", None) else "Skipped"

    # NEW: Check if this is an environment-related skip
    is_environment_skip = "environment" in skip_reason.lower() or "unavailable" in skip_reason.lower()
    
    logger.info(f"🔍 DEBUG: Processing SKIPPED test in setup: {nodeid}")
    logger.info(f"🔍 DEBUG: Skip reason: {skip_reason}")
    logger.info(f"🔍 DEBUG: Environment-related skip: {is_environment_skip}")

    # Get the appropriate suite reporter
    suite_reporter = None
    test_path = str(item.fspath)
    
    if "smoke_tests" in test_path:
        suite_reporter = get_suite_reporter("smoke")
    elif "regression_tests" in test_path:
        suite_reporter = get_suite_reporter("regression")
    elif "sanity_tests" in test_path:
        suite_reporter = get_suite_reporter("sanity")
    elif "api_tests" in test_path:
        suite_reporter = get_suite_reporter("api")
    else:
        suite_reporter = get_suite_reporter("smoke")
    
    # Add the skipped test to reporting
    if suite_reporter:
        suite_reporter.add_test_result(
            test_name=nodeid,
            status="SKIP",
            error_message=skip_reason,
            screenshot_path=None,
            duration=0.0,
            skip_reason=skip_reason,
        )
        logger.info(f"Added SKIPPED test result to {suite_reporter.test_suite_name}: {nodeid}")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test results for reporting, attach screenshots/html and latest log to pytest-html"""
    outcome = yield
    report = outcome.get_result()

    # Debug all phases to see what's happening
    logger.info(f"🔍 DEBUG: Test phase - {report.when} for {item.nodeid} - Skipped: {report.skipped}")
    
    # Set start time for duration calculation
    if report.when == "setup":
        item.start_time = time.time()
        
        
        if report.skipped:
            _handle_skipped_test(item, report)
        return

    # Only process call phase for test results
    if report.when != "call":
        return

    nodeid = getattr(item, "nodeid", item.name if hasattr(item, "name") else str(item))
    start_time = getattr(item, "start_time", time.time())
    duration = time.time() - start_time

    status = "UNKNOWN"
    error_message = None
    skip_reason = None

    try:
        if report.passed:
            status = "PASS"
        elif report.skipped:
            status = "SKIP"
            # Extract skip reason properly
            if hasattr(report, 'wasxfail'):
                skip_reason = f"Expected failure: {report.wasxfail}"
            else:
                skip_reason = str(report.longrepr) if getattr(report, "longrepr", None) else "Skipped"
            error_message = skip_reason
            logger.info(f"🔍 DEBUG: Processing SKIPPED test in call: {nodeid}")
            logger.info(f"🔍 DEBUG: Skip reason: {skip_reason}")
        else:
            status = "FAIL"
            # prefer concise exception from call.excinfo
            if call.excinfo is not None:
                try:
                    error_message = f"{call.excinfo.type.__name__}: {call.excinfo.value}"
                except Exception:
                    error_message = str(report.longrepr) if getattr(report, "longrepr", None) else "Test failed"
            else:
                error_message = str(report.longrepr) if getattr(report, "longrepr", None) else "Test failed"

        screenshot_path = None
        html_path = None

        # If failed, capture evidence with ScreenshotUtils (use same files for pytest-html and smoke reporter)
        if status == "FAIL":
            driver_instance = item.funcargs.get("driver", None)
            # also look for common alternate driver fixture names
            if not driver_instance:
                for alt in ("webdriver", "browser_driver", "browser"):
                    driver_instance = item.funcargs.get(alt)
                    if driver_instance:
                        break

            if driver_instance:
                try:
                    ss = ScreenshotUtils(driver_instance)
                    result = ss.capture_screenshot_on_failure(
                        test_name=nodeid,
                        error_message=error_message or "Test failed",
                        additional_info={"nodeid": nodeid},
                        browser_info=os.getenv("BROWSER", None),
                    )
                    screenshot_path = result.get("screenshot")
                    html_path = result.get("html")

                    # attach screenshot and html to pytest-html via report.extra
                    extras_list = getattr(report, "extras", [])
                    if screenshot_path and os.path.exists(screenshot_path):
                        extras_list.append(extras.image(screenshot_path))
                    if html_path and os.path.exists(html_path):
                        try:
                            with open(html_path, "r", encoding="utf-8") as f:
                                html_content = f.read()
                            extras_list.append(extras.html(f"<details><summary>Error HTML</summary>{html_content}</details>"))
                        except Exception:
                            logger.exception("Failed reading html_path for attachment")
                    report.extras = extras_list

                    # also store on item so other hooks or reporters can reuse
                    setattr(item, "_screenshot_path", screenshot_path)
                    setattr(item, "_error_html_path", html_path)
                    logger.info(f"Captured failure evidence for {nodeid} -> {screenshot_path}, {html_path}")
                except Exception:
                    logger.exception("Failed capturing screenshot/html via ScreenshotUtils")
            else:
                logger.warning("No webdriver fixture available on test item; skipping screenshot capture")
        
        suite_reporter = None
        test_path = str(item.fspath)
        
        if "smoke_tests" in test_path:
            suite_reporter = get_suite_reporter("smoke")
        elif "regression_tests" in test_path:
            suite_reporter = get_suite_reporter("regression")
        elif "sanity_tests" in test_path:
            suite_reporter = get_suite_reporter("sanity")
        elif "api_tests" in test_path:
            suite_reporter = get_suite_reporter("api")
        else:
            # Fallback to smoke reporter
            suite_reporter = get_suite_reporter("smoke")
            
        # record result in the appropriate reporter with proper metadata
        if suite_reporter:
            logger.info(f"🔍 DEBUG: About to add to {suite_reporter.test_suite_name}: {nodeid} - {status}")
            suite_reporter.add_test_result(
                test_name=nodeid,
                status=status,
                error_message=error_message,
                screenshot_path=screenshot_path,
                duration=duration,
                skip_reason=skip_reason,  # Add skip reason for skipped tests
            )
            logger.info(f"Added test result to {suite_reporter.test_suite_name}: {nodeid} - {status}")
        else:
            logger.warning(f"No reporter found for test: {nodeid}")

        # Attach latest log file to pytest-html (copy into reports/logs and add link + preview)
        try:
            logs_dir = Path("logs")
            reports_dir = Path("reports")
            target_logs_dir = reports_dir / "logs"
            latest_log_path = None

            if logs_dir.exists() and logs_dir.is_dir():
                candidates = sorted(
                    [p for p in logs_dir.iterdir() if p.is_file() and p.suffix.lower() in (".log", ".txt")],
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )
                if candidates:
                    latest_log = candidates[0]
                    target_logs_dir.mkdir(parents=True, exist_ok=True)
                    dest_name = f"{latest_log.stem}__{int(latest_log.stat().st_mtime)}{latest_log.suffix}"
                    copied = target_logs_dir / dest_name
                    try:
                        shutil.copy2(latest_log, copied)
                        latest_log_path = copied
                    except Exception:
                        logger.exception("Failed copying latest log to reports/logs; will reference original")
                        latest_log_path = latest_log

            if latest_log_path and latest_log_path.exists():
                extras_list = getattr(report, "extras", [])
                rel_path = os.path.relpath(latest_log_path, start=reports_dir) if reports_dir.exists() else str(latest_log_path)
                # Add a download link
                link_html = f'<p><a href="{rel_path}" download>Download latest test log ({Path(rel_path).name})</a></p>'
                extras_list.append(extras.html(link_html))

                # Add a tail preview (last ~2000 chars) inside a collapsible <details>
                try:
                    with open(latest_log_path, "r", encoding="utf-8", errors="replace") as f:
                        f.seek(0, os.SEEK_END)
                        size = f.tell()
                        tail_size = 2000
                        if size > tail_size:
                            f.seek(max(0, size - tail_size))
                            preview = f.read()
                        else:
                            f.seek(0)
                            preview = f.read()
                    safe_preview = html_escape.escape(preview)
                    preview_html = (
                        f"<details><summary>Latest log preview ({Path(rel_path).name})</summary>"
                        f"<pre style='white-space:pre-wrap;max-height:400px;overflow:auto'>{safe_preview}</pre></details>"
                    )
                    extras_list.append(extras.html(preview_html))
                except Exception:
                    logger.exception("Failed to read/attach log preview")
                report.extras = extras_list
                setattr(item, "_latest_log_path", str(latest_log_path))
        except Exception:
            logger.exception("Failed to attach latest log to pytest-html")

    except Exception:
        logger.exception("Unhandled exception in pytest_runtest_makereport")
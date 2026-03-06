# conftest.py

import os
import random
import time
import sys
import shutil
from pathlib import Path
import html as html_escape
import logging
import pytest
from datetime import datetime
from pytest_html import extras
from typing import Dict, List, Tuple, Optional, Any
import json

from src.core.driver_factory import driver_factory
from src.utils.reporting import smoke_reporting
from src.utils.reporting import get_suite_reporter
from src.utils.screenshot import ScreenshotUtils
from configs.environment import EnvironmentConfig
from src.utils.notifications import slack_notifier
from src.utils.logger import GeoLogger
import uuid

logger = GeoLogger("conftest")

# Global flags for environment status
environment_available = True
environment_skip_info: Optional[Dict[str, Any]] = None
SKIP_UI_ENV_CHECK = False

# Test type classification
TEST_TYPE_PATTERNS = {
    'ui': ['smoke_tests', 'regression_tests', 'sanity_tests'],
    'api': ['api_tests'],
    'partners_api': ['partners_api_tests']
}


def pytest_addoption(parser):
    """Add command line options for environment control"""
    parser.addoption(
        "--skip-env-check",
        action="store_true",
        default=False,
        help="Skip all environment availability checks"
    )
    parser.addoption(
        "--env-timeout",
        action="store",
        default=30,
        type=int,
        help="Timeout in seconds for environment checks"
    )


def detect_test_types(items: List[pytest.Item]) -> Dict[str, bool]:
    """
    Detect which types of tests are being run based on file paths.
    
    Args:
        items: List of collected test items
    
    Returns:
        Dictionary with boolean flags for each test type
    """
    detected = {
        'ui': False,
        'api': False,
        'partners_api': False
    }
    
    for item in items:
        test_path = str(item.fspath).lower()
        
        # Check for Partners API tests first (more specific)
        if any(pattern in test_path for pattern in TEST_TYPE_PATTERNS['partners_api']):
            detected['partners_api'] = True
        # Check for regular API tests
        elif any(pattern in test_path for pattern in TEST_TYPE_PATTERNS['api']):
            detected['api'] = True
        # Check for UI tests
        elif any(pattern in test_path for pattern in TEST_TYPE_PATTERNS['ui']):
            detected['ui'] = True
    
    return detected


def check_environment_with_retry(
    check_func,
    env_type: str,
    url: str,
    max_attempts: int = 3,
    timeout: int = 10
) -> Tuple[bool, Optional[str]]:
    """
    Generic environment check with retry logic.
    
    Args:
        check_func: Function to check environment
        env_type: Type of environment (UI, API, Partners API)
        url: URL being checked
        max_attempts: Maximum number of check attempts
        timeout: Timeout per attempt
    
    Returns:
        Tuple of (success, error_message)
    """
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"{env_type} check attempt {attempt}/{max_attempts} for {url}")
            
            if check_func():
                logger.success(f"{env_type} environment is accessible")
                return True, None
            
            logger.warning(f"{env_type} check attempt {attempt} failed")
            
        except Exception as e:
            logger.error(f"{env_type} check attempt {attempt} failed: {str(e)}")
        
        if attempt < max_attempts:
            wait_time = 5 * attempt
            logger.info(f"Waiting {wait_time}s before next {env_type} check...")
            time.sleep(wait_time)
    
    error_msg = f"{env_type} environment ({url}) is not accessible after {max_attempts} attempts"
    logger.error(error_msg)
    return False, error_msg


def check_required_environments(
    detected_tests: Dict[str, bool],
    config_timeout: int = 30
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Check only the environments required for the detected test types.
    
    Args:
        detected_tests: Dictionary with detected test types
        config_timeout: Timeout from pytest config
    
    Returns:
        Tuple of (all_available, skip_info)
    """
    global environment_skip_info
    
    all_available = True
    unavailable_environments = []
    max_attempts = 3
    timeout = min(10, config_timeout // max_attempts)  # Distribute timeout
    
    logger.info(f"🔍 Detected test types: {detected_tests}")
    
    # Check UI environment if UI tests are detected
    if detected_tests['ui']:
        url = EnvironmentConfig.get_base_url()
        success, error = check_environment_with_retry(
            lambda: EnvironmentConfig._is_ui_accessible(
                EnvironmentConfig.TEST_ENV,
                max_attempts=1,  # We handle retry in wrapper
                timeout=timeout
            ),
            "UI",
            url,
            max_attempts,
            timeout
        )
        
        if not success:
            all_available = False
            unavailable_environments.append({
                'type': 'UI',
                'url': url,
                'error': error
            })
    
    # Check API environment if API tests are detected
    if detected_tests['api']:
        url = EnvironmentConfig.get_api_base_url()
        success, error = check_environment_with_retry(
            lambda: EnvironmentConfig.is_api_accessible(
                environment=EnvironmentConfig.TEST_ENV,
                max_attempts=1,  # We handle retry in wrapper
                timeout=timeout
            ),
            "API",
            url,
            max_attempts,
            timeout
        )
        
        if not success:
            all_available = False
            unavailable_environments.append({
                'type': 'API',
                'url': url,
                'error': error
            })
    
    # Check Partners API environment if Partners API tests are detected
    if detected_tests['partners_api']:
        url = EnvironmentConfig.get_partners_api_base_url()
        # Partners API might have a different health endpoint
        success, error = check_environment_with_retry(
            lambda: EnvironmentConfig.is_api_accessible(
                endpoint="/auth/health",  # Adjust based on actual endpoint
                environment=EnvironmentConfig.TEST_ENV,
                max_attempts=1,  # We handle retry in wrapper
                timeout=timeout
            ),
            "Partners API",
            url,
            max_attempts,
            timeout
        )
        
        if not success:
            all_available = False
            unavailable_environments.append({
                'type': 'Partners API',
                'url': url,
                'error': error
            })
    
    # Prepare skip info if any environment is unavailable
    skip_info = None
    if not all_available:
        skip_info = {
            'environment': EnvironmentConfig.TEST_ENV,
            'unavailable_environments': unavailable_environments,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'detected_test_types': detected_tests
        }
        
        # Log all unavailable environments
        for env in unavailable_environments:
            logger.error(f"❌ {env['type']} environment is not accessible: {env['url']}")
    
    return all_available, skip_info


def pytest_configure(config):
    """Initialize pytest configuration"""
    global environment_available, environment_skip_info
    
    # Store config for later use
    config.environment_down = False
    config._should_check_env = not config.getoption("--skip-env-check")
    config._env_timeout = config.getoption("--env-timeout")
    
    if config._should_check_env:
        logger.info("Environment checks will be performed after test collection")
    else:
        environment_available = True
        logger.info("⚠️ Environment checks skipped by user request")


def pytest_collection_modifyitems(config, items):
    """
    After collecting tests, detect test types and check required environments.
    This runs after test discovery but before test execution.
    """
    global environment_available, environment_skip_info
    
    # Detect which test types are being run
    detected_tests = detect_test_types(items)
    
    # Store detected types in config for later use
    config.detected_test_types = detected_tests
    
    # Check if we need to validate environments
    if getattr(config, '_should_check_env', False):
        logger.info("🔍 Checking required environments based on detected test types...")
        
        # Check only the environments we need
        all_available, skip_info = check_required_environments(
            detected_tests,
            config._env_timeout
        )
        
        if not all_available:
            # Environment(s) are down - set up skipping mechanism
            config.environment_down = True
            environment_available = False
            environment_skip_info = skip_info
            
            # Create comprehensive skip message
            unavailable_list = [
                f"{env['type']} ({env['url']})" 
                for env in skip_info['unavailable_environments']
            ]
            skip_message = (
                f"❌ Required environment(s) not accessible: {', '.join(unavailable_list)}. "
                f"Tests cannot proceed."
            )
            
            # Mark all tests as skipped
            skip_env = pytest.mark.skip(reason=skip_message)
            for item in items:
                item.add_marker(skip_env)
            
            # Store test count for reporting
            config.skipped_tests_count = len(items)
            config.environment_skip_info = skip_info
            config.environment_skip_info['skipped_tests'] = len(items)
            config.environment_skip_info['test_names'] = [item.nodeid for item in items]
            
            logger.error(skip_message)
            logger.info(f"📝 Marked {len(items)} tests as skipped due to environment unavailability")
        else:
            config.environment_down = False
            environment_available = True
            
            # Log which environments are being used
            active_envs = [k for k, v in detected_tests.items() if v]
            logger.success(f"✅ All required environments are accessible: {', '.join(active_envs)}")
    
    # Set backward compatibility flags
    if detected_tests['api'] or detected_tests['partners_api']:
        os.environ["SKIP_UI_ENV_CHECK"] = "true"


def pytest_sessionfinish(session, exitstatus):
    """Handle session finish - only send reports if tests actually ran"""
    global environment_available
    
    # Don't send reports if all tests were skipped due to environment
    if getattr(session.config, 'environment_down', False) and not environment_available:
        logger.info("📊 All tests skipped due to environment unavailability - no test report sent")
        return
    
    # Handle cases where some tests might have run despite partial environment issues
    env_skip_info = getattr(session.config, 'environment_skip_info', None)
    if env_skip_info and env_skip_info.get('skipped_tests', 0) > 0:
        logger.info(
            f"📊 Session finished with {env_skip_info['skipped_tests']} tests "
            f"skipped due to environment issues"
        )


def pytest_runtest_setup(item):
    """Handle test setup - skip if environment is down"""
    global environment_available
    
    # Set current test in logger handler
    logger.set_current_test(item.nodeid)
    
    if not environment_available:
        # Create comprehensive skip reason
        skip_info = environment_skip_info
        if skip_info and 'unavailable_environments' in skip_info:
            unavailable_list = [
                f"{env['type']} ({env['url']})" 
                for env in skip_info['unavailable_environments']
            ]
            skip_message = (
                f"❌ Required environment(s) not accessible: {', '.join(unavailable_list)}. "
                f"Test cannot run."
            )
        else:
            skip_message = "❌ Environment is not accessible"
        
        pytest.skip(skip_message)


# ========== HELPER FIXTURES ==========

@pytest.fixture
def is_api_test(request) -> bool:
    """Check if current test is an API test"""
    test_path = str(request.node.fspath).lower()
    return any(pattern in test_path for pattern in TEST_TYPE_PATTERNS['api'])


@pytest.fixture
def is_partners_api_test(request) -> bool:
    """Check if current test is a Partners API test"""
    test_path = str(request.node.fspath).lower()
    return any(pattern in test_path for pattern in TEST_TYPE_PATTERNS['partners_api'])


@pytest.fixture
def is_ui_test(request) -> bool:
    """Check if current test is a UI test"""
    test_path = str(request.node.fspath).lower()
    return any(pattern in test_path for pattern in TEST_TYPE_PATTERNS['ui'])


@pytest.fixture
def test_type(request) -> str:
    """Get the type of the current test"""
    if is_partners_api_test(request):
        return "partners_api"
    elif is_api_test(request):
        return "api"
    elif is_ui_test(request):
        return "ui"
    return "unknown"


@pytest.fixture
def environment_urls(request) -> Dict[str, str]:
    """Get URLs for all environments based on current test type"""
    urls = {
        'ui': EnvironmentConfig.get_base_url(),
        'api': EnvironmentConfig.get_api_base_url(),
        'partners_api': EnvironmentConfig.get_partners_api_base_url()
    }
    return urls


# ========== DRIVER FIXTURES ==========

@pytest.fixture
def driver(request):
    """Provides WebDriver instance to UI tests"""
    global environment_available
    
    # Check environment before creating driver
    if not environment_available:
        pytest.skip("Environment unavailable - skipping UI test")
    
    # Skip if this is not a UI test
    test_path = str(request.node.fspath).lower()
    if not any(pattern in test_path for pattern in TEST_TYPE_PATTERNS['ui']):
        pytest.skip("Driver fixture only available for UI tests")
    
    driver_instance = driver_factory.create_driver()
    
    # Set window size
    if EnvironmentConfig.WINDOW_SIZE:
        width, height = EnvironmentConfig.WINDOW_SIZE.split('x')
        driver_instance.set_window_size(int(width), int(height))
    else:
        driver_instance.maximize_window()
    
    yield driver_instance
    
    try:
        driver_instance.quit()
    except Exception:
        logger.exception("Error quitting webdriver")


@pytest.fixture
def browser(driver):
    """Provides browser name for cross-browser tests"""
    return EnvironmentConfig.BROWSER


# ========== REPORTING HOOKS ==========

def _handle_skipped_test(item, report):
    """Handle skipped tests from setup phase"""
    nodeid = getattr(item, "nodeid", item.name if hasattr(item, "name") else str(item))
    
    # Extract skip reason
    if hasattr(report, 'wasxfail'):
        skip_reason = f"Expected failure: {report.wasxfail}"
    else:
        skip_reason = str(report.longrepr) if getattr(report, "longrepr", None) else "Skipped"

    # Check if this is an environment-related skip
    is_environment_skip = "environment" in skip_reason.lower() or "unavailable" in skip_reason.lower()
    
    logger.info(f"🔍 Processing SKIPPED test: {nodeid}")
    logger.info(f"🔍 Skip reason: {skip_reason}")
    logger.info(f"🔍 Environment-related skip: {is_environment_skip}")

    # Get the appropriate suite reporter
    suite_reporter = _get_suite_reporter(str(item.fspath))
    
    if suite_reporter:
        suite_reporter.add_test_result(
            test_name=nodeid,
            status="SKIP",
            error_message=skip_reason,
            screenshot_path=None,
            duration=0.0,
            skip_reason=skip_reason,
        )
        logger.info(f"Added SKIPPED test to {suite_reporter.test_suite_name}: {nodeid}")


def _get_suite_reporter(test_path: str):
    """Get the appropriate suite reporter based on test path"""
    test_path_lower = test_path.lower()
    
    if "partners_api_tests" in test_path_lower:
        return get_suite_reporter("partners_api")
    elif "api_tests" in test_path_lower:
        return get_suite_reporter("api")
    elif "smoke_tests" in test_path_lower:
        return get_suite_reporter("smoke")
    elif "regression_tests" in test_path_lower:
        return get_suite_reporter("regression")
    elif "sanity_tests" in test_path_lower:
        return get_suite_reporter("sanity")
    else:
        return get_suite_reporter("smoke")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test results for reporting"""
    outcome = yield
    report = outcome.get_result()

    # Debug logging
    logger.debug(f"Test phase - {report.when} for {item.nodeid} - Skipped: {report.skipped}")
    
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
            if hasattr(report, 'wasxfail'):
                skip_reason = f"Expected failure: {report.wasxfail}"
            else:
                skip_reason = str(report.longrepr) if getattr(report, "longrepr", None) else "Skipped"
            error_message = skip_reason
        else:
            status = "FAIL"
            if call.excinfo is not None:
                try:
                    error_message = f"{call.excinfo.type.__name__}: {call.excinfo.value}"
                except Exception:
                    error_message = str(report.longrepr) if getattr(report, "longrepr", None) else "Test failed"
            else:
                error_message = str(report.longrepr) if getattr(report, "longrepr", None) else "Test failed"

        screenshot_path = None
        html_path = None
        evidence = {}

        # Handle failed tests
        if status == "FAIL":
            test_path = str(item.fspath)
            is_api_test = "api_tests" in test_path.lower()
            
            # Capture screenshots for UI tests
            if not is_api_test:
                driver_instance = item.funcargs.get("driver", None)
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

                        # Attach to report
                        extras_list = getattr(report, "extras", [])
                        if screenshot_path and os.path.exists(screenshot_path):
                            extras_list.append(extras.image(screenshot_path))
                        if html_path and os.path.exists(html_path):
                            try:
                                with open(html_path, "r", encoding="utf-8") as f:
                                    html_content = f.read()
                                extras_list.append(extras.html(
                                    f"<details><summary>Error HTML</summary>{html_content}</details>"
                                ))
                            except Exception:
                                logger.exception("Failed reading html_path for attachment")
                        report.extras = extras_list
                        
                    except Exception:
                        logger.exception("Failed capturing screenshot/html")
            
            # Capture API response dumps
            if "api" in test_path.lower():
                try:
                    dumps_dir = Path("reports/failed_responses")
                    dumps_dir.mkdir(parents=True, exist_ok=True)
                    
                    safe_name = nodeid.replace("::", "_").replace("/", "_").replace(":", "_")
                    timestamp = datetime.now().strftime("%H%M%S")
                    dump_file = dumps_dir / f"{safe_name}_{timestamp}.json"
                    
                    response_data = {
                        "test_name": nodeid,
                        "timestamp": datetime.now().isoformat(),
                        "error_message": error_message,
                        "response_captured": False
                    }
                    
                    # Try to capture response data
                    if hasattr(item, 'funcargs'):
                        for arg_name, arg_value in item.funcargs.items():
                            if hasattr(arg_value, 'last_response'):
                                response = arg_value.last_response
                                response_data.update({
                                    "status_code": response.status_code,
                                    "body": response.text[:2000],
                                    "response_captured": True
                                })
                                break
                    
                    with open(dump_file, "w", encoding="utf-8") as f:
                        json.dump(response_data, f, indent=2, default=str)
                    
                    evidence["response_file"] = str(dump_file)
                    
                except Exception as e:
                    logger.error(f"Failed to create API failure record: {e}")

        # Send to reporter
        suite_reporter = _get_suite_reporter(str(item.fspath))
        
        if suite_reporter:
            suite_reporter.add_test_result(
                test_name=nodeid,
                status=status,
                error_message=error_message,
                screenshot_path=screenshot_path,
                duration=duration,
                skip_reason=skip_reason,
                evidence=evidence,
            )

    except Exception:
        logger.exception("Unhandled exception in pytest_runtest_makereport")
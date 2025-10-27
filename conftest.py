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
from src.utils.screenshot import ScreenshotUtils
from configs.environment import EnvironmentConfig
from src.utils.notifications import slack_notifier
from src.utils.logger import GeoLogger

logger = GeoLogger("conftest")


def pytest_configure(config):
    """Check environment availability before test session starts"""
    # Check if we should skip environment check
    skip_env_check = config.getoption("--skip-env-check") or False
    
    if not skip_env_check:
        logger.info("Checking environment availability...")
        environment = EnvironmentConfig.TEST_ENV
        base_url = EnvironmentConfig.get_base_url()
        
        if not EnvironmentConfig.is_environment_accessible():
            # Environment is down - set up skipping mechanism
            config.environment_down = True
            config.environment_name = environment
            config.environment_url = base_url
            
            logger.error(f"Environment {environment} ({base_url}) is not accessible after multiple attempts")
            logger.info("Tests will be skipped due to environment unavailability")
            
        else:
            config.environment_down = False
            logger.success("Environment is accessible - proceeding with tests")
    else:
        config.environment_down = False
        logger.info("Environment check skipped")


def pytest_collection_modifyitems(config, items):
    """Skip all tests if environment is down"""
    if getattr(config, 'environment_down', False):
        skip_env = pytest.mark.skip(reason=f"Environment {config.environment_name} is not accessible")
        
        for item in items:
            item.add_marker(skip_env)
        
        # Store test count for reporting
        config.skipped_tests_count = len(items)
        config.environment_skip_info = {
            'environment': config.environment_name,
            'url': config.environment_url,
            'skipped_tests': len(items),
            'test_names': [item.nodeid for item in items]
        }
        
        # Send Slack notification with test count
        message = (
            f"🚫 *Environment Unavailable - Tests Skipped*\n"
            f"*Environment:* {config.environment_name}\n"
            f"*URL:* {config.environment_url}\n"
            f"*Skipped Tests:* {len(items)}\n"
            f"*Status:* All tests skipped due to environment unavailability\n\n"
            f"⚠️ Please check the environment status and try again later."
        )
        
        slack_notifier.send_webhook_message(message)
        logger.info(f"Sent Slack notification about {len(items)} skipped tests")


def pytest_sessionfinish(session, exitstatus):
    """Handle session finish - only send success report if tests actually ran"""
    # Don't send any success/failure report if all tests were skipped due to environment
    if getattr(session.config, 'environment_down', False):
        logger.info("All tests skipped due to environment unavailability - no test report sent")
        return


def pytest_addoption(parser):
    """Add command line option to skip environment check"""
    parser.addoption(
        "--skip-env-check",
        action="store_true",
        default=False,
        help="Skip environment availability check"
    )


@pytest.fixture
def driver():
    """Provides WebDriver instance to tests"""
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


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test results for reporting, attach screenshots/html and latest log to pytest-html"""
    outcome = yield
    report = outcome.get_result()

    # only interested in the call phase
    if report.when != "call":
        return

    nodeid = getattr(item, "nodeid", item.name if hasattr(item, "name") else str(item))
    start_time = getattr(item, "start_time", time.time())
    duration = time.time() - start_time

    status = "UNKNOWN"
    error_message = None

    try:
        if report.passed:
            status = "PASS"
        elif report.skipped:
            status = "SKIPPED"
            error_message = str(report.longrepr) if getattr(report, "longrepr", None) else "Skipped"
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
                    extra = getattr(report, "extra", [])
                    if screenshot_path and os.path.exists(screenshot_path):
                        extra.append(extras.image(screenshot_path))
                    if html_path and os.path.exists(html_path):
                        try:
                            with open(html_path, "r", encoding="utf-8") as f:
                                html_content = f.read()
                            extra.append(extras.html(f"<details><summary>Error HTML</summary>{html_content}</details>"))
                        except Exception:
                            logger.exception("Failed reading html_path for attachment")
                    report.extra = extra

                    # also store on item so other hooks or reporters can reuse
                    setattr(item, "_screenshot_path", screenshot_path)
                    setattr(item, "_error_html_path", html_path)
                    logger.info(f"Captured failure evidence for {nodeid} -> {screenshot_path}, {html_path}")
                except Exception:
                    logger.exception("Failed capturing screenshot/html via ScreenshotUtils")
            else:
                logger.warning("No webdriver fixture available on test item; skipping screenshot capture")

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
                extra = getattr(report, "extra", [])
                rel_path = os.path.relpath(latest_log_path, start=reports_dir) if reports_dir.exists() else str(latest_log_path)
                # Add a download link
                link_html = f'<p><a href="{rel_path}" download>Download latest test log ({Path(rel_path).name})</a></p>'
                extra.append(extras.html(link_html))

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
                    extra.append(extras.html(preview_html))
                except Exception:
                    logger.exception("Failed to read/attach log preview")
                report.extra = extra
                setattr(item, "_latest_log_path", str(latest_log_path))
        except Exception:
            logger.exception("Failed to attach latest log to pytest-html")

        # record result in SmokeReporter (use same paths)
        try:
            smoke_reporting.add_test_result(
                test_name=nodeid,
                status=status,
                error_message=error_message,
                screenshot_path=screenshot_path,
                duration=duration,
            )
        except Exception:
            logger.exception("Failed adding result to smoke_reporting")

    except Exception:
        logger.exception("Unhandled exception in pytest_runtest_makereport")
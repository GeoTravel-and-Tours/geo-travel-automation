#!/usr/bin/env python3
"""
Test suite runner with CLI argument for suite selection and comprehensive reporting
"""
import sys
import os
import argparse
import traceback
import pytest
from dotenv import load_dotenv
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.utils.reporting import smoke_reporting, regression_reporting, sanity_reporting, api_smoke_reporting, unified_reporter, partners_api_smoke_reporting
from src.utils.notifications import slack_notifier
from src.utils.git_utils import setup_git_metadata
from configs.environment import EnvironmentConfig
from src.utils.logger import GeoLogger

# Load environment variables
load_dotenv()


def get_suite_reporter(suite_name):
    """Get the appropriate reporter for the test suite"""
    reporters = {
        "smoke": smoke_reporting,
        "regression": regression_reporting, 
        "sanity": sanity_reporting,
        "api": api_smoke_reporting,
        "partners_api": partners_api_smoke_reporting
    }
    return reporters.get(suite_name, smoke_reporting)

def _setup_environment_metadata():
    """Setup and collect all environment metadata for reporting"""
    # Get git metadata FIRST (highest priority)
    git_info = setup_git_metadata()
    
    if not os.getenv("BRANCH"):
        os.environ["BRANCH"] = git_info["branch"]
    
    if not os.getenv("BUILD_ID"):
        # Generate build ID from timestamp and commit
        commit_suffix = f".{git_info['commit_hash'][:7]}" if git_info['commit_hash'] != 'UNKNOWN' else ""
        build_id = f"#{datetime.now().strftime('%Y.%m.%d.%H%M')}{commit_suffix}"
        os.environ["BUILD_ID"] = build_id
    
    if not os.getenv("BROWSER"):
        os.environ["BROWSER"] = EnvironmentConfig.BROWSER.upper()
    
    # Log the metadata being used
    logger = GeoLogger("MetadataSetup")
    logger.info(f"Branch: {os.getenv('BRANCH')}")
    logger.info(f"Build ID: {os.getenv('BUILD_ID')}")
    logger.info(f"Browser: {os.getenv('BROWSER')}")
    logger.info(f"Environment: {EnvironmentConfig.TEST_ENV.upper()}")
    
def _send_environment_unavailable_notification(environment, url, check_type="UI", reason=None):
    """Send environment unavailable notification to Slack"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    message_lines = [
        "🚫 *Environment Unavailable - Tests Skipped*",
        "------------------------------------------------------",
        f"*Environment:* {environment.upper()}",
        f"*URL:* {url}",
        f"*Time:* {timestamp}",
        f"*Check Type:* {check_type}",
        f"*Status:* All tests will be skipped"
    ]
    
    if reason:
        message_lines.append(f"*Reason:* {reason}")  # Include skip reason in Slack message
    
    message_lines.extend([
        "------------------------------------------------------",
        "⚠️ *Recommended Actions:*",
        "• Check if the environment is running",
        "• Verify network connectivity",
        "• Contact DevOps team if issue persists",
        "• Retry when environment is available"
    ])
    
    message = "\n".join(message_lines)
    slack_notifier.send_webhook_message(message)


def run_tests(suite_name, pytest_args=None, skip_env_check=False, is_unified_run=False):
    """Run selected test suite with comprehensive reporting"""
    logger = GeoLogger("TestRunner")
    
    # Setup metadata before running tests
    _setup_environment_metadata()
    
    # Get the appropriate reporter for this suite
    suite_reporter = get_suite_reporter(suite_name)

    # Map suite names to directories
    test_suites = {
        "smoke": "src/tests/smoke_tests/",
        "regression": "src/tests/regression_tests/",
        "sanity": "src/tests/sanity_tests/", 
        "api": "src/tests/api_tests/",
        "partners_api": "src/tests/partners_api_tests/",
    }

    # Validate suite name
    if suite_name not in test_suites:
        logger.error(f"Invalid suite name: '{suite_name}'")
        print(f"Available options: {', '.join(test_suites.keys())}")
        sys.exit(1)

    test_path = test_suites[suite_name]

    # Create reports directory if not exists
    os.makedirs("reports", exist_ok=True)

    logger.info(f"Running {suite_name.upper()} tests from {test_path}")

    # Send start notification for single suite runs
    if not is_unified_run:
        slack_notifier.send_webhook_message(
            f"🚀 Hey Team, GEO-Bot here! 🤖\n"
            f"✨ *[{suite_reporter.env}] {suite_reporter.test_suite_name}* Suite has Officially *Launched*!\n"
            f"🕒 *Start Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Let's squash some bugs! 🐛🔨"
        )

    # Environment check - ONLY for UI tests, skip for API and Partners API tests
    if not skip_env_check and suite_name not in ["api", "partners_api"]:
        logger.info("Checking UI environment availability...")

        skip_reason = None
        try:
            if not EnvironmentConfig.is_environment_accessible():
                skip_reason = "Homepage URL not reachable"
        except Exception as e:
            skip_reason = f"UI health check failed: {e}"

        if skip_reason:
            logger.error(f"Skipping UI tests: {skip_reason}")
            base_url = EnvironmentConfig.get_base_url()
            _send_environment_unavailable_notification(
                environment=EnvironmentConfig.TEST_ENV,
                url=base_url,
                check_type="UI",
                reason=skip_reason
            )
            if not is_unified_run:
                logger.info("Slack notification sent for skipped UI tests")
            return 0
        else:
            logger.success("UI environment is accessible - proceeding with tests")

    # Partners API-specific environment check
    if not skip_env_check and suite_name == "partners_api":
        logger.info("Checking Partners API environment availability...")

        skip_reason = None
        try:
            # Check if Partners API base URL is configured and accessible
            partners_base_url = EnvironmentConfig.get_partners_api_base_url()
            if not partners_base_url:
                skip_reason = "Partners API base URL not configured"
            else:
                # Test basic connectivity to Partners API gateway
                from src.pages.api.partners_api.partners_auth_api import PartnersAuthAPI
                auth_api = PartnersAuthAPI()
                welcome_response = auth_api.get_welcome()
                
                if welcome_response.status_code != 200:
                    skip_reason = f"Partners API gateway unreachable (Status: {welcome_response.status_code})"
                else:
                    # Verify welcome message structure
                    welcome_data = welcome_response.json()
                    if 'message' not in welcome_data or 'Welcome to GeoTravel API Gateway' not in welcome_data.get('message', ''):
                        skip_reason = "Partners API returned unexpected response structure"
                    
        except ImportError as e:
            skip_reason = f"Partners API dependencies not available: {str(e)}"
        except Exception as e:
            skip_reason = f"Partners API health check failed: {e}"

        if skip_reason:
            logger.error(f"Skipping Partners API tests: {skip_reason}")
            partners_base_url = getattr(EnvironmentConfig, 'get_partners_api_base_url', lambda: "Not configured")()
            _send_environment_unavailable_notification(
                environment=EnvironmentConfig.TEST_ENV,
                url=partners_base_url if partners_base_url else "Not configured",
                check_type="Partners API",
                reason=skip_reason
            )
            if not is_unified_run:
                logger.info("Slack notification sent for skipped Partners API tests")
            return 0
        else:
            logger.success("Partners API environment is accessible - proceeding with tests")

    # API-specific environment check
    if not skip_env_check and suite_name == "api":
        logger.info("Checking API environment availability...")

        skip_reason = None
        try:
            if EnvironmentConfig.should_skip_api_tests():
                skip_reason = "Authentication endpoint not accessible"
        except Exception as e:
            skip_reason = f"API health check failed: {e}"

        if skip_reason:
            logger.warning(f"Skipping API tests: {skip_reason}")
            api_base_url = EnvironmentConfig.get_api_base_url()
            _send_environment_unavailable_notification(
                environment=EnvironmentConfig.TEST_ENV,
                url=api_base_url,
                check_type="API",
                reason=skip_reason
            )
            if not is_unified_run:
                logger.info("Slack notification sent for skipped API tests")
            return 0
        else:
            logger.success("API environment is accessible - proceeding with tests")


    # Start individual suite reporting
    suite_reporter.start_test_suite()

    try:
        # Base pytest arguments
        base_pytest_args = [
            test_path,
            "-v",
            f"--html=reports/{suite_name}_test_report.html",
            "--self-contained-html",
            f"--json-report-file=reports/{suite_name}_test_report.json",
            "--capture=tee-sys",  # capture and show logs
            "--log-cli-level=INFO",  # include logging output
            "--log-cli-format=%(asctime)s [%(levelname)s] %(message)s",
            "--log-cli-date-format=%Y-%m-%d %H:%M:%S",
        ]

        # Add markers for specific suites
        if suite_name in ["smoke", "regression", "sanity"]:
            base_pytest_args.extend(["-m", suite_name])
        
        # API-specific configurations
        if suite_name == "api":
            from conftest import SKIP_UI_ENV_CHECK
            SKIP_UI_ENV_CHECK = True  # Ensure UI checks are skipped in API tests
            base_pytest_args.extend([
                "--log-cli-level=DEBUG",  # More verbose for API debugging
                "-o", "log_cli=true",  # Ensure CLI logging
                "-m", "api"  # Use api marker for API tests
            ])
        # Partners API-specific configurations
        if suite_name == "partners_api":
            base_pytest_args.extend([
                "-m", "partners_api",  # Use partners_api marker
                "--log-cli-level=DEBUG",  # More verbose for debugging
            ])

        # Add any additional pytest arguments
        if pytest_args:
            base_pytest_args.extend(pytest_args)

        exit_code = pytest.main(base_pytest_args)
        
        # Get the individual suite report
        suite_report = suite_reporter.end_test_suite()
        
        if suite_report:
            # Add to unified reporter if this is part of a unified run
            if is_unified_run:
                unified_reporter.add_suite_result(suite_name, suite_report)
            else:
                # Send individual report for single suite runs
                suite_reporter.send_individual_slack_report(suite_report)
            
            if suite_report["failed_tests"] == 0:
                logger.success(f"All {suite_report['total_tests']} {suite_name} tests passed!")
            else:
                logger.error(f"{suite_report['failed_tests']} of {suite_report['total_tests']} {suite_name} tests failed")
        else:
            # Tests were all skipped due to environment
            logger.info("All tests were skipped due to environment unavailability")
            suite_reporter.test_results = []
            suite_reporter.suite_start_time = None
            
        return exit_code
    
    except Exception as e:
        error_message = "".join(traceback.format_exception_only(type(e), e)).strip()
        suite_reporter.add_test_result(
            test_name=f"{suite_name} suite execution",
            status="FAIL",
            error_message=f"Suite execution failed: {error_message}",
        )
        suite_report = suite_reporter.end_test_suite()
        if is_unified_run and suite_report:
            unified_reporter.add_suite_result(suite_name, suite_report)
        else:
            if suite_report:
                suite_reporter.send_individual_slack_report(suite_report)
        logger.error(f"Test suite execution failed: {error_message}")
        raise


def run_multiple_suites(suite_names, skip_env_check=False):
    """Run multiple test suites sequentially with unified reporting"""
    logger = GeoLogger("TestRunner")
    overall_exit_code = 0
    
    # Setup metadata before running tests
    _setup_environment_metadata()
    
    # Start unified reporting
    unified_reporter.start_unified_test_run(suite_names)
    
    for suite_name in suite_names:
        logger.info(f"🚀 Starting {suite_name.upper()} test suite...")
        exit_code = run_tests(suite_name, skip_env_check=skip_env_check, is_unified_run=True)
        
        # If any suite fails, overall result should be failure
        if exit_code != 0:
            overall_exit_code = exit_code
            
        logger.info(f"✅ Completed {suite_name.upper()} test suite")
    
    # Send unified report
    unified_reporter.send_unified_slack_report()
    
    return overall_exit_code


def run_api_tests_with_config():
    """Specialized function for running API tests with proper configuration"""
    logger = GeoLogger("APITestRunner")
    
    # Set environment variables for API testing
    os.environ["TEST_TYPE"] = "API"
    
    # Use environment-specific API URL
    api_base_url = EnvironmentConfig.get_api_base_url()
    logger.info(f"Running API tests against: {api_base_url}")
    
    # Run comprehensive API health check
    health_status = EnvironmentConfig.check_api_health_comprehensive()
    
    # Run all API tests
    return run_tests("api")


if __name__ == "__main__":
    git_info = setup_git_metadata()
    default_branch = git_info["branch"]
    default_build_id = f"#{datetime.now().strftime('%Y.%m.%d.%H%M')}.{git_info['commit_hash'][:7]}" if git_info['commit_hash'] != 'UNKNOWN' else f"#{datetime.now().strftime('%Y.%m.%d.%H%M')}"
    
    parser = argparse.ArgumentParser(
        description="Run test suites dynamically (smoke, regression, sanity, api, partners_api)"
    )
    parser.add_argument(
        "--suite",
        nargs="+",
        required=True,
        choices=["smoke", "regression", "sanity", "api", "partners_api"],
        help="Specify test suite(s) to run (one or more of: smoke, regression, sanity, api, partners_api)"
    )
    parser.add_argument(
        "--skip-env-check",
        action="store_true",
        help="Skip environment availability check (use with caution)"
    )
    parser.add_argument(
        "--api-only",
        action="store_true",
        help="Run only API tests with specialized configuration"
    )
    parser.add_argument(
        "--pytest-args",
        nargs="*",
        help="Additional arguments to pass to pytest (e.g., -k 'test_login')"
    )
    
    # NEW: Add metadata collection arguments
    parser.add_argument(
        "--branch",
        default=os.getenv("BRANCH", "MAIN"),
        help="Specify branch name for reporting"
    )
    parser.add_argument(
        "--build-id", 
        default=os.getenv("BUILD_ID", f"#{datetime.now().strftime('%Y.%m.%d.%H%M')}"),
        help="Specify build ID for reporting"
    )
    parser.add_argument(
        "--browser",
        default=os.getenv("BROWSER", "CHROME"),
        help="Specify browser for reporting"
    )
    
    args = parser.parse_args()

    # NEW: Set metadata from command line arguments
    os.environ["BRANCH"] = args.branch
    os.environ["BUILD_ID"] = args.build_id
    os.environ["BROWSER"] = args.browser.upper()

    if args.api_only:
        run_api_tests_with_config()
    elif len(args.suite) == 1:
        # Single suite - use individual reporting
        run_tests(args.suite[0], args.pytest_args, args.skip_env_check, is_unified_run=False)
    else:
        # Multiple suites - use unified reporting
        run_multiple_suites(args.suite, args.skip_env_check)
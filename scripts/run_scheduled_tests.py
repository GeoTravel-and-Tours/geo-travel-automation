# scripts/run_scheduled_tests.py

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

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Import your custom reporter
from src.utils.reporting import smoke_reporting
from configs.environment import EnvironmentConfig
from src.utils.logger import GeoLogger

# Load environment variables
load_dotenv()


def run_tests(suite_name, pytest_args=None, skip_env_check=False):
    """Run selected test suite with comprehensive reporting"""
    logger = GeoLogger("TestRunner")

    # Map suite names to directories
    test_suites = {
        "smoke": "src/tests/smoke_tests/",
        "regression": "src/tests/regression_tests/",
        "sanity": "src/tests/sanity_tests/",
        "api": "src/tests/api_tests/",
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

    # Environment check - ONLY for UI tests, skip for API tests
    if not skip_env_check and suite_name != "api":
        logger.info("Checking UI environment availability...")
        if not EnvironmentConfig.is_environment_accessible():
            logger.error("UI environment is not accessible. Skipping UI tests.")
            smoke_reporting.start_test_suite()
            smoke_reporting.add_test_result(
                test_name="Environment Check",
                status="SKIP",
                error_message="UI environment is not accessible"
            )
            smoke_reporting.end_test_suite()
            return 0
        else:
            logger.success("UI environment is accessible - proceeding with tests")

    # API-specific environment check
    if not skip_env_check and suite_name == "api":
        logger.info("Checking API environment availability...")
        if EnvironmentConfig.should_skip_api_tests():
            logger.warning("API environment is not accessible. Skipping API tests.")
            smoke_reporting.start_test_suite()
            smoke_reporting.add_test_result(
                test_name="API Environment Check",
                status="SKIP", 
                error_message="API environment is not accessible"
            )
            smoke_reporting.end_test_suite()
            return 0
        else:
            logger.success("API environment is accessible - proceeding with tests")
            # SKIP UI CHECK FOR API TESTS - DON'T CHECK UI ENVIRONMENT
            pass

    # Start reporting
    smoke_reporting.start_test_suite()

    try:
        # Base pytest arguments
        pytest_args = [
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
            pytest_args.extend(["-m", suite_name])
        
        # API-specific configurations
        if suite_name == "api":
            pytest_args.extend([
                "--log-cli-level=DEBUG",  # More verbose for API debugging
                "-o", "log_cli=true",  # Ensure CLI logging
                "-m", "api"  # Use api marker for API tests
            ])

        exit_code = pytest.main(pytest_args)
        
        if smoke_reporting.test_results:
            report = smoke_reporting.end_test_suite()
            
            if report["failed_tests"] == 0:
                logger.success(f"All {report['total_tests']} {suite_name} tests passed!")
            else:
                logger.error(f"{report['failed_tests']} of {report['total_tests']} {suite_name} tests failed")
        else:
            # Tests were all skipped due to environment - don't send success report
            logger.info("All tests were skipped due to environment unavailability")
            # Clear the test suite without sending success report
            smoke_reporting.test_results = []
            smoke_reporting.suite_start_time = None
            
        return exit_code
    
    except Exception as e:
        error_message = "".join(traceback.format_exception_only(type(e), e)).strip()
        smoke_reporting.add_test_result(
            test_name=f"{suite_name} suite execution",
            status="FAIL",
            error_message=f"Suite execution failed: {error_message}",
        )
        smoke_reporting.end_test_suite()
        logger.error(f"Test suite execution failed: {error_message}")
        raise


def run_api_tests_with_config():
    """Specialized function for running API tests with proper configuration"""
    logger = GeoLogger("APITestRunner")
    
    # Set environment variables for API testing
    os.environ["TEST_TYPE"] = "API"
    
    # Use environment-specific API URL with proper debugging
    api_base_url = EnvironmentConfig.get_api_base_url()
    current_env = EnvironmentConfig.TEST_ENV
    
    logger.info(f"Running API tests - Environment: {current_env}")
    logger.info(f"API Base URL: {api_base_url}")
    
    # Run comprehensive API health check
    health_status = EnvironmentConfig.check_api_health_comprehensive()
    
    # Run all API tests
    return run_tests("api")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run test suites dynamically (smoke, regression, sanity, api)"
    )
    parser.add_argument(
        "--suite",
        required=True,
        choices=["smoke", "regression", "sanity", "api"],
        help="Specify test suite to run"
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
    args = parser.parse_args()

    if args.api_only:
        # Force API suite regardless of --suite argument
        run_api_tests_with_config()
    else:
        run_tests(args.suite, args.skip_env_check)
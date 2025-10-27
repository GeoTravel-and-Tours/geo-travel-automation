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


def run_tests(suite_name, skip_env_check=False):
    """Run selected test suite with comprehensive reporting"""
    logger = GeoLogger("TestRunner")

    # Map suite names to directories
    test_suites = {
        "smoke": "src/tests/smoke_tests/",
        "regression": "src/tests/regression_tests/",
        "sanity": "src/tests/sanity_tests/",
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

    # Start reporting
    smoke_reporting.start_test_suite()

    try:
        # Pytest arguments
        pytest_args = [
            test_path,
            "-v",
            "--html=reports/{}_test_report.html".format(suite_name),
            "--self-contained-html",
            "--json-report",
            "--json-report-file=reports/{}_test_report.json".format(suite_name),
            "-m",
            suite_name,  # pytest marker
            "--capture=tee-sys",  # capture and show logs
            "--log-cli-level=INFO",  # include logging output
            "--log-cli-format=%(asctime)s [%(levelname)s] %(message)s",
            "--log-cli-date-format=%Y-%m-%d %H:%M:%S",
        ]

        # Add skip env check flag if requested
        if skip_env_check:
            pytest_args.append("--skip-env-check")

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run test suites dynamically (smoke, regression, sanity)"
    )
    parser.add_argument(
        "--suite",
        required=True,
        help="Specify test suite to run (smoke, regression, sanity)",
    )
    parser.add_argument(
        "--skip-env-check",
        action="store_true",
        help="Skip environment availability check (use with caution)"
    )
    args = parser.parse_args()

    run_tests(args.suite, args.skip_env_check)
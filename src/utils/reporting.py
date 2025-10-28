# src/utils/reporting.py

import os
import json
from datetime import datetime
from pathlib import Path
from .notifications import slack_notifier, email_notifier
from src.utils.html_templates import get_html_report_template, get_error_report_template
from .logger import GeoLogger
from src.utils.cleanup import get_cleanup_manager


# ====== REPORT UTILITIES ======
class ReportUtils:
    """Utility for generating test reports"""

    def __init__(self, report_dir="reports"):
        self.report_dir = Path(report_dir)
        self.logger = GeoLogger(name="ReportUtils")
        self._setup_directories()
    

    def _setup_directories(self):
        """Create report directory structure"""
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def generate_json_report(self, test_results, filename=None):
        """Generate JSON test report"""
        if not filename:
            filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        report_path = self.report_dir / filename

        with open(report_path, "w") as f:
            json.dump(test_results, f, indent=2)

        self.logger.info(f"JSON report generated: {report_path}")
        return report_path

    def generate_html_report(self, test_results, filename=None):
        """Generate enhanced HTML report using template"""
        html_content = get_html_report_template(test_results, filename)
        
        # Save the HTML content to file
        if not filename:
            filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        report_path = self.report_dir / filename
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        self.logger.info(f"Enhanced HTML report generated: {report_path}")
        return report_path
    
    def _generate_comprehensive_report(self, test_results, test_suite_name, suite_start_time, suite_end_time, duration):
        """Generate comprehensive test report with proper counting"""
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in test_results if r["status"] == "FAIL"])
        skipped_tests = len([r for r in test_results if r["status"] == "SKIP"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        failed_tests_details = [r for r in test_results if r["status"] == "FAIL"]
        skipped_tests_details = [r for r in test_results if r["status"] == "SKIP"]

        report = {
            "test_suite_name": test_suite_name,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "success_rate": success_rate,
            "duration": duration,
            "start_time": suite_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": suite_end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "failed_tests_details": failed_tests_details,
            "skipped_tests_details": skipped_tests_details,
        }

        return report

    
    def _generate_error_html(self, test_name, error_message, driver=None, additional_info=None):
        """Generate enhanced HTML error report using template"""
        current_url = driver.current_url if driver else "N/A"
        page_source = (
            driver.page_source[:5000] + ('...' if len(driver.page_source) > 5000 else '')
            if driver
            else "<!-- No page source available -->"
        )

        html_content = get_error_report_template(
            test_name=test_name,
            error_message=error_message,
            current_url=current_url,
            page_source=page_source,
            additional_info=additional_info
        )

        return html_content


# ====== GEO REPORTER ======
class GeoReporter:
    def __init__(self, test_suite_name="Smoke Tests"):
        self.test_suite_name = test_suite_name
        self.test_results = []
        self.suite_start_time = None
        self.suite_end_time = None
        self.logger = GeoLogger(name="GeoReporter")
        
        self.reporting = ReportUtils()
        self.suite_results = {}
        self.overall_start_time = None

        try:
            from configs.environment import EnvironmentConfig
        except:
            self.env = "UNKNOWN"
        else:
            self.env = EnvironmentConfig.TEST_ENV.upper()
            
    def start_test_suite(self):
        """Start tracking test suite"""
        self.suite_start_time = datetime.now()
        self.test_results = []
        self.logger.info(f"Starting test suite: {self.test_suite_name}")

    def start_unified_test_run(self, suite_names):
        """Start unified test run for multiple suites"""
        self.overall_start_time = datetime.now()
        self.suite_results = {}
        self.test_suite_name = f"Combined {', '.join(suite_names).upper()} Tests"

        self.logger.info(f"Starting unified test run for: {', '.join(suite_names)}")

        # Send start notification
        slack_notifier.send_webhook_message(
            f"🚀 Hey Team, GEO-Bot here! 🤖\n"
            f"✨ *[{self.env}] {self.test_suite_name}* suite has officially *launched*!\n"
            f"🕒 *Start Time:* {self.overall_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Let's squash some bugs! 🐛🔨"
        )

    def add_test_result(
        self, test_name, status, error_message=None, screenshot_path=None, duration=None, skip_reason=None
    ):
        """Add individual test result with comprehensive metadata"""
        test_result = {
            "test_name": test_name,
            "status": status,
            "error_message": error_message,
            "screenshot_path": screenshot_path,
            "duration": duration or 0.0,  # Ensure duration is never None
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "skip_reason": skip_reason,  # Store skip reason for reporting
        }
        self.test_results.append(test_result)
        self.logger.info(f"Test result added: {test_name} - {status} (Duration: {duration:.2f}s)")

    def add_suite_result(self, suite_name, report_data):
        """Add results from a specific test suite for unified reporting"""
        if report_data:
            self.suite_results[suite_name] = {
                "report": report_data,
                "timestamp": datetime.now()
            }
            self.logger.info(f"Added {suite_name} suite results to unified report")

    def end_test_suite(self):
        """End test suite and return report data"""
        self.suite_end_time = datetime.now()
        
        # If no test results were manually added, create a basic report
        if not self.test_results:
            self.logger.warning("No test results were manually recorded. Creating basic report...")
            # Create a basic report indicating tests ran but weren't tracked
            report = {
                "test_suite_name": self.test_suite_name,
                "total_tests": 0,  # Will be updated by pytest results
                "passed_tests": 0,
                "failed_tests": 0,
                "skipped_tests": 0,
                "success_rate": 0,
                "duration": (self.suite_end_time - self.suite_start_time).total_seconds(),
                "start_time": self.suite_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": self.suite_end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "failed_tests_details": [],
            }
            return report
        
        duration = (self.suite_end_time - self.suite_start_time).total_seconds()

        # Generate report data from manually collected results
        report = self.reporting._generate_comprehensive_report(
            self.test_results, 
            self.test_suite_name, 
            self.suite_start_time, 
            self.suite_end_time, 
            duration
        )
        
        self.logger.info(f"Test suite completed: {report['total_tests']} tests, {report['passed_tests']} passed")
        return report

    def generate_unified_report(self):
        """Generate a unified report combining all suite results"""
        if not self.suite_results:
            return None

        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        all_failed_tests = []
        all_skipped_tests = []

        # Calculate totals across all suites
        for suite_name, suite_data in self.suite_results.items():
            report = suite_data["report"]
            total_tests += report.get("total_tests", 0)
            total_passed += report.get("passed_tests", 0)
            total_failed += report.get("failed_tests", 0)
            total_skipped += report.get("skipped_tests", 0)

            # Collect failed tests with suite context
            failed_tests = report.get("failed_tests_details", [])
            for failed_test in failed_tests:
                failed_test["suite"] = suite_name
                all_failed_tests.append(failed_test)

            # Collect Skipped tests too
            skipped_tests = report.get("skipped_tests_details", [])
            for skipped_test in skipped_tests:
                skipped_test["suite"] = suite_name
                all_skipped_tests.append(skipped_test)

        # Calculate overall success rate
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        unified_report = {
            "test_suite_name": self.test_suite_name,
            "total_tests": total_tests,
            "passed_tests": total_passed,
            "failed_tests": total_failed,
            "skipped_tests": total_skipped,
            "success_rate": round(success_rate, 1),
            "duration": (datetime.now() - self.overall_start_time).total_seconds() if self.overall_start_time else 0,
            "start_time": self.overall_start_time.strftime("%Y-%m-%d %H:%M:%S") if self.overall_start_time else None,
            "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "suites_run": list(self.suite_results.keys()),
            "suite_details": self.suite_results,
            "all_failed_tests": all_failed_tests,
            "all_skipped_tests": all_skipped_tests
        }

        return unified_report

    def send_unified_slack_report(self):
        """Send unified report to Slack"""
        unified_report = self.generate_unified_report()
        if not unified_report:
            self.logger.warning("No test results to report")
            return

        summary = {
            "total_tests": unified_report["total_tests"],
            "passed_tests": unified_report["passed_tests"],
            "failed_tests": unified_report["failed_tests"], 
            "skipped_tests": unified_report["skipped_tests"],
            "success_rate": unified_report["success_rate"],
            "duration": unified_report["duration"],
            "start_time": unified_report["start_time"],
            "end_time": unified_report["end_time"],
            "suites_run": unified_report["suites_run"]
        }

        all_failed_tests = unified_report["all_failed_tests"]

        # Collect all skipped tests from all suites
        all_skipped_tests = []
        for suite_name, suite_data in self.suite_results.items():
            report = suite_data["report"]
            skipped_tests = report.get("skipped_tests_details", [])
            for skipped_test in skipped_tests:
                skipped_test["suite"] = suite_name
                all_skipped_tests.append(skipped_test)

        # Determine overall status
        if summary["failed_tests"] == 0:
            status_emoji = "✅✅✅"
            status_message = "🎉 Great news team! All tests passed. GEO-Bot is proud 🤖✨"
        else:
            status_emoji = "❌❌❌" 
            status_message = "⚠️ Uh-oh, GEO-Bot spotted some issues! Please check the details below 🐞🔧"

        # Build the main message
        message = (
            f"*{status_emoji}* *[{self.env}]* *{unified_report['test_suite_name']}* - Test Report *{status_emoji}*\n\n"
            f"{status_message}\n\n"
            f"*📊 Summary*\n"
            f"• Total Tests: {summary['total_tests']}\n"
            f"• Passed: {summary['passed_tests']} ✅\n"
            f"• Failed: {summary['failed_tests']} ❌\n"
            f"• Skipped: {summary['skipped_tests']} ⚠️\n"
            f"• Success Rate: {summary['success_rate']:.1f}%\n"
            f"• Duration: {summary['duration']:.2f}s\n\n"
            f"*🕐 Execution Time*\n"
            f"• Start: {summary['start_time']}\n"
            f"• End: {summary['end_time']}\n"
        )

        # Add suite breakdown
        message += f"\n*📋 Suite Breakdown:*\n"
        for suite_name, suite_data in self.suite_results.items():
            report = suite_data["report"]
            suite_emoji = "✅" if report.get("failed_tests", 0) == 0 else "❌"
            message += f"• {suite_emoji} {suite_name.upper()}: {report.get('passed_tests', 0)}/{report.get('total_tests', 0)} passed\n"

        # Add failed tests section if any
        if all_failed_tests:
            message += f"\n*❌ Failed Tests ({len(all_failed_tests)}):*\n"
            for i, test in enumerate(all_failed_tests[:8], 1):  # Limit to first 8
                suite = test.get('suite', 'Unknown').upper()
                test_name = test.get('test_name', 'Unknown Test')
                error = self._clean_error_message(test.get('error_message', 'Unknown error'))
                message += f"\n{i}. *[{suite}]* {test_name}\n   Error: {error}\n"

            if len(all_failed_tests) > 8:
                message += f"\n... and {len(all_failed_tests) - 8} more failures"

        # Add Skipped Tests section
        if all_skipped_tests:
            message += f"\n*⚠️ Skipped Tests ({len(all_skipped_tests)}):*\n"
            for i, test in enumerate(all_skipped_tests[:5], 1):  # Limit to first 5
                suite = test.get('suite', 'Unknown').upper()
                test_name = test.get('test_name', 'Unknown Test')
                skip_reason = self._clean_error_message(test.get('skip_reason', 'Skipped'))
                message += f"\n{i}. *[{suite}]* {test_name}\n   Reason: {skip_reason}\n"

            if len(all_skipped_tests) > 5:
                message += f"\n... and {len(all_skipped_tests) - 5} more skipped tests"

        slack_notifier.send_webhook_message(message)
        self._save_unified_report(unified_report)

    def send_individual_slack_report(self, report):
        """Send individual suite report to Slack"""
        if not report:
            return

        all_passed = report["failed_tests"] == 0

        if all_passed:
            status_emoji = "✅✅✅"
            intro_message = (
                f"*{status_emoji}* *[{self.env}]* *{report['test_suite_name']}* - Test Report {status_emoji}\n\n"
                f"🎉 Great news team! All tests passed. GEO-Bot is proud 🤖✨\n"
            )
        else:
            status_emoji = "❌❌❌"
            intro_message = (
                f"*{status_emoji}* *[{self.env}]* *{report['test_suite_name']}* - Test Report {status_emoji}\n\n"
                f"⚠️ Uh-oh, GEO-Bot spotted some issues! Please check the details below 🐞🔧\n"
            )

        message = (
            intro_message
            + f"""

    *📊 Summary*
    • Total Tests: {report['total_tests']}
    • Passed: {report['passed_tests']} ✅  
    • Failed: {report['failed_tests']} ❌
    • Skipped: {report['skipped_tests']} ⚠️
    • Success Rate: {report['success_rate']:.1f}%
    • Duration: {report['duration']:.2f}s

    *🕐 Execution Time*
    • Start: {report['start_time']}
    • End: {report['end_time']}
    """
        )

        # ENHANCED FAILURE DETAILS
        if report["failed_tests"] > 0:
            message += f"\n*❌ Failed Tests ({report['failed_tests']}):*\n"

            for i, failed_test in enumerate(report["failed_tests_details"], 1):
                message += f"\n*{i}. {failed_test['test_name']}*\n"

                # Error message
                if failed_test["error_message"]:
                    error_msg = self._clean_error_message(failed_test["error_message"])
                    message += f"   *Error:* {error_msg}\n"

                # Test duration - use actual duration from test result
                actual_duration = failed_test.get("duration")
                if actual_duration is not None:
                    message += f"   *Duration:* {actual_duration:.2f}s\n"
                else:
                    message += f"   *Duration:* 0.00s\n"

                # Screenshot info
                if failed_test.get("screenshot_path"):
                    message += f"   *Screenshot:* `{failed_test['screenshot_path']}`\n"

                # Additional context based on test type
                context = self._get_test_context(failed_test["test_name"])
                if context:
                    message += f"   *Context:* {context}\n"

        # Add Skipped Tests section
        if report["skipped_tests"] > 0:
            message += f"\n*⚠️ Skipped Tests ({report['skipped_tests']}):*\n"

            for i, skipped_test in enumerate(report.get("skipped_tests_details", []), 1):
                message += f"\n*{i}. {skipped_test['test_name']}*\n"

                # Skip reason
                skip_reason = skipped_test.get("skip_reason", "Skipped")
                clean_reason = self._clean_error_message(skip_reason)
                message += f"   *Reason:* {clean_reason}\n"

                # Test duration
                actual_duration = skipped_test.get("duration")
                if actual_duration is not None:
                    message += f"   *Duration:* {actual_duration:.2f}s\n"
                else:
                    message += f"   *Duration:* 0.00s\n"

                # Context
                context = self._get_test_context(skipped_test["test_name"])
                if context:
                    message += f"   *Context:* {context}\n"

        slack_notifier.send_webhook_message(message)
        self._save_report_to_file(report)

    def _clean_error_message(self, error_message):
        """Clean and format error message for Slack"""
        lines = error_message.split("\n")
        clean_lines = []

        for line in lines:
            line = line.strip()
            if (
                line.startswith('File "')
                or line.startswith("self = <")
                or "object at 0x" in line
                or line.startswith("E   ")
                or not line
            ):
                continue

            if (
                "AssertionError" in line
                or "Failed:" in line
                or "Error:" in line
                or "Exception:" in line
            ):
                clean_lines.append(line)

        if clean_lines:
            return " | ".join(clean_lines[:3])
        return error_message[:150] + ("..." if len(error_message) > 150 else "")

    def _get_test_context(self, test_name):
        """Provide context about what the test was doing"""
        method_name = test_name.split("::")[-1] if "::" in test_name else test_name
        context_map = {
            #============================ UI Tests ============================#
            # Homepage Tests
            "test_homepage_loads_successfully": "Homepage loading and basic validation",
            "test_basic_homepage_elements_exist": "Checking page structure and elements",
            "test_homepage_navigation_works": "Testing page navigation links",
            "test_homepage_health_check": "Overall page health and validation",
            # Login Tests
            "test_login_page_accessibility": "Login page structure check",
            "test_successful_login_and_redirect": "User authentication flow",
            "test_failed_login_with_error_message": "Invalid login handling",
            "test_logout_functionality": "User session termination",
            # Flight Booking Tests
            "test_flight_search_form_visible": "Flight search form visibility",
            "test_basic_flight_search": "Performing a basic flight search",
            "test_search_results_display": "Verifying flight search results",
            "test_flight_selection_works": "Selecting a flight from results",
            "test_passenger_form_loads": "Passenger details form loading",
            "test_payment_page_accessible": "Accessing payment options",
            "test_flights_navigation_works": "Testing browser navigation during flight booking",
            "test_error_handling": "Error scenarios during flight booking",
            # Package Booking Tests
            "test_complete_package_booking_flow": "End-to-end package booking process",
            "test_package_search_functionality": "Searching for travel packages",
            "test_booking_form_validation": "Validating package booking form",
            
            
            #============================ API Tests ============================#
            # Auth API Tests
            "test_login_success": "User login API endpoint",
            "test_login_invalid_credentials": "Handling invalid login attempts via API", 
            "test_login_empty_credentials": "Empty credentials validation via API",
            "test_login_missing_password": "Missing password validation via API",
            "test_auth_token_set_after_successful_login": "Authentication token validation",

            # Flight API Tests  
            "test_flight_search_request": "Creating flight search requests via API",
            "test_get_booked_flights": "Fetching user's booked flights via API",
        }

        return context_map.get(method_name, "Functional test")

    def _cleanup_old_reports(self):
        """Clean up old report files"""
        try:
            manager = get_cleanup_manager()
            deleted_count = manager.cleanup_old_files(
                directory="reports",
                patterns=["*.json", "*.html"],
                recursive=False,
                dry_run=False
            )
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old report files")
        except Exception as e:
            self.logger.error(f"Report cleanup error: {e}")

    def _save_report_to_file(self, report):
        """Save individual test report to a file"""
        os.makedirs("reports", exist_ok=True)
        filename = f"reports/{self.test_suite_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(report, f, indent=4)
        self._cleanup_old_reports()

    def _save_unified_report(self, unified_report):
        """Save unified report to file"""
        os.makedirs("reports", exist_ok=True)
        filename = f"reports/unified_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(unified_report, f, indent=4)
        self._cleanup_old_reports()


# ====== GLOBAL INSTANCES ======
# Individual suite reporters
smoke_reporting = GeoReporter("Smoke Tests")
regression_reporting = GeoReporter("Regression Tests") 
sanity_reporting = GeoReporter("Sanity Tests")
api_reporting = GeoReporter("API Tests")

# Unified reporter instance (reuses one of the instances)
unified_reporter = smoke_reporting

def get_suite_reporter(suite_name):
    """Get the appropriate reporter for the test suite"""
    reporters = {
        "smoke": smoke_reporting,
        "regression": regression_reporting, 
        "sanity": sanity_reporting,
        "api": api_reporting
    }
    return reporters.get(suite_name, smoke_reporting)
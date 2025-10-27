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
        """Generate comprehensive test report"""
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in test_results if r["status"] == "FAIL"])
        skipped_tests = len([r for r in test_results if r["status"] == "SKIPPED"])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        failed_tests_details = [r for r in test_results if r["status"] == "FAIL"]

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

        # Notify suite start
        slack_notifier.send_webhook_message(
            f"🚀 Hey Team, GEO-Bot here! 🤖\n"
            f"✨ *[{self.env}] {self.test_suite_name}* suite has officially *launched*!\n"
            f"🕒 *Start Time:* {self.suite_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Let's squash some bugs! 🐛🔨"
        )

    def add_test_result(
        self, test_name, status, error_message=None, screenshot_path=None, duration=None
    ):
        """Add individual test result"""
        test_result = {
            "test_name": test_name,
            "status": status,
            "error_message": error_message,
            "screenshot_path": screenshot_path,
            "duration": duration,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
        self.test_results.append(test_result)

    def end_test_suite(self):
        """End test suite and send report ONLY if tests actually ran"""
        
        # Don't send report if no tests were executed (all skipped due to environment)
        if not self.test_results:
            self.logger.warning("No test results to report.")
            return None
        
        self.suite_end_time = datetime.now()
        duration = (self.suite_end_time - self.suite_start_time).total_seconds()

        # Generate and send report
        report = self.reporting._generate_comprehensive_report(
            self.test_results, 
            self.test_suite_name, 
            self.suite_start_time, 
            self.suite_end_time, 
            duration
        )
        self._send_slack_report(report)
        self._save_report_to_file(report)

        return report
    
    def _cleanup_old_reports(self):
        """Clean up old report files"""
        try:
            manager = get_cleanup_manager()

            # FIX: Use the correct method name
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

    # Then call it in your _save_report_to_file method:
    def _save_report_to_file(self, report):
        """Save test report to a file"""
        os.makedirs("reports", exist_ok=True)
        filename = f"reports/{self.test_suite_name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(report, f, indent=4)

        # Clean up old reports after saving new one
        self._cleanup_old_reports()

    def _send_slack_report(self, report):
        """Send comprehensive report to Slack with detailed failure info"""

        all_passed = report["failed_tests"] == 0

        if all_passed:
            # 🎉 Success style
            status_emoji = "✅✅✅"
            intro_message = (
                f"*{status_emoji}* *[{self.env}]* *{report['test_suite_name']}* - Test Report {status_emoji}\n\n"
                f"🎉 Great news team! All tests passed. GEO-Bot is proud 🤖✨\n"
            )
        else:
            # Failure style
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
                    # Clean and format error message
                    error_msg = self._clean_error_message(failed_test["error_message"])
                    message += f"   *Error:* {error_msg}\n"

                # Test duration
                if failed_test["duration"]:
                    message += f"   *Duration:* {failed_test['duration']:.2f}s\n"

                # Screenshot info
                if failed_test.get("screenshot_path"):
                    message += f"   *Screenshot:* `{failed_test['screenshot_path']}`\n"

                # Additional context based on test type
                context = self._get_test_context(failed_test["test_name"])
                if context:
                    message += f"   *Context:* {context}\n"

        slack_notifier.send_webhook_message(message)

    def _clean_error_message(self, error_message):
        """Clean and format error message for Slack"""
        # Remove Python traceback and keep only the meaningful part
        lines = error_message.split("\n")
        clean_lines = []

        for line in lines:
            line = line.strip()
            # Skip traceback lines and keep only error messages
            if (
                line.startswith('File "')
                or line.startswith("self = <")
                or "object at 0x" in line
                or line.startswith("E   ")
                or not line
            ):
                continue

            # Keep assertion errors, failure messages, etc.
            if (
                "AssertionError" in line
                or "Failed:" in line
                or "Error:" in line
                or "Exception:" in line
            ):
                clean_lines.append(line)

        # If we found clean lines, use them
        if clean_lines:
            return " | ".join(clean_lines[:3])  # Max 3 lines

        # Otherwise, return first 150 chars of original message
        return error_message[:150] + ("..." if len(error_message) > 150 else "")

    def _get_test_context(self, test_name):
        """Provide context about what the test was doing"""
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
            # Flight API Tests
            "test_flight_search_request": "Creating flight search requests via API",
            "test_get_flight_search_results": "Retrieving flight search results via API",
            "test_get_booked_flights": "Fetching user's booked flights via API",
        }

        return context_map.get(test_name, "Functional test")


# ====== GLOBAL INSTANCE ======
# Global instance for smoke tests
smoke_reporting = GeoReporter("Smoke Tests")
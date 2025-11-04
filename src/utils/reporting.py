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
    def __init__(self, test_suite_name="SMOKE TESTS"):
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
        
        self.branch = os.getenv("BRANCH") or os.getenv("GIT_BRANCH") or "MAIN"
        self.build_id = os.getenv("BUILD_ID") or f"#{datetime.now().strftime('%Y.%m.%d.%H%M')}"
        self.browser = os.getenv("BROWSER", "CHROME").upper()
        self.test_type, self.test_scope = self._determine_test_type()
            
    def _determine_test_type(self):
        """Determine if this is API, UI, or mixed test suite"""
        suite_lower = self.test_suite_name.lower()

        if "api" in suite_lower:
            return "API", "BACKEND"
        elif any(ui_type in suite_lower for ui_type in ["smoke", "regression", "sanity", "ui"]):
        # elif any(ui_type in suite_lower for ui_type in ["smoke", "regression", "sanity", "ui", "flight", "package", "login", "homepage"]):
            return "UI", "FRONTEND"
        else:
            return "MIXED", "FRONTEND & BACKEND"
    
    def _determine_scope_from_suite_names(self, suite_names):
        """Determine scope from suite names"""
        has_frontend = any(suite in ["smoke", "regression", "sanity"] for suite in suite_names)
        has_backend = "api" in suite_names

        if has_frontend and has_backend:
            return "FRONTEND & BACKEND"
        elif has_frontend:
            return "FRONTEND"
        elif has_backend:
            return "BACKEND"
        return "UNKNOWN"

    def start_test_suite(self):
        """Start tracking test suite"""
        self.suite_start_time = datetime.now()
        self.test_results = []
        self.logger.info(f"Starting test suite: {self.test_suite_name}")

    def start_unified_test_run(self, suite_names):
        """Start unified test run for multiple suites"""
        self.overall_start_time = datetime.now()
        self.suite_results = {}
        self.test_suite_name = f"Unified {self._format_suite_names(suite_names)} TEST REPORT"

        self.test_scope = self._determine_scope_from_suite_names(suite_names)
        self.test_type = "MIXED" if self.test_scope == "FRONTEND & BACKEND" else self.test_scope

        self.logger.info(f"Starting unified test run for: {', '.join(suite_names)}")

        # Send start notification with scope info
        scope_icon = self._get_scope_icon(self.test_scope)
        slack_notifier.send_webhook_message(
            f"🚀 Hey Team, GEO-Bot here! 🤖\n"
            f"✨ *[{self.env}] {self.test_suite_name}* Suite has Officially *Launched*!\n"
            f"{scope_icon} *Scope:* {self.test_scope}\n"
            f"🕒 *Start Time:* {self.overall_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Let's squash some bugs! 🐛🔨"
        )

    def add_test_result(
        self, test_name, status, error_message=None, screenshot_path=None, duration=None, skip_reason=None
    ):
        """Add individual test result with comprehensive metadata"""
        actual_duration = duration or 0.0
        
        test_result = {
            "test_name": test_name,
            "status": status,
            "error_message": error_message,
            "screenshot_path": screenshot_path,
            "duration": actual_duration,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "skip_reason": skip_reason,
            "category": self._get_test_category(test_name, error_message) if status == "FAIL" else None,
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
            report = {
                "test_suite_name": self.test_suite_name,
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "skipped_tests": 0,
                "success_rate": 0,
                "duration": (self.suite_end_time - self.suite_start_time).total_seconds(),
                "start_time": self.suite_start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": self.suite_end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "failed_tests_details": [],
                "skipped_tests_details": [],
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

            # Collect skipped tests with suite context
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
    def _determine_unified_scope(self):
        """Determine the scope for unified reports based on included suites"""
        if not self.suite_results:
            return "UNKNOWN"

        has_frontend = any(suite in ["smoke", "regression", "sanity"] for suite in self.suite_results.keys())
        has_backend = "api" in self.suite_results.keys()

        if has_frontend and has_backend:
            return "FRONTEND & BACKEND"
        elif has_frontend:
            return "FRONTEND"
        elif has_backend:
            return "BACKEND"
        else:
            return "UNKNOWN"

    def _get_scope_icon(self, scope):
        """Get appropriate icon for the scope"""
        icon_map = {
            "FRONTEND": "💻",
            "BACKEND": "🔧", 
            "FRONTEND & BACKEND": "🔗",
            "UNKNOWN": "❓"
        }
        return icon_map.get(scope, "❓")

    def send_unified_slack_report(self):
        """Send enhanced unified report to Slack with new formatting"""
        unified_report = self.generate_unified_report()
        if not unified_report:
            self.logger.warning("No test results to report")
            return

        # Calculate duration in minutes and seconds
        total_seconds = unified_report["duration"]
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        duration_formatted = f"{total_seconds:.1f}s ({minutes}m {seconds}s)" if minutes > 0 else f"{total_seconds:.1f}s"

        # Determine overall status
        if unified_report["failed_tests"] == 0:
            status_emoji = "✅✅✅"
            status_message = "🎉 Great news team! All tests passed. GEO-Bot is proud 🤖✨"
        else:
            status_emoji = "❌❌❌" 
            status_message = "⚠️ Uh-oh, GEO-Bot spotted some issues! Please check the details below 🐞🔧"

        unified_scope = self._determine_unified_scope()
        scope_icon = self._get_scope_icon(unified_scope)

        message_lines = [
            "",
            f"*🧪 {unified_report['test_suite_name']}*",
            f"Executed: {unified_report['end_time']}",
            f"Environment: {self.env}",
            f"Branch: {self.branch}",
        ]

        # Add browser info only for FRONTEND tests
        if unified_scope in ["FRONTEND", "FRONTEND & BACKEND"]:
            message_lines.append(f"Browser: {self.browser}")

        # Add scope line
        message_lines.append(f"Scope: {unified_scope}")
        
        # Alternatively, include icon
        # message_lines.append(f"{scope_icon} Scope: {unified_scope}")
        message_lines.append(f"Build ID: {self.build_id}")

        message_lines.extend([
            "",
            "------------------------------------------------------",
            f"{status_emoji} {status_message}",
            "------------------------------------------------------",
            "",
            "*📊 Summary*\n",
            f"• Total Tests: {unified_report['total_tests']}",
            f"• ✅ Passed: {unified_report['passed_tests']}",
            f"• ⚠️ Skipped: {unified_report['skipped_tests']}",
            f"• ❌ Failed: {unified_report['failed_tests']}",
            f"• 🧮 Success Rate: {unified_report['success_rate']:.1f}%",
            f"• 🕒 Duration: {duration_formatted}",
            "",
            "------------------------------------------------------",
            "",
            "🧠 Suite Breakdown",
            ""
        ])
        
        # Add suite breakdown
        for suite_name, suite_data in self.suite_results.items():
            report = suite_data["report"]
            total = report.get('total_tests', 0)
            passed = report.get('passed_tests', 0)
            success_rate = (passed / total * 100) if total > 0 else 0
            suite_display = self._format_suite_display_name(suite_name)
            message_lines.append(f"{suite_display}: {passed}/{total} Passed ({success_rate:.0f}%)")

        message_lines.append("------------------------------------------------------")

        # Add failed tests section
        all_failed_tests = unified_report["all_failed_tests"]
        if all_failed_tests:
            message_lines.append(f"❌ Failed Tests({len(all_failed_tests)})")
            message_lines.append("")

            for i, test in enumerate(all_failed_tests[:8], 1):  # Limit to first 8
                suite = test.get('suite', 'Unknown')
                test_name = test.get('test_name', 'Unknown Test')
                error = self._clean_error_message(test.get('error_message', 'Unknown error'))
                category = test.get('category') or self._get_test_category(test_name, error)
                context = self._get_test_context(test_name, error)
                duration = test.get('duration', 0)
                
                # Format test name to be more readable
                readable_test_name = self._format_test_name(test_name)
                suite_display = self._format_suite_display_name(suite)
                
                message_lines.append(f"{i}️⃣ [{suite_display}] {readable_test_name}")
                message_lines.append(f"‣ Error: {error}")
                message_lines.append(f"‣ Context: {context}")
                message_lines.append(f"‣ Issue Type: {category}")
                
                # Add fix suggestion for specific categories
                fix_suggestion = self._get_fix_suggestion(category, test_name)
                if fix_suggestion:
                    message_lines.append(f"‣ Fix Suggestion: {fix_suggestion}")
                
                if duration > 0:
                    message_lines.append(f"‣ Duration: {duration:.2f}s")
                
                message_lines.append("")  # Empty line between tests

        # Add skipped tests section
        all_skipped_tests = unified_report.get("all_skipped_tests", [])
        if all_skipped_tests:
            if not all_failed_tests:  # Add separator only if no failed tests section
                message_lines.append("------------------------------------------------------")
            message_lines.append(f"⚠️ Skipped Tests({len(all_skipped_tests)})")
            message_lines.append("")

            for skipped_test in all_skipped_tests[:5]:  # Limit to first 5
                suite = skipped_test.get('suite', 'Unknown')
                test_name = skipped_test.get('test_name', 'Unknown Test')
                skip_reason = self._clean_error_message(skipped_test.get('skip_reason', 'Skipped'))
                readable_test_name = self._format_test_name(test_name)
                suite_display = self._format_suite_display_name(suite)
                
                message_lines.append(f"• [{suite_display}] {readable_test_name} → Reason: \"{skip_reason}\"")

        # Join all lines and send
        final_message = "\n".join(message_lines)
        slack_notifier.send_webhook_message(final_message)
        self._save_unified_report(unified_report)

    def send_individual_slack_report(self, report):
        """Send enhanced individual suite report to Slack"""
        if not report:
            return

        # Calculate duration
        total_seconds = report["duration"]
        minutes = int(total_seconds // 60)
        seconds = int(total_seconds % 60)
        duration_formatted = f"{total_seconds:.1f}s ({minutes}m {seconds}s)" if minutes > 0 else f"{total_seconds:.1f}s"

        # Determine overall status
        if report["failed_tests"] == 0:
            status_emoji = "✅✅✅"
            status_message = "🎉 Great news team! All tests passed. GEO-Bot is proud 🤖✨"
        else:
            status_emoji = "❌❌❌" 
            status_message = "⚠️ Uh-oh, GEO-Bot spotted some issues! Please check the details below 🐞🔧"

        # Determine scope icon
        scope_icon = self._get_scope_icon(self.test_scope)

        # Build message lines
        message_lines = [
            "",
            f"*🧪 {self.test_suite_name} REPORT*",
            f"Executed: {report['end_time']}",
            f"Environment: {self.env}",
            f"Branch: {self.branch}",
        ]
        
        if self.test_scope in ["FRONTEND", "FRONTEND & BACKEND"]:
            message_lines.append(f"Browser: {self.browser}")

        # Add scope line
        message_lines.append(f"Scope: {self.test_scope}")

        # Alternatively, include icon
        # message_lines.append(f"{scope_icon} Scope: {unified_scope}")
        message_lines.append(f"Build ID: {self.build_id}")

        message_lines.extend([
            "",
            "------------------------------------------------------",
            f"{status_emoji} {status_message}",
            "------------------------------------------------------",
            "",
            "*📊 Summary*\n",
            f"• Total Tests: {report['total_tests']}",
            f"• ✅ Passed: {report['passed_tests']}",
            f"• ⚠️ Skipped: {report['skipped_tests']}",
            f"• ❌ Failed: {report['failed_tests']}",
            f"• 🧮 Success Rate: {report['success_rate']:.1f}%",
            f"• 🕒 Duration: {duration_formatted}",
            "",
            "------------------------------------------------------"
            "",
        ])

        # Add failed tests section
        if report["failed_tests"] > 0:
            message_lines.append(f"❌ Failed Tests({report['failed_tests']})")
            message_lines.append("")

            for i, failed_test in enumerate(report["failed_tests_details"], 1):
                test_name = failed_test['test_name']
                error = self._clean_error_message(failed_test['error_message'])
                category = failed_test.get('category') or self._get_test_category(test_name, error)
                context = self._get_test_context(test_name, error)
                duration = failed_test.get('duration', 0)
                readable_test_name = self._format_test_name(test_name)
                
                message_lines.append(f"{i}️⃣ {readable_test_name}")
                message_lines.append(f"‣ Error: {error}")
                message_lines.append(f"‣ Type: {category}")
                message_lines.append(f"‣ Context: {context}")

                # Add fix suggestion
                fix_suggestion = self._get_fix_suggestion(category, test_name)
                if fix_suggestion:
                    message_lines.append(f"‣ Fix Suggestion: {fix_suggestion}")
                
                if duration > 0:
                    message_lines.append(f"‣ Duration: {duration:.2f}s")
                
                message_lines.append("")

        # Add skipped tests section
        if report.get("skipped_tests_details"):
            if report["failed_tests"] == 0:  # Add separator only if no failed tests
                message_lines.append("------------------------------------------------------")
            message_lines.append(f"⚠️ Skipped Tests({report['skipped_tests']})")
            message_lines.append("")

            for skipped_test in report["skipped_tests_details"][:5]:
                test_name = skipped_test['test_name']
                skip_reason = self._clean_error_message(skipped_test.get('skip_reason', 'Skipped'))
                readable_test_name = self._format_test_name(test_name)
                
                message_lines.append(f"• {readable_test_name} → Reason: \"{skip_reason}\"")

        final_message = "\n".join(message_lines)
        slack_notifier.send_webhook_message(final_message)
        self._save_report_to_file(report)

    # ====== HELPER METHODS ======
    def _format_suite_names(self, suite_names):
        """Format suite names for the report header"""
        formatted_names = []
        for name in suite_names:
            formatted_names.append(self._format_suite_display_name(name))
        return " + ".join(formatted_names)

    def _format_suite_display_name(self, suite_name):
        """Format individual suite name for display"""
        name_map = {
            "api": "API",
            "smoke": "UI Smoke", 
            "regression": "UI Regression",
            "sanity": "UI Sanity"
        }
        return name_map.get(suite_name, suite_name.upper())

    def _format_test_name(self, test_name):
        """Format test name to be more readable"""
        if "::" in test_name:
            parts = test_name.split("::")
            if len(parts) >= 3:
                class_name = parts[1].replace("Test", "").strip()
                method_name = parts[2]
                return f"{class_name}.{method_name}"
            elif len(parts) == 2:
                file_name = parts[0].split("/")[-1].replace(".py", "").replace("test_", "")
                method_name = parts[1]
                return f"{file_name}.{method_name}"
        return test_name

    def _get_test_context(self, test_name, error_message):
        """Categorize test failures for better reporting"""
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
    
    def _get_test_category(self, test_name, error_message):
        """Categorize test failures based on error messages and test names"""
        if not error_message:
            return "Unknown"
            
        error_lower = error_message.lower()
        test_lower = test_name.lower()
        
        # API Test Categories
        if "api" in test_lower:
            if "assertionerror" in error_lower or "expected" in error_lower:
                return "Functional"
            elif "dependency" in error_lower or "login failed" in error_lower:
                return "Dependency Failure"
            elif "timeout" in error_lower:
                return "API Timeout"
            else:
                return "API Error"
        
        # UI Test Categories  
        elif "elementclickintercepted" in error_lower:
            return "Wait Condition Issue"
        elif "timeout" in error_lower:
            if "loader" in error_lower or "page load" in error_lower:
                return "Slow Page Load / Loader Interference"
            return "Timeout Exception"
        elif "nosuchelement" in error_lower:
            return "Element Not Found"
        elif "staleelement" in error_lower:
            return "Stale Element Reference"
        else:
            return "Functional"

    def _get_fix_suggestion(self, category, test_name):
        """Provide fix suggestions based on failure category"""
        suggestions = {
            "Wait Condition Issue": "Add EC.element_to_be_clickable() with explicit wait",
            "Slow Page Load / Loader Interference": "Increase timeout or add loader wait condition",
            "Element Not Found": "Check element locator or add explicit wait",
            "Stale Element Reference": "Re-locate element before interaction",
            "API Timeout": "Increase API timeout or check endpoint responsiveness",
            "Dependency Failure": "Check prerequisite test steps or data setup",
            "Timeout Exception": "Increase wait time or optimize page load",
            "API Error": "Check API endpoint and request parameters"
        }
        return suggestions.get(category, "")

    def _clean_error_message(self, error_message):
        """Clean and format error message for Slack"""
        if not error_message:
            return "No error message"
            
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
        
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.strftime("%Y-%m-%d %H:%M:%S")
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
        
        with open(filename, "w") as f:
            json.dump(report, f, indent=4, default=json_serializer)
        self._cleanup_old_reports()

    def _save_unified_report(self, unified_report):
        """Save unified report to file"""
        os.makedirs("reports", exist_ok=True)
        filename = f"reports/unified_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.strftime("%Y-%m-%d %H:%M:%S")
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
        
        with open(filename, "w") as f:
            json.dump(unified_report, f, indent=4, default=json_serializer)
        self._cleanup_old_reports()


# ====== GLOBAL INSTANCES ======
# Individual suite reporters
smoke_reporting = GeoReporter("UI SMOKE TEST")
regression_reporting = GeoReporter("UI REGRESSION TEST")
sanity_reporting = GeoReporter("UI SANITY TEST")
api_smoke_reporting = GeoReporter("API SMOKE TEST")
api_regression_reporting = GeoReporter("API REGRESSION TEST")
api_sanity_reporting = GeoReporter("API SANITY TEST")

# Unified reporter instance
unified_reporter = smoke_reporting

def get_suite_reporter(suite_name):
    """Get the appropriate reporter for the test suite"""
    reporters = {
        "smoke": smoke_reporting,
        "regression": regression_reporting, 
        "sanity": sanity_reporting,
        "api": api_smoke_reporting,
        "api_regression": api_regression_reporting,
        "api_sanity": api_sanity_reporting
    }
    return reporters.get(suite_name, smoke_reporting)
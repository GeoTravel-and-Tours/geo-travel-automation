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
        elif "partners_api" in suite_lower or "partners" in suite_lower:
            return "PARTNERS_API", "PARTNERS_BACKEND"
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
        self, test_name, status, error_message=None, screenshot_path=None, duration=None, skip_reason=None, evidence=None
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
        # Attach additional evidence metadata (logs, response files, etc.)
        if evidence and isinstance(evidence, dict):
            test_result["evidence"] = evidence
            # If a log path was provided, expose it as a downloadable link
            log_path = evidence.get("log_path")
            if log_path:
                test_result["log_path"] = str(log_path)
                # Prefer an absolute hosted URL so Slack will render it as a clickable link.
                gh_pages = os.getenv("GH_PAGES_BASE_URL", "https://geotravel-and-tours.github.io/geo-travel-automation")
                timestamp = os.getenv("RUN_TIMESTAMP", "")
                if timestamp:
                    test_result["log_url"] = f"{gh_pages}/{timestamp}/logs/{Path(log_path).name}"
                else:
                    test_result["log_url"] = f"{gh_pages}/reports/logs/{Path(log_path).name}"
            # If a response dump file exists, provide its hosted URL too
            resp_file = evidence.get("response_file")
            if resp_file:
                test_result.setdefault("evidence", {})
                test_result["evidence"]["response_file"] = str(resp_file)
                gh_pages = os.getenv("GH_PAGES_BASE_URL", "https://geotravel-and-tours.github.io/geo-travel-automation")
                test_result["response_file_url"] = f"{gh_pages}/reports/failed_responses/{Path(resp_file).name}"
        if screenshot_path:
            screenshot_filename = Path(screenshot_path).name
            timestamp = os.getenv("RUN_TIMESTAMP", "")
            if timestamp:
                test_result["screenshot_url"] = f"https://geotravel-and-tours.github.io/geo-travel-automation/{timestamp}/screenshots/{screenshot_filename}"
            else:
                test_result["screenshot_url"] = f"https://geotravel-and-tours.github.io/geo-travel-automation/screenshots/failures/{screenshot_filename}"

        self.test_results.append(test_result)
        self.logger.info(f"Test result added: {test_name} - {status} (Duration: {actual_duration:.2f}s)")

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
            "PARTNERS_BACKEND": "🤝",
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
            
        # NEW: Add @channel mention when tests fail
        if unified_report["failed_tests"] > 0:
            message_lines = [
                "<!channel> 🚨",
                "",
                f"*🧪 {unified_report['test_suite_name']}*",
            ]
        else:
            message_lines = [
                "",
                f"*🧪 {unified_report['test_suite_name']}*",
                ]    # Start with empty line for success case

        unified_scope = self._determine_unified_scope()
        scope_icon = self._get_scope_icon(unified_scope)

        message_lines.extend([
            f"Executed: {unified_report['end_time']}",
            f"Environment: {self.env}",
            f"Branch: {self.branch}",
        ])

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

            # Limit how many failures to display in Slack to avoid huge messages.
            # Configurable via env var REPORT_MAX_FAILURES (default 8)
            try:
                max_failures = int(os.getenv("REPORT_MAX_FAILURES", "8"))
            except Exception:
                max_failures = 8

            # If you want to see ALL failures in the message, replace the slice below
            # with `for i, test in enumerate(all_failed_tests, 1):` — commented out on purpose.
            for i, test in enumerate(all_failed_tests[:max_failures], 1):
                suite = test.get('suite', 'Unknown')
                test_name = test.get('test_name', 'Unknown Test')
                raw_error = test.get('error_message', 'Unknown error')
                error = self._clean_error_message(raw_error)
                category = test.get('category') or self._get_test_category(test_name, raw_error)
                context = self._get_test_context(test_name, raw_error)
                duration = test.get('duration', 0)

                # Format test name to be more readable
                readable_test_name = self._format_test_name(test_name)
                suite_display = self._format_suite_display_name(suite)

                # Expected vs Actual extraction where possible
                expected_actual = self._extract_expected_actual(raw_error) or "See error message"

                message_lines.append(f"{i}️⃣ [{suite_display}] {readable_test_name}")
                message_lines.append(f"• Error: {error}")
                message_lines.append(f"• Context: {context}")
                message_lines.append(f"• Expected vs Actual: {expected_actual}")
                message_lines.append(f"• Evidence: {self._get_failure_links(test)}")

                # Add fix suggestion for specific categories
                fix_suggestion = self._get_fix_suggestion(category, test_name)
                if fix_suggestion:
                    message_lines.append(f"• Suggested Fix: {fix_suggestion}")

                if duration > 0:
                    message_lines.append(f"• Duration: {duration:.2f}s | Timestamp: {test.get('timestamp', '')}")

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
                raw_error = failed_test.get('error_message', '')
                error = self._clean_error_message(raw_error)
                category = failed_test.get('category') or self._get_test_category(test_name, raw_error)
                context = self._get_test_context(test_name, raw_error)
                duration = failed_test.get('duration', 0)
                readable_test_name = self._format_test_name(test_name)

                # Expected vs Actual extraction
                expected_actual = self._extract_expected_actual(raw_error) or "See error message"

                suite_display = self._format_suite_display_name("individual")
                message_lines.append(f"{i}️⃣ [{suite_display}] {readable_test_name}")
                message_lines.append(f"• Error: {error}")
                message_lines.append(f"• Context: {context}")
                message_lines.append(f"• Expected vs Actual: {expected_actual}")
                message_lines.append(f"• Evidence: {self._get_failure_links(failed_test)}")

                # Add fix suggestion
                fix_suggestion = self._get_fix_suggestion(category, test_name)
                if fix_suggestion:
                    message_lines.append(f"• Suggested Fix: {fix_suggestion}")

                if duration > 0:
                    message_lines.append(f"• Duration: {duration:.2f}s | Timestamp: {failed_test.get('timestamp', '')}")

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
            "sanity": "UI Sanity",
            "partners_api": "Partners API",
            "partners_api_regression": "Partners API Regression", 
            "partners_auth": "Partners Auth API",
            "partners_flight": "Partners Flight API",
            "partners_package": "Partners Package API", 
            "partners_organization": "Partners Organization API"
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
            "test_homepage_loads_successfully": "Homepage loading and basic validation - quick smoke check",
            "test_basic_homepage_elements_exist": "Checking page structure, HTML, and core elements exist",
            "test_homepage_navigation_works": "Testing page navigation links and functionality",
            "test_homepage_health_check": "Overall page health, logo visibility, and validation",
            
            # Login/Auth Tests
            "test_login_page_accessibility": "Login page structure check and required elements validation",
            "test_successful_login_and_redirect": "User authentication flow with valid credentials",
            "test_failed_login_with_error_message": "Invalid login handling and error messaging",
            "test_logout_functionality": "User session termination and logout flow",
            
            # Flight Booking Tests
            "test_flight_search_form_visible": "Flight search form visibility and accessibility",
            "test_error_handling": "Error scenarios handling during flight booking",
            
            # Package Booking Tests
            "test_package_search_functionality": "Searching for travel packages with filters and validation",
            "test_booking_form_navigation_on_homepage": "Booking form basic navigation and interaction",
            "test_complete_package_booking_flow": "End-to-end package booking process with payment flow",
            
            # Visa Tests
            "test_visa_page_navigation": "Visa page loading and navigation verification",
            "test_visa_form_basic_interaction": "Visa form basic input acceptance and field validation",
            "test_dropdown_functionality": "All visa form dropdowns functionality testing",
            "test_date_picker_functionality": "Travel date picker functionality verification",
            "test_complete_visa_application_flow": "Comprehensive end-to-end visa application submission",
            "test_visa_application_cancel_flow": "Visa application cancellation functionality",
            
            
            
            #============================ API Tests ============================#
            # Auth API Tests
            "test_login_success": "Successful user login with valid credentials from environment variables",
            "test_login_invalid_credentials": "Testing login failure with invalid email/password combination",
            "test_login_empty_credentials": "Validating API response for empty username and password fields",
            "test_login_missing_password": "Testing login failure when password field is empty",
            "test_auth_token_set_after_successful_login": "Verifying authentication token is properly set after successful login",
            "test_dynamic_token_extraction": "Testing dynamic token extraction from response body, cookies, or headers",
            "test_token_validation": "Validating token extraction and format verification functionality",

            # Flight API Tests  
            "test_flight_search_request": "Creating flight search requests via API",
            "test_flight_search_flow": "End-to-end flight search process via API",
            "test_flight_quote_flow": "Flight quoting process via API",
            "test_passenger_email_validation": "Validating passenger email via API",
            "test_different_cabins": "Testing different cabin classes via API",
            "test_get_booked_flights": "Fetching user's booked flights via API",
            "test_return_flight_search": "Testing return flight search via API",
            "test_passenger_combinations": "Testing different passenger combinations via API",
            "test_initiate_booking_flow": "Testing flight booking initiation via API",
            "test_error_scenarios": "Testing error handling in flight booking via API",

            # Miscellaneous API Tests
            "test_get_google_reviews": "Fetching Google business reviews via API",
            "test_get_commercial_deals": "Fetching commercial deals with pagination (limit=5)",
            "test_get_single_commercial_deal": "Fetching a single commercial deal by ID (dynamic from deals list)",
            "test_get_all_events": "Fetching all events with pagination (limit=5)",
            "test_get_airports": "Fetching airport codes and information via API",
            "test_get_airlines": "Fetching airline codes and information via API",
            "test_get_all_blogs": "Fetching all blog posts with pagination (limit=5)",
            "test_get_single_blog": "Fetching a single blog post by ID (dynamic from blogs list)",
            "test_get_blog_comments": "Fetching comments for a specific blog post (dynamic blog ID)",
            "test_refresh_token": "Refreshing authentication token with current session",
            "test_get_user_profile": "Fetching authenticated user's profile information",
            "test_get_user_transactions": "Fetching user's transaction history with pagination (limit=5)",
            "test_get_notifications": "Fetching user's notifications list",
            "test_subscribe_newsletter": "Subscribing user email to newsletter service",
            "test_apply_voucher": "Applying voucher/promo code for discounts",

            # Packages API Tests
            "test_get_all_packages": "Getting all packages with pagination,",
            "test_get_package_countries": "Getting list of countries where packages are available",
            "test_get_single_package": "Getting a single package by ID (fetches first available package)",
            "test_search_packages": "Searching packages with filters",
            "test_get_all_deals": "Getting all package deals with active filters",
            "test_get_single_deal": "Getting a single deal by ID",
            "test_book_package_and_verify_user_bookings": "End-to-end test: Booking a package and verifying it appears in user bookings with payment verification",
            "test_book_package_without_auth_not_in_user_bookings": "Testing unauthenticated booking attempts and user bookings access",
            "test_get_user_booked_packages": "Getting user's booked packages with optional filters",
            "test_get_user_booked_packages_analytics": "Getting user's booking analytics and statistics",
            
            #Hotel API Tests
            "test_get_hotel_cities_success": "Getting hotel cities with valid keyword search ('ABU')",
            "test_get_hotel_cities_empty_keyword": "Testing hotel cities endpoint with empty keyword (should reject)",
            "test_get_hotel_cities_invalid_keyword": "Testing hotel cities with various invalid keywords",
            "test_search_hotels_without_price": "Searching hotels without price range filter",
            "test_search_hotels_with_price_range_currency": "Searching hotels with price range and currency filter",
            "test_search_hotels_missing_required_fields": "Testing hotel search with missing required fields",
            "test_search_hotels_pagination": "Testing hotel search pagination functionality with different page/limit combinations",
            "test_search_hotels_invalid_dates": "Testing hotel search with various invalid date combinations",
            "test_get_hotel_rating_success": "Getting hotel rating for a valid hotel ID (fetched from search results)",
            "test_get_hotel_rating_invalid_id": "Testing hotel rating with invalid/non-existent hotel IDs",
            "test_book_hotel_without_auth": "Booking hotel WITHOUT authentication (user_id must be null)",
            "test_book_hotel_with_auth": "Booking hotel WITH authentication (must have user_id attached)",
            "test_book_hotel_missing_required_fields": "Testing hotel booking with missing required fields",
            "test_search_hotels_performance_without_auth": "Testing hotel search response time performance WITHOUT authentication",
            "test_search_hotels_performance_with_auth": "Testing hotel search response time performance WITH authentication",
            "test_hotel_endpoints_without_auth": "Testing all hotel endpoints accessibility WITHOUT authentication",
            "test_hotel_endpoints_with_auth": "Testing all hotel endpoints accessibility WITH authentication",
            
            #Visa API Tests
            "test_create_visa_enquiry_without_auth": "Creating visa enquiry WITHOUT authentication (user_id must be null)",
            "test_create_visa_enquiry_with_auth": "Creating visa enquiry WITH authentication (must have user_id attached)",
            "test_create_visa_enquiry_missing_required_fields": "Testing visa enquiry creation with various missing required fields",
            "test_create_visa_enquiry_invalid_type": "Testing visa enquiry creation with invalid visa types",
            "test_create_visa_enquiry_invalid_dates": "Testing visa enquiry creation with invalid travel dates",
            "test_make_payment_flutterwave_without_auth": "Making payment with Flutterwave WITHOUT authentication",
            "test_make_payment_bank_transfer_without_auth": "Making payment with Bank Transfer WITHOUT authentication",
            "test_make_payment_flutterwave_with_auth": "Making payment with Flutterwave WITH authentication",
            "test_make_payment_invalid_visa_id": "Making payment with invalid/non-existent visa ID",
            "test_make_payment_invalid_method": "Making payment with invalid payment methods",
            "test_get_user_visa_applications_with_auth": "Getting user's visa applications WITH authentication",
            "test_get_user_visa_applications_without_auth": "Getting user's visa applications WITHOUT authentication (should reject)",
            "test_get_user_visa_applications_with_filters": "Getting user's visa applications with various filters (status, type, date range)",
            "test_get_user_visa_applications_pagination": "Testing user visa applications pagination functionality",
            "test_get_visa_application_by_id_with_auth": "Getting specific visa application by ID WITH authentication",
            "test_get_visa_application_by_id_without_auth": "Getting specific visa application by ID WITHOUT authentication",
            "test_complete_visa_flow_with_auth": "Complete end-to-end visa flow test WITH authentication",
            "test_complete_visa_flow_without_auth": "Complete end-to-end visa flow test WITHOUT authentication",
            
            
            
            # ============================ PARTNERS API TESTS ============================ #
            # Partners Auth API Tests
            "test_welcome_message": "Partners API gateway connectivity and welcome message verification",
            "test_organization_signup_success": "Organization registration process via Partners API",
            "test_organization_login_unverified_returns_no_token": "Unverified user authentication flow - token denial",
            "test_verified_user_login_returns_token": "Verified user token generation and JWT validation",
            "test_verified_user_login_response_structure": "Verified user login response structure validation",
            
            # Partners Flight API Tests
            "test_partners_dynamic_token_extraction": "Dynamic token extraction from Partners API responses",
            "test_unverified_user_blocked_from_flight_search": "Security validation - unverified users blocked from flight search",
            "test_unverified_user_blocked_from_flight_booking": "Security validation - unverified users blocked from flight booking",
            "test_verified_user_can_search_flights": "Flight search functionality for verified partners with response structure validation",
            "test_verified_user_can_book_flight": "Flight booking functionality for verified partners including response validation",
            "test_flight_search_counted_in_usage": "Flight search usage tracking and analytics verification",
            "test_flight_booking_counted_in_usage": "Flight booking usage tracking and analytics verification",
            "test_flight_usage_reflected_in_range_endpoint": "Flight usage range reporting and data aggregation validation",
            
            # Partners Package API Tests
            "test_verified_user_can_get_packages": "Package listing access for verified partners with response structure validation",
            "test_verified_user_can_get_package_countries": "Package countries and cities access for verified partners",
            "test_verified_user_can_book_package": "Package booking functionality for verified partners",
            "test_package_booking_appears_in_bookings_list": "Package booking record validation and appearance in bookings list",
            "test_package_booking_counted_in_usage": "Package booking usage tracking and analytics verification",
            "test_package_usage_reflected_in_range_endpoint": "Package usage range reporting and data aggregation validation",
            "test_unverified_user_blocked_from_package_listing": "Package API security validation - unverified users blocked",
            "test_unverified_user_blocked_from_package_countries": "Package countries security - unverified users blocked",
            "test_unverified_user_blocked_from_package_booking": "Package booking security - unverified users blocked",
            
            # Partners Organization API Tests  
            "test_verified_user_can_access_profile": "Organization profile access for verified partners",
            "test_verified_user_can_reset_api_keys": "API key management and reset functionality for verified partners",
            "test_verified_user_can_access_usage_data": "Organization usage data access for verified partners",
            "test_verified_account_status": "Verified account validation and status verification",
            "test_usage_records_contain_flight_data": "Flight data presence and structure in usage records",
            "test_usage_records_contain_package_data": "Package data presence and structure in usage records",
            "test_usage_range_shows_cumulative_data": "Cumulative usage reporting and data aggregation validation",
            "test_unverified_user_blocked_from_all_organization_endpoints": "Organization API security - comprehensive endpoint blocking",
            "test_unverified_login_returns_no_token": "Unverified login token validation - token denial verification",
            "test_malformed_token_returns_401": "Token validation security - malformed token rejection",
            "test_expired_token_returns_401": "Token expiration handling - expired token rejection",
            "test_credential_initialization_flow": "Credential initialization and verification process",
            "test_package_booking_creates_complete_record": "Complete package booking record creation and validation"
        }

        return context_map.get(method_name, "Functional test")
    
    def _get_test_category(self, test_name, error_message):
        """Categorize test failures based on error messages and test names"""
        if not error_message:
            return "Unknown"

        error_lower = error_message.lower()
        test_lower = test_name.lower()
        
        # PARTNERS API SPECIFIC CATEGORIES
        if "partners_api" in test_lower or "partners" in test_lower:
            if "500" in error_lower or "internal server" in error_lower:
                return "Partners API Server Error"
            if "502" in error_lower or "bad gateway" in error_lower:
                return "Partners API Gateway Error"
            if "503" in error_lower or "service unavailable" in error_lower:
                return "Partners API Service Unavailable"
            if "404" in error_lower or "not found" in error_lower:
                return "Partners API Resource Not Found"
            if "400" in error_lower or "bad request" in error_lower:
                return "Partners API Request Validation"
            elif "401" in error_lower or "unauthorized" in error_lower:
                return "Partners API Authentication"
            elif "403" in error_lower or "forbidden" in error_lower:
                return "Partners API Authorization" 
            elif "token" in error_lower and ("invalid" in error_lower or "expired" in error_lower):
                return "Partners Token Validation"
            elif "verified" in error_lower and "unverified" in error_lower:
                return "Partners Verification Status"
            elif "api key" in error_lower or "api_secret" in error_lower:
                return "Partners API Credentials"
            elif "organization" in error_lower:
                return "Partners Organization Access"
            elif "flight" in error_lower and "search" in error_lower:
                return "Partners Flight Search"
            elif "flight" in error_lower and "book" in error_lower:
                return "Partners Flight Booking" 
            elif "package" in error_lower and "book" in error_lower:
                return "Partners Package Booking"
            elif "usage" in error_lower:
                return "Partners Usage Tracking"
            elif "KeyError" in error_lower or "IndexError" in error_lower:
                return "Partners Response Parsing"
            elif "AssertionError" in error_lower or "expected" in error_lower:
                return "Partners Functional Assertion"
            elif "TypeError" in error_lower or "AttributeError" in error_lower:
                return "Partners Code Logic"
            elif "timeout" in error_lower or "read timed out" in error_lower:
                return "Partners API Timeout"
            elif "connection" in error_lower or "refused" in error_lower:
                return "Partners API Connection"
            elif "valueerror" in error_lower or "bad request" in error_lower:
                return "Partners Request Validation"
            else:
                return "Partners API Error"
        
        # Dependency/Skip related
        if "skip" in error_lower or "skipped" in error_lower or "dependency" in error_lower:
            return "Dependency Failure"
        
        # Environment/Setup issues
        if "environment" in error_lower or "unavailable" in error_lower or "setup" in error_lower:
            return "Environment Setup"
        
        # Network issues
        if "network" in error_lower or "connection" in error_lower or "ssl" in error_lower:
            return "Network Issue"
        
        # Data/State issues  
        if "data" in error_lower or "state" in error_lower or "prerequisite" in error_lower:
            return "Test Data"

        # Airport Selection Failures
        if "failed to select departure airport" in error_lower or "failed to select arrival airport" in error_lower:
            return "Airport Selection"

        # Search Functionality Failures  
        if "search session" in error_lower and "initialized" in error_lower:
            return "Search Initialization"

        # Form Interaction Failures
        if "failed to select" in error_lower and ("date" in error_lower or "calendar" in error_lower):
            return "Date Selection"

        # Dropdown/Selection Failures
        if "failed to select" in error_lower and ("dropdown" in error_lower or "option" in error_lower):
            return "Dropdown Interaction"

        # API Test Categories
        if "api" in test_lower:
            if "timeout" in error_lower or "read timed out" in error_lower:
                return "API Timeout"
            elif "connection" in error_lower or "refused" in error_lower:
                return "API Connection"
            elif "401" in error_lower or "unauthorized" in error_lower:
                return "Authentication"
            if "503" in error_lower or "service unavailable" in error_lower:
                return "API Service Unavailable"
            elif "403" in error_lower or "forbidden" in error_lower:
                return "Authorization"
            elif "404" in error_lower or "not found" in error_lower:
                return "Resource Not Found"
            elif "400" in error_lower or "bad request" in error_lower:
                return "Request Validation"
            elif "500" in error_lower or "internal server" in error_lower:
                return "Server Error"
            elif "keyerror" in error_lower or "indexerror" in error_lower:
                return "Response Parsing"
            elif "assertionerror" in error_lower or "expected" in error_lower:
                return "Functional Assertion"
            elif "dependency" in error_lower or "login failed" in error_lower:
                return "Dependency Failure"
            elif "typeerror" in error_lower or "attributeerror" in error_lower:
                return "Code Logic"
            elif "connection" in error_lower or "refused" in error_lower:
                return "API Connection"
            else:
                return "API Error"

        # UI Test Categories  
        elif "elementclickintercepted" in error_lower:
            return "UI Interaction"
        elif "timeout" in error_lower:
            if "loader" in error_lower or "page load" in error_lower:
                return "Page Load Performance"
            return "UI Timeout"
        elif "nosuchelement" in error_lower:
            return "Element Visibility"
        elif "staleelement" in error_lower:
            return "DOM State"
        elif "javascript" in error_lower:
            return "JavaScript Execution"
        elif "screenshot" in error_lower:
            return "Visual Validation"
        else:
            return "Functional"

    def _get_fix_suggestion(self, category, test_name):
        """Provide fix suggestions based on failure category"""
        suggestions = {
            # Airport Selection Issues
            "Airport Selection": "Update airport locators, add retry logic for airport dropdown, verify airport codes",
            "Search Initialization": "Check search session state, verify package availability, add session validation",
            "Date Selection": "Update date picker locators, add calendar interaction waits, verify date format",
            "Dropdown Interaction": "Add explicit waits for dropdown options, verify option visibility, update selectors",

            # API Categories
            "API Timeout": "Increase API timeout settings or check endpoint responsiveness",
            "API Connection": "Verify network connectivity and API server status",
            "Authentication": "Check auth token validity and refresh mechanism",
            "Authorization": "Verify user permissions and role-based access",
            "Resource Not Found": "Validate resource IDs and endpoint URLs",
            "Request Validation": "Check request parameters and data format",
            "Server Error": "Monitor server logs and check backend services",
            "Response Parsing": "Add response structure validation and error handling",
            "Dependency Failure": "Check prerequisite test steps or data setup",
            "Code Logic": "Review test code for type mismatches or method calls",
            "API Error": "Check API documentation and endpoint specifications",

            # UI Categories
            "UI Interaction": "Add explicit wait conditions for element clickability",
            "Page Load Performance": "Increase timeout or add loader wait conditions",
            "UI Timeout": "Optimize wait strategies and element locators",
            "Element Visibility": "Verify element selectors and page state",
            "DOM State": "Re-locate elements after DOM updates",
            "JavaScript Execution": "Check browser compatibility and script loading",
            "Visual Validation": "Update screenshot references or adjust thresholds",

            # General
            "Functional Assertion": "Review test expectations and actual results",
            "Unknown": "Investigate logs and reproduce manually",
            
            
            # PARTNERS API SPECIFIC SUGGESTIONS
            "Partners API Server Error": "Check Partners API service status, verify endpoint URLs, review server logs",
            "Partners API Authentication": "Verify API credentials, check token validity, validate authentication flow",
            "Partners API Authorization": "Check user permissions, verify organization status, review access controls",
            "Partners Token Validation": "Validate token format, check expiration, verify token generation process",
            "Partners Verification Status": "Confirm email verification status, check verification flow, validate user state",
            "Partners API Credentials": "Verify API key/secret configuration, check credential rotation, validate app ID",
            "Partners Organization Access": "Check organization registration, verify profile access, validate org permissions",
            "Partners Flight Search": "Validate flight search parameters, check availability, verify search session",
            "Partners Flight Booking": "Review booking payload, check passenger data, validate payment flow",
            "Partners Package Booking": "Verify package availability, check booking parameters, validate package status",
            "Partners Usage Tracking": "Check usage recording mechanism, verify data aggregation, validate reporting endpoints",
            "Partners API Error": "Review Partners API documentation, check request/response format, validate endpoints",
        }
        return suggestions.get(category, "Review test implementation and error logs")

    def _extract_expected_actual(self, error_message: str):
        """Try to extract Expected vs Actual from common assertion patterns."""
        if not error_message:
            return None
        import re

        # common pattern: assert 500 == 200
        m = re.search(r"assert\s+([^\s]+)\s*==\s*([^\s]+)", error_message)
        if m:
            return f"Expected: {m.group(2)} | Actual: {m.group(1)}"

        # pattern: expected 200 but got 500
        m = re.search(r"expected\s+([^\s,]+)\s+but\s+got\s+([^\s,]+)", error_message, re.I)
        if m:
            return f"Expected: {m.group(1)} | Actual: {m.group(2)}"

        return None

    def _clean_error_message(self, error_message):
        """Clean and format error message for Slack"""
        if not error_message:
            return "No error message"
        
        # SPECIAL HANDLING FOR SKIPPED TESTS - Clean file paths
        if "Skipped:" in error_message or "skipped" in error_message.lower():
            # Remove file paths and line numbers, keep only the reason
            lines = error_message.split("\n")
            clean_lines = []
            
            for line in lines:
                line = line.strip()
                # Skip file path lines
                if line.startswith('(') and '.py"' in line:
                    continue
                if "Skipped:" in line:
                    # Extract just the reason after "Skipped:"
                    reason = line.split("Skipped:")[-1].strip()
                    clean_lines.append(reason)
                elif line and not line.startswith('File "'):
                    clean_lines.append(line)
            
            if clean_lines:
                return " | ".join(clean_lines[:2])
        
        # Original error cleaning logic for non-skipped tests
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
        
    def _get_failure_links(self, failed_test):
        """Generate direct links for failed test evidence"""
        gh_pages = "https://geotravel-and-tours.github.io/geo-travel-automation"
        test_name = failed_test.get('test_name', '').lower()
        
        links = []
        
        # Get timestamp from environment
        timestamp = os.getenv("RUN_TIMESTAMP", "")
        
        # Determine test type
        is_ui_test = 'smoke' in test_name and 'api' not in test_name
        is_api_test = 'api' in test_name
        
        # UI TESTS - Only screenshot
        if is_ui_test:
            screenshot_path = failed_test.get('screenshot_path')
            if screenshot_path:
                screenshot_name = os.path.basename(screenshot_path)
                if timestamp:
                    # NEW structure: /TIMESTAMP/screenshots/
                    links.append(f"📸 <{gh_pages}/{timestamp}/screenshots/{screenshot_name}|View Screenshot>")
                else:
                    # OLD structure (fallback)
                    links.append(f"📸 <{gh_pages}/screenshots/failures/{screenshot_name}|View Screenshot>")
        
        # API TESTS - Test Logs + Response Dump
        elif is_api_test:
            evidence = failed_test.get('evidence', {})
            
            # API response
            resp_path = evidence.get('response_file')
            if resp_path and timestamp:
                resp_name = os.path.basename(resp_path)
                links.append(f"🗂 <{gh_pages}/{timestamp}/api_failed_responses/{resp_name}|View Response>")
                
            # Log file
            log_path = evidence.get('log_path')
            if log_path and timestamp:
                log_name = os.path.basename(log_path)
                links.append(f"📄 <{gh_pages}/{timestamp}/logs/{log_name}|View Log>")
            
        
        return " | ".join(links) if links else "No evidence captured"



# ====== GLOBAL INSTANCES ======
# Individual suite reporters
smoke_reporting = GeoReporter("UI SMOKE TEST")
regression_reporting = GeoReporter("UI REGRESSION TEST")
sanity_reporting = GeoReporter("UI SANITY TEST")
api_smoke_reporting = GeoReporter("API SMOKE TEST")
api_regression_reporting = GeoReporter("API REGRESSION TEST")
api_sanity_reporting = GeoReporter("API SANITY TEST")
partners_api_smoke_reporting = GeoReporter("PARTNERS API SMOKE TEST")
partners_api_regression_reporting = GeoReporter("PARTNERS API REGRESSION TEST")

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
        "api_sanity": api_sanity_reporting,
        "partners_api": partners_api_smoke_reporting,
        "partners_api_regression": partners_api_regression_reporting
    }
    return reporters.get(suite_name, smoke_reporting)

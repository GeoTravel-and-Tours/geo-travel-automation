## 🧭 `CHANGELOG.md`

# Changelog

This file documents notable updates or changes made to the automation framework.  
It helps track improvements, fixes, and added features over time.

---

## [Unreleased]
### Planned
- Add support for email notification integration
- Regression test suites for major features
- Switch from using Slack Webhook URL to using Slack Bot Token because it is more controllable and has more Pros
- Performance monitoring integration

---

## [1.4.1] - 2025-11-19
### Added
- GitHub Pages integration for direct screenshot access without zip downloads
- Direct clickable links in Slack reports for failed test evidence
- Enhanced screenshot naming with error-type prefixes (element_not_found, api_timeout, etc.)
- Public artifact deployment to gh-pages branch for browser-accessible test evidence
- Automated GitHub Pages workflow that publishes screenshots and reports after test runs

### Changed
- Improved test reporting with better environment handling and screenshot robustness
- Enhanced driver availability checks before capturing screenshots to prevent errors
- Fixed duration logging to use actual_duration instead of potentially None values
- Updated module resolution in test runner scripts for proper import handling
- More robust API test skipping logic to prevent false positives in environment checks
- GitHub workflow enhancements with consistent environment variable loading

### Fixed
- Critical method errors in screenshot capture by removing non-existent method calls
- GitHub Pages URL generation logic for proper direct linking
- Undefined variable issues in individual report generation
- Environment skip notifications with proper reason parameter passing
- Driver validation in screenshot utilities to handle None driver instances

---

## [1.4.1] - 2025-11-13
### Added
- GitHub Actions workflow (.github/workflows/qa-automation.yml) to replace CircleCI pipeline, including:
- Daily smoke tests schedule
- Weekly regression tests (commented for future use)
- Manual cleanup workflow via workflow_dispatch
- Artifact uploads for test screenshots
- Dependency installation and cleanup steps
- Environment variable support in scripts for GitHub Actions (GITHUB_REF_NAME, GITHUB_SHA) to ensure CI/CD metadata collection works on GitHub Actions as well as CircleCI

### Changed
- Updated get_current_branch() to check GITHUB_REF_NAME in addition to CircleCI variables
- Updated get_commit_hash() to check GITHUB_SHA in addition to CircleCI variables
- Updated _get_artifacts_link() to generate artifact links in GitHub Actions if CircleCI variables are not present
- Ensures CI/CD scripts are fully compatible with GitHub Actions while maintaining CircleCI fallback

### Fixed
- N/A (migration-focused update)

---

## [1.4.0] - 2025-11-04
### Added
- Centralized failure capture via pytest_runtest_makereport hook that saves screenshots and HTML error captures for failed tests.
- Attachment of failure artifacts (screenshots, HTML error files, latest log) into the pytest-html report using pytest-html extras.
- ValidationUtils implemented to provide safe element finding and visibility checks with proper wait handling.
- Backwards-compatible wrapper in CleanupManager to satisfy older callers (e.g., _cleanup_directory) and robust deletion helpers to handle read-only files and recursive deletion.
- TestBase improvements: reliable teardown reporting and screenshot-on-failure integration with ScreenshotUtils.
- API test scaffolding and fixtures for AuthAPI (session-scoped client, auth fixtures).
- Smoke reporting integration updated to accept screenshot and HTML artifact paths for unified reporting.
- More API tests

### Changed
- Resolved circular import between logger and cleanup modules by using lazy imports and removing module-level side effects.
- pytest-html integration updated to attach images/html previews and a downloadable latest log file into the generated HTML report.
- Reporting flow made defensive to prevent reporting hooks from crashing test runs.
- Standardized artifact locations under reports/ (screenshots, logs) for easier collection and CI uploads.

### Fixed
- Fixed TypeError caused by passing unsupported timeout parameter to Selenium's find_element by using explicit wait utilities.
- Fixed multiple teardown/reporting race conditions that could prevent screenshots or logs from being captured.
- Fixed cleanup script to support dry-run, treat directories as cleanup targets, and handle permission issues more robustly.
- Fixed missing skip reason handling so skipped tests include reasons in reports and notifications.

---

## [1.3.0] - 2025-10-28
### Added
- **Enhanced Slack Reporting** with modern formatting and demarcation lines
- **Dynamic test suite reporting** supporting both unified (API+UI) and individual suite runs
- **Comprehensive metadata collection** including Branch, Build ID, Browser, and Environment
- **Automated git branch detection** for accurate branch information in reports
- **Test failure categorization** with specific types (Functional, Wait Condition, API Timeout, etc.)
- **Fix suggestions** for common test failure scenarios
- **Environment unavailable handling** with proper Slack notifications and test skipping
- **Status emojis and motivational messages** for test results
- **Human-readable duration formatting** (Xm Ys) in reports

### Changed
- **Complete Slack message redesign** with emojis, sections, and clear demarcation
- **Improved environment check logic** to prevent false test failures
- **Enhanced test name formatting** for better readability in reports
- **Updated pytest-html integration** to use modern `report.extras` API
- **Restructured environment configuration** with better organization and documentation

### Fixed
- **Environment down scenarios** now properly skip tests without marking as failed
- **TypeError in duration logging** when duration is None
- **Duplicate git metadata collection** in test execution
- **Missing branch and build ID** in Slack reports
- **Deprecation warnings** from pytest-html plugin
- **Test execution flow** when environment checks fail early

---

## [1.2.0] - 2025-10-28
### Added
- Dynamic and robust reporting mechanism for different test suites
- Comprehensive test result tracking with proper status categorization
- Skipped test handling and reporting in Slack notifications
- Real test duration tracking for accurate performance metrics
- Context-specific test descriptions in reports

### Fixed
- Skipped tests not being counted in Slack reports
- Test duration displaying as 0.00s for all tests
- Duplicate test reporting causing incorrect counts
- Missing skip reasons in test reports
- Generic "Functional test" context for all tests

---

## [1.1.0] - 2025-10-27
### Added
- API test suite implementation for AuthAPI and FlightAPI
- Comprehensive login scenario coverage (success, invalid credentials, empty fields)
- Flight search request and booked flights endpoints testing
- Enhanced logging system for better test execution traceability
- Structured test organization by suite type (smoke, api, regression, sanity)

### Changed
- Improved file organization for better test suite separation
- Enhanced error handling in API test methods
- Better environment configuration for API testing

---

## [1.0.1] - 2025-10-26
### Added
- Utility classes for common test operations
- Page Object Model implementations for Homepage, Flight booking, and Package booking
- Test report generation with detailed failure analysis
- Screenshot capture utility for UI test failures
- Notification manager for test execution alerts
- Initial test file structure for major user flows

### Changed
- Partial implementation of Flight booking and Package booking flows
- Improved test data management
- Enhanced test fixture organization

---

## [1.0.0] - 2025-10-16
### Added
- Initial framework structure with Page Object Model design pattern
- Cross-browser driver factory supporting Chrome, Firefox, and Edge
- Smoke test suites for Flights and Packages functionality
- Slack notification integration for test execution alerts
- Automated screenshot and HTML capture on test failures
- Comprehensive HTML and JSON test reporting
- Environment configuration management via .env and YAML files
- CircleCI pipeline for scheduled and on-demand test execution
- Logging system with compression support
- Test configuration via pytest.ini

### Changed
- N/A (Initial release)

### Fixed
- N/A (Initial release)
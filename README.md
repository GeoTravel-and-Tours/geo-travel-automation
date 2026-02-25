## 🧩 `README.md`


# Geo-Automation Framework

A structured and maintainable automation testing framework designed for ***Geo Travel*** Web App test execution. This setup provides flexibility for integration with different tools, environments, and pipelines.

---

## 🚀 Purpose

The Geo-Automation Framework was built to:
- Automate end-to-end testing for the Geo Travel web application.
- Ensure high-quality releases through robust test coverage.
- Provide seamless integration with CI/CD pipelines for continuous testing.
- Deliver detailed and actionable test reports for stakeholders.

---

## 🏆 Key Achievements

- **100% Test Coverage**: Comprehensive test suites for core functionalities.
- **Cross-Browser Support**: Automated tests for Chrome, Firefox, and Edge.
- **Slack Integration**: Real-time notifications for test execution results.
- **Robust Reporting**: HTML and JSON reports with detailed logs and screenshots.
- **CI/CD Integration**: Fully automated pipelines for scheduled and on-demand test execution.

---

## 🔧 Technical Highlights

- **Design Pattern**: Page Object Model (POM) for maintainable and scalable test scripts.
- **Frameworks**: Built on `pytest` for test execution and `Selenium` for browser automation.
- **Environment Management**: Configurable via `.env` and YAML files.
- **Error Handling**: Automated screenshot and HTML capture on test failures.
- **Scalability**: Modular structure to support additional test suites and integrations.

---

## 📂 Structure

| Directory       | Description                                      |
|-----------------|--------------------------------------------------|
| **src/**        | Main source folder containing framework components |
| **core/**       | Base classes, driver setup, and initialization logic |
| **pages/**      | Page objects or endpoint definitions             |
| **tests/**      | Organized test suites (e.g., smoke, regression)  |
| **utils/**      | Reusable utilities such as logging, waits, and reporting |
| **configs/**    | Environment files and global configuration settings |
| **scripts/**    | CLI tools or scheduled test runners              |

---

## 🛠️ Setup

1. Clone the repository:
   ```sh
   git clone <repository-url>
   ```

2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Configure environment variables or `.env` file as required.

4. Update any local or environment-specific settings under `configs/`.

---

## 🧪 Running Tests

Run all tests:
```sh
pytest
```

Run specific suites:
```sh
python scripts/run_scheduled_tests.py --suite smoke
python scripts/run_scheduled_tests.py --suite api
python scripts/run_scheduled_tests.py --suite partners_api
python scripts/run_scheduled_tests.py --suite api smoke partners_api
```

Reports and logs are saved in the `reports/` and `logs/` directories.

---

## 🔄 CI/CD Integration

The framework integrates seamlessly with CircleCI for:
- **Scheduled Tests**: Automated nightly runs to ensure stability.
- **On-Demand Tests**: Trigger tests for specific branches or commits.
- **Artifacts**: Uploads reports, logs, and screenshots for easy access.

---

## 🤝 Contribution Guide

We welcome contributions to improve the framework! Follow these steps:

1. Fork the repository.
2. Create a new branch:
   ```sh
   git checkout -b feature/your-feature-name
   ```
3. Make your changes and commit them:
   ```sh
   git commit -m "Add your message here"
   ```
4. Push to your branch:
   ```sh
   git push origin feature/your-feature-name
   ```
5. Open a pull request.

---

## 📈 Scalability

The framework is designed to scale with your project:
- Add new test suites under the `tests/` directory.
- Extend utilities in the `utils/` folder for reusable components.
- Integrate with additional tools like Appium for mobile testing.

---

## 📊 Sample Reports

### HTML Report
![HTML Report Screenshot](docs/screenshots/sample_html_report.png)

### Slack Notifications

#### Server/App Not Accessible
![Server Not Accessible](docs/screenshots/slack_notifs/slack_server_not_accessible.png)

#### Failure
![Failure Notification](docs/screenshots/slack_notifs/slack_failure_notification.png)

#### Total Pass
![Total Pass Notification](docs/screenshots/slack_notifs/slack_total_pass_notification.png)

---

>  ‎
> ⚠️ **PROPRIETARY CODE NOTICE**
>
> This repository contains internal QA automation tooling for Geo Travel.
> It is publicly visible **only for GitHub Pages usage**.
>
> **Reuse, copying, or redistribution is strictly prohibited.**
>  ‎
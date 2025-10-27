## 🧩 `README.md`


# Automation Testing Framework

A structured and maintainable automation testing framework designed for ***Geo Travel*** Web App test execution.  
This setup provides flexibility for integration with different tools, environments, and pipelines.

---

## Overview

The framework supports:
- Organized and reusable test suites  
- Scalable structure for multiple environments  
- Centralized reporting and logging  
- Integration with schedulers or CI/CD systems

---

## Structure

| Directory | Description |
|------------|-------------|
| **src/** | Main source folder containing framework components |
| **core/** | Base classes, driver setup, and initialization logic |
| **pages/** | Page objects or endpoint definitions |
| **tests/** | Organized test suites (e.g., smoke, regression) |
| **utils/** | Reusable utilities such as logging, waits, and reporting |
| **configs/** | Environment files and global configuration settings |
| **scripts/** | CLI tools or scheduled test runners |

---

## Setup

1. Clone the repository.  
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

3. Configure environment variables or `.env` file as required.
4. Update any local or environment-specific settings under `configs/`.

---

## Running Tests

Run all tests:

```sh
pytest
```

Run specific suites:

```sh
python scripts/run_tests.py --suite smoke
python scripts/run_tests.py --suite regression
```

Reports and logs are saved in the `reports/`, `logs\` directory.

---

## Maintenance

* Keep dependencies up to date
* Periodically clear old reports and logs
* Extend existing modules rather than duplicating functionality
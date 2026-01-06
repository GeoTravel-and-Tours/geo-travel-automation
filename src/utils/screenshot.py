# src/utils/screenshot.py

import os
import base64
import logging
from datetime import datetime, timedelta
from src.utils.html_templates import get_success_capture_template
from pathlib import Path
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from src.utils.reporting import ReportUtils
from src.utils.cleanup import CleanupManager


class ScreenshotUtils:
    """
    Screenshot and error capture utility
    Enhanced with HTML error reporting and better organization
    """

    def __init__(
        self,
        driver: WebDriver,
        screenshot_dir="reports/screenshots",
        github_pages_base=None,
        logs_dir="logs",
        logger=None,
    ):
        self.driver = driver
        self.screenshot_dir = Path("reports/screenshots")
        self.github_pages_base = github_pages_base or self._get_github_pages_url()
        self.logs_dir = Path(logs_dir)
        self.logger = logger or self._setup_default_logger()
        self._setup_directories()
        
        self.reporting = ReportUtils()

    def _setup_default_logger(self):
        """Setup a default logger if none provided"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _setup_directories(self):
        """Create directory structure"""
        try:
            # Create main directories
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)
            self.logs_dir.mkdir(parents=True, exist_ok=True)

            # Screenshot subdirectories
            screenshot_subdirs = [
                "failures",
                "success",
                "steps",
                "elements",
                "fullpage",
            ]
            for subdir in screenshot_subdirs:
                (self.screenshot_dir / subdir).mkdir(exist_ok=True)

            # Logs subdirectories
            logs_subdirs = ["error_captures", "page_captures", "html_reports"]
            for subdir in logs_subdirs:
                (self.logs_dir / subdir).mkdir(exist_ok=True)

            self.logger.debug(
                f"Directories setup: {self.screenshot_dir}, {self.logs_dir}"
            )
        except Exception as e:
            self.logger.error(f"Failed to create directories: {e}")
            raise

    def _get_github_pages_url(self):
        """Generate GitHub Pages URL based on repo"""
        repo = os.getenv('GITHUB_REPOSITORY', 'GeoTravel-and-Tours/geo-travel-automation')
        return f"https://{repo.split('/')[0]}.github.io/{repo.split('/')[1]}"
    
    def _generate_timestamp(self):
        """Generate consistent timestamp"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _clean_filename(self, name):
        """Clean filename to be filesystem-safe"""
        return "".join(c for c in name if c.isalnum() or c in ("-", "_")).strip()

    def _generate_filename(
        self, prefix, subfolder=None, browser_info=None, extension="png"
    ):
        """Generate consistent filename with timestamp"""
        timestamp = self._generate_timestamp()
        browser_suffix = f"_{browser_info}" if browser_info else ""
        filename = f"{prefix}{browser_suffix}_{timestamp}.{extension}"

        if subfolder:
            return self.screenshot_dir / subfolder / filename
        return self.screenshot_dir / filename

    def _ensure_extension(self, filename, extension):
        """Ensure filename has correct extension"""
        if filename and not filename.lower().endswith(f".{extension}"):
            return f"{filename}.{extension}"
        return filename
    
    def capture_validation_failure(
        self, test_name, validation_results, error_message="", browser_info=None
    ):
        """
        Specialized capture for validation failures
        """
        additional_info = {
            "Confidence Score": f"{validation_results.get('confidence_score', 0):.1f}%",
            "Found Keywords": ", ".join(validation_results.get("found_keywords", [])),
            "Missing Keywords": ", ".join(
                validation_results.get("missing_keywords", [])
            ),
            "Total Checks": validation_results.get("total_checks", "N/A"),
            "Passed Checks": validation_results.get("passed_checks", "N/A"),
        }

        return self.capture_screenshot_on_failure(
            test_name, error_message, additional_info, browser_info
        )

    def capture_page_load_failure(self, test_name, error_message="", browser_info=None):
        """Specialized capture for page load failures"""
        return self.capture_screenshot_on_failure(
            test_name, error_message, None, browser_info
        )

    def capture_screenshot(self, filename=None, subfolder=None, browser_info=None, full_page=False):
        """
        Capture screenshot (supports full-page by default)
        """
        try:
            print(f"🔍 DEBUG: capture_screenshot called with filename: {filename}")
            
            self.logger.debug("Starting screenshot capture...")

            # Handle filename generation
            if filename:
                filename = self._ensure_extension(filename, "png")
                if subfolder:
                    filepath = self.screenshot_dir / subfolder / filename
                else:
                    filepath = self.screenshot_dir / filename
            else:
                filepath = self._generate_filename(
                    "screenshot", subfolder, browser_info
                )

            print(f"🔍 DEBUG: Saving to: {filepath}")
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Full-page logic
            if full_page:
                original_size = self.driver.get_window_size()
                total_height = self.driver.execute_script("return document.body.scrollHeight")
                total_width = self.driver.execute_script("return document.body.scrollWidth")
                self.driver.set_window_size(total_width, total_height)
                self.driver.save_screenshot(str(filepath))
                self.driver.set_window_size(original_size["width"], original_size["height"])
            else:
                # Normal viewport screenshot
                print(f"🔍 DEBUG: Taking normal screenshot...")
                self.driver.save_screenshot(str(filepath))
                print(f"🔍 DEBUG: Screenshot taken successfully")

            self.logger.info(f"Screenshot captured: {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"Failed to capture screenshot: {e}")
            import traceback
            print(f"🔍 DEBUG: Screenshot error: {traceback.format_exc()}")
            return None

    def capture_screenshot_on_failure(
        self, test_name, error_message="", additional_info=None, browser_info=None
    ):
        """
        Complete failure capture: screenshot + HTML error report
        Returns paths to both files with GitHub Pages URLs
        """
        try:
            # DEBUG: Check driver status
            print(f"🔍 DEBUG: Starting screenshot capture for {test_name}")
            print(f"🔍 DEBUG: Driver exists: {hasattr(self, 'driver')}")
            
            if not hasattr(self, 'driver') or not self.driver:
                self.logger.warning("No driver available for screenshot capture")
                return {"screenshot": None, "html": None}

            # Check if driver has current_url method (is a valid WebDriver instance)
            if not hasattr(self.driver, 'current_url'):
                self.logger.warning("Driver object is not a valid WebDriver instance")
                return {"screenshot": None, "html": None}
            
            # DEBUG: Check if we can interact with driver
            try:
                current_url = self.driver.current_url
                print(f"🔍 DEBUG: Current URL: {current_url}")
            except Exception as e:
                print(f"🔍 DEBUG: Cannot get current URL: {e}")
                return {"screenshot": None, "html": None}
            
            timestamp = self._generate_timestamp()
            clean_test_name = test_name.replace("::", "_").replace("/", "_").replace(":", "_")
            clean_test_name = self._clean_filename(clean_test_name)

            # 1. Capture screenshot in failures folder
            # Extract error type for better naming
            error_type = "error"
            if additional_info and 'category' in additional_info:
                error_type = additional_info['category'].lower().replace(' ', '_')
            elif error_message:
                # Extract first word of error
                error_type = error_message.split(':')[0].lower().replace(' ', '_')[:15]

            test_parts = test_name.split("::")
            if len(test_parts) > 2:
                method_name = test_parts[-1]
                class_name = test_parts[-2].replace("Test", "")
                readable_name = f"{class_name}_{method_name}"
            else:
                readable_name = clean_test_name
                
            safe_name = readable_name.replace("::", "_").replace("/", "_").replace(":", "_")[:50]
            screenshot_filename = f"{safe_name}_{timestamp}"
            print(f"🔍 DEBUG: Attempting screenshot: {screenshot_filename}")
            
            screenshot_path = self.capture_screenshot(
                screenshot_filename, "failures", browser_info
            )

            print(f"🔍 DEBUG: Screenshot result: {screenshot_path}")

            # 3. Generate GitHub Pages URLs for direct access
            result = {
                "screenshot": screenshot_path,
                "timestamp": timestamp,
            }
            
            # Generate public URLs for GitHub Pages
            if screenshot_path:
                screenshot_filename = Path(screenshot_path).name
                result["public_screenshot_url"] = f"screenshots/failures/{screenshot_filename}"
                print(f"🔍 DEBUG: GitHub Pages URL: {result['public_screenshot_url']}")

            self.logger.error(
                f"📊 Failure captured - Screenshot: {screenshot_path}"
            )

            return result

        except Exception as e:
            self.logger.error(f"Failed to capture complete failure: {e}")
            import traceback
            print(f"🔍 DEBUG: Full error: {traceback.format_exc()}")
            return {"screenshot": None, "html": None, "timestamp": None}

    def capture_screenshot_on_success(self, test_name, browser_info=None):
        """Capture success evidence with enhanced HTML report"""
        try:
            timestamp = self._generate_timestamp()
            clean_test_name = self._clean_filename(test_name)

            # Capture screenshot
            screenshot_filename = f"SUCCESS_{clean_test_name}_{timestamp}"
            screenshot_path = self.capture_screenshot(
                screenshot_filename, "success", browser_info
            )

            # Generate enhanced HTML report
            html_filename = f"SUCCESS_{clean_test_name}_{timestamp}.html"
            html_path = self.logs_dir / "page_captures" / html_filename

            html_content = get_success_capture_template(
                test_name, 
                str(screenshot_path) if screenshot_path else None, 
                browser_info
            )

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            self.logger.info(f"Enhanced success captured: {screenshot_path}")
            return screenshot_path

        except Exception as e:
            self.logger.error(f"Failed to capture success: {e}")
            return None


    def capture_element_screenshot(
        self, element: WebElement, filename=None, browser_info=None
    ):
        """Capture screenshot of a specific element"""
        try:
            if not element.is_displayed():
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", element
                )

            original_style = element.get_attribute("style")
            self.driver.execute_script(
                "arguments[0].style.border='3px solid red'; arguments[0].style.backgroundColor='yellow';",
                element,
            )

            if filename:
                filename = self._ensure_extension(filename, "png")
                filepath = self.screenshot_dir / "elements" / filename
            else:
                filepath = self._generate_filename("element", "elements", browser_info)

            filepath.parent.mkdir(parents=True, exist_ok=True)
            element.screenshot(str(filepath))

            self.driver.execute_script(
                "arguments[0].setAttribute('style', arguments[1]);",
                element,
                original_style,
            )

            self.logger.info(f"Element screenshot captured: {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.error(f"Failed to capture element screenshot: {e}")
            return self.capture_screenshot(
                f"element_fallback", "elements", browser_info
            )

    def capture_step_screenshot(self, step_description, browser_info=None):
        """
        Capture screenshot for test steps with improved filename handling
        """
        clean_description = (
            "".join(c for c in step_description if c.isalnum() or c in (" ", "-", "_"))
            .strip()
            .replace(" ", "_")[:40]
        )

        filename = f"STEP_{clean_description}"
        screenshot_path = self.capture_screenshot(filename, "steps", browser_info)

        if screenshot_path:
            self.logger.info(
                f"Step screenshot: {step_description} -> {screenshot_path}"
            )

        return screenshot_path

    def capture_screenshot_as_base64(self):
        """Capture screenshot as base64 string"""
        try:
            screenshot_bytes = self.driver.get_screenshot_as_png()
            base64_screenshot = base64.b64encode(screenshot_bytes).decode("utf-8")
            self.logger.debug("Screenshot captured as base64")
            return base64_screenshot
        except Exception as e:
            self.logger.error(f"Failed to capture base64 screenshot: {e}")
            return None
    
    def capture_cross_browser_screenshot(self, name, browser_name):
        """
        Capture screenshot with browser name in filename for cross-browser tests
        """
        clean_name = "".join(c for c in name if c.isalnum() or c in ("-", "_"))
        filename = f"{clean_name}_{browser_name}"

        return self.capture_screenshot(filename, "cross_browser", browser_name)


    def cleanup_old_screenshots(self, days_old=30, dry_run=False):
        """Use centralized cleanup for screenshots"""
        manager = CleanupManager(retention_days=days_old)
        deleted_count = manager._cleanup_directory(
            self.screenshot_dir,
            ["*.png", "*.jpg", "*.jpeg"],
            dry_run=dry_run,
            recursive=True
        )
        
        if not dry_run:
            self.logger.info(f"Screenshot cleanup: {deleted_count} files deleted")
        
        return deleted_count, 0
# src/core/base_page.py

from selenium.webdriver.remote.webdriver import WebDriver
from src.utils.element_actions import ElementActions
from src.utils.javascript import JavaScriptUtils
from src.utils.logger import GeoLogger
from src.utils.navigation import NavigationUtils
from src.utils.validation import ValidationUtils
from src.utils.wait_strategy import WaitStrategy
from src.utils.reporting import ReportUtils
from src.utils.page_info import PageInfoUtils
from src.utils.screenshot import ScreenshotUtils
from src.utils.cleanup import CleanupManager
from configs.environment import EnvironmentConfig
import time


class BasePage:
    """Base page with essential utilities"""

    def __init__(self, driver: WebDriver, timeout=10):
        self.driver = driver
        self.timeout = timeout
        self.browser = EnvironmentConfig.BROWSER

        # Core utilities only
        self.element = ElementActions(driver, timeout)
        self.javascript = JavaScriptUtils(driver)
        self.logger = GeoLogger(self.__class__.__name__)
        self.navigator = NavigationUtils(driver)
        self.pageinfo = PageInfoUtils(driver)
        self.reporting = ReportUtils(report_dir="./reports")
        self.screenshot = ScreenshotUtils(driver)
        self.validator = ValidationUtils(driver)
        self.waiter = WaitStrategy(driver, timeout)
        self.cleanup = CleanupManager(retention_days=30)

        # Environment
        self.base_url = EnvironmentConfig.get_base_url()

    # Simplified navigation methods
    def open(self, path=""):
        """Navigate to page URL"""
        url = f"{self.base_url}/{path.lstrip('/')}"
        self.driver.get(url)
        self.logger.info(f"Navigated to: {url}")

    @property
    def title(self):
        """Get page title"""
        return self.driver.title

    def is_browser(self, *browsers):
        """Check current browser"""
        return self.browser in browsers

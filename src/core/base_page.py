"""Superclass for every Selenium UI page object in the framework.

``BasePage`` is instantiated (via ``super().__init__(driver)``) by
every page-object class under ``src/pages/ui/`` and wires up the
shared helper objects those subclasses use for interacting with the
page: ``self.element`` (find/click/type helpers), ``self.javascript``
(JS execution helpers), ``self.logger`` (per-class logger),
``self.navigator`` (navigation helpers), ``self.pageinfo`` (page
metadata helpers), ``self.reporting`` (test report writer),
``self.screenshot`` (failure screenshot capture), ``self.validator``
(assertion/validation helpers), ``self.waiter`` (explicit-wait
helpers), and ``self.cleanup`` (old-artifact cleanup). Subclasses
typically only need to define locators and page-specific interaction
methods; cross-cutting concerns (waiting, logging, screenshots, etc.)
are expected to go through these shared helpers rather than being
reimplemented per page.
"""

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
    """Base class for Page Object Model pages, wiring up shared utilities.

    Holds the live ``WebDriver`` (``self.driver``), the default wait
    timeout (``self.timeout``), the configured browser name
    (``self.browser``), the resolved app base URL (``self.base_url``),
    and one instance of each shared utility helper (element actions,
    JS execution, logging, navigation, page info, reporting,
    screenshots, validation, waiting, cleanup - see the module
    docstring above for what each one does).

    Subclasses call ``super().__init__(driver)`` in their own
    ``__init__`` and then rely on ``self.element``, ``self.waiter``,
    ``self.logger``, etc. instead of calling Selenium directly, so
    behavior like logging and explicit waits stays consistent across
    all page objects.

    ``self._last_interacted_element`` is general-purpose storage some
    subclasses use to stash the last WebElement they touched, e.g. for
    screenshot/debugging context when a later step fails.
    """

    def __init__(self, driver: WebDriver, timeout=10):
        """Wire up the driver reference and all shared page-object utilities.

        Args:
            driver (WebDriver): Active Selenium WebDriver instance
                shared by this page object and all the utility helpers
                created here.
            timeout (int): Default explicit-wait timeout in seconds,
                passed through to ``ElementActions`` and
                ``WaitStrategy``. Defaults to 10.
        """
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

        # Storage for last interacted element
        self._last_interacted_element = None  # general storage for last element

    # Simplified navigation methods
    def open(self, path=""):
        """Navigate the driver to a path relative to the app's base URL.

        Args:
            path (str): Path to append to ``self.base_url`` (leading
                slashes are stripped before joining). Defaults to "",
                i.e. the base URL itself.
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        self.driver.get(url)
        self.logger.info(f"Navigated to: {url}")

    @property
    def title(self):
        """str: The current page's ``<title>`` text, from the live driver."""
        return self.driver.title

    def is_browser(self, *browsers):
        """Check whether the configured browser is one of the given names.

        Args:
            *browsers (str): One or more browser names to check against
                (e.g. "chrome", "firefox").

        Returns:
            bool: True if ``self.browser`` matches any of ``browsers``.
        """
        return self.browser in browsers

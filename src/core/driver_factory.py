"""Creates and tracks Selenium WebDriver instances for the test suite.

``DriverFactory`` reads the configured browser (chrome/firefox/edge)
and browser options from ``EnvironmentConfig``, downloads/launches the
matching driver binary via ``webdriver-manager``, and keeps a
reference to every driver it creates so they can all be torn down
together. Callers (typically pytest fixtures in ``conftest.py``) use
the pre-built module-level singleton ``driver_factory`` rather than
instantiating ``DriverFactory`` themselves.
"""

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from configs.environment import EnvironmentConfig
from src.utils.logger import GeoLogger


class DriverFactory:
    """Builds Selenium WebDriver instances and manages their lifecycle.

    Holds a ``GeoLogger`` (``self.logger``) and a list of every driver
    this factory instance has created (``self._drivers``), so
    ``quit_all`` can clean them all up - e.g. at the end of a test
    session or if driver creation itself fails partway through.
    """

    def __init__(self):
        """Initialize the logger and the list of tracked driver instances."""
        self.logger = GeoLogger(__name__)
        self._drivers = []

    def create_driver(self):
        """Create and configure a WebDriver for the configured browser.

        Reads the target browser and browser options from
        ``EnvironmentConfig``, installs the matching driver binary via
        ``webdriver-manager``, and applies common post-creation
        settings (implicit wait timeout, and maximizing the window
        unless running headless). The new driver is appended to
        ``self._drivers`` for later cleanup via ``quit_all``.

        Returns:
            WebDriver: The newly created, ready-to-use driver instance.

        Raises:
            ValueError: If ``EnvironmentConfig.BROWSER`` is not one of
                "chrome", "firefox", or "edge".
            Exception: Re-raised if driver creation fails for any other
                reason; any drivers already created by this factory are
                quit first via ``quit_all`` to avoid leaking browser
                processes.
        """
        try:

            browser = EnvironmentConfig.BROWSER
            options = EnvironmentConfig.get_browser_options()

            self.logger.info(f"Creating {browser} driver...")

            try:
                # Use webdriver-manager for automatic driver management
                if browser == "chrome":
                    service = webdriver.chrome.service.Service(
                        ChromeDriverManager().install()
                    )
                    driver = webdriver.Chrome(service=service, options=options)
                elif browser == "firefox":
                    service = webdriver.firefox.service.Service(
                        GeckoDriverManager().install()
                    )
                    driver = webdriver.Firefox(service=service, options=options)
                elif browser == "edge":
                    service = webdriver.edge.service.Service(
                        EdgeChromiumDriverManager().install()
                    )
                    driver = webdriver.Edge(service=service, options=options)
                else:
                    raise ValueError(f"Unsupported browser: {browser}")

                # Common settings
                driver.implicitly_wait(EnvironmentConfig.TIMEOUT)
                if not EnvironmentConfig.HEADLESS:
                    driver.maximize_window()

                self._drivers.append(driver)
                self.logger.info(f"{browser} driver created successfully")
                return driver

            except Exception as e:
                self.logger.error(f"Failed to create {browser} driver: {e}")
                raise
        except Exception as e:
            self.quit_all()  # Cleanup on failure
            self.logger.error(f"Error in driver creation: {e}")
            raise

    def quit_all(self):
        """Quit every driver this factory has created.

        Iterates over a shallow copy of ``self._drivers`` (since each
        successful quit mutates the list) so a failure quitting one
        driver doesn't stop the others from being cleaned up. Errors
        are logged rather than raised.
        """
        for driver in self._drivers[:]:
            try:
                if driver:
                    driver.quit()
                    self._drivers.remove(driver)
            except Exception as e:
                self.logger.error(f"Error quitting driver: {e}")


# Global instance shared across the framework, so fixtures/tests don't
# need to construct their own DriverFactory.
driver_factory = DriverFactory()

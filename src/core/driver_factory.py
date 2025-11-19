# src/core/driver_factory.py

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from configs.environment import EnvironmentConfig
from src.utils.logger import GeoLogger


class DriverFactory:
    """Simplified driver factory"""

    def __init__(self):
        self.logger = GeoLogger(__name__)
        self._drivers = []

    def create_driver(self):
        """Create driver with current environment settings"""
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
        """Quit all drivers"""
        for driver in self._drivers[:]:
            try:
                if driver:
                    driver.quit()
                    self._drivers.remove(driver)
            except Exception as e:
                self.logger.error(f"Error quitting driver: {e}")


# Global instance
driver_factory = DriverFactory()

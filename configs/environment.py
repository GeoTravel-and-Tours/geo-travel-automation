# configs/environment.py

import os
import requests
import time
from dotenv import load_dotenv
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from urllib3.util.retry import Retry
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from requests.adapters import HTTPAdapter
from src.utils.logger import GeoLogger

load_dotenv()


class EnvironmentConfig:
    """Configuration for cross-browser testing"""

    # Environment URLs
    ENVIRONMENTS = {
        "dev": {"base_url": "https://retail.dev.gowithgeo.com"},
        "qa": {"base_url": "https://retail.qa.gowithgeo.com"},
        "staging": {"base_url": "https://retail.stg.gowithgeo.com"},
        'production': {'base_url': 'https://www.gowithgeo.com'}
    }

    # Browser configurations
    BROWSERS = {
        "chrome": {
            "driver_class": webdriver.Chrome,
            "options_class": webdriver.ChromeOptions,
            "manager": ChromeDriverManager,
        },
        "firefox": {
            "driver_class": webdriver.Firefox,
            "options_class": webdriver.FirefoxOptions,
            "manager": GeckoDriverManager,
        },
        "edge": {
            "driver_class": webdriver.Edge,
            "options_class": webdriver.EdgeOptions,
            "manager": EdgeChromiumDriverManager,
        },
    }

    TEST_ENV = os.getenv("TEST_ENV", "qa").lower()
    BROWSER = os.getenv("BROWSER", "chrome").lower()
    HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
    WINDOW_SIZE = os.getenv("WINDOW_SIZE", "1920x1080")
    TIMEOUT = int(os.getenv("TIMEOUT", "10"))

    @classmethod
    def get_base_url(cls, environment=None):
        env = environment or cls.TEST_ENV
        return cls.ENVIRONMENTS.get(env, {}).get("base_url")

    @classmethod
    def get_browser_config(cls, browser=None):
        browser = browser or cls.BROWSER
        return cls.BROWSERS.get(browser, cls.BROWSERS["chrome"])
    
    @classmethod
    def get_browser_capabilities(cls, browser=None):
        browser = browser or cls.BROWSER
        capabilities = {}

        if browser == "edge":
            capabilities = {
                "acceptInsecureCerts": True,
                "unhandledPromptBehavior": "accept",
                "pageLoadStrategy": "normal"
            }

        return capabilities

    @classmethod
    def is_environment_accessible(cls, environment=None, max_attempts=3, timeout=10):
        """Check if the environment frontend is accessible with retry logic"""
        logger = GeoLogger("EnvironmentCheck")
        
        env = environment or cls.TEST_ENV
        base_url = cls.get_base_url(env)
        
        if not base_url:
            logger.error(f"No base URL found for environment: {env}")
            return False
            
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Environment check attempt {attempt}/{max_attempts} for {base_url}")
                response = session.get(base_url, timeout=timeout, verify=False)
                
                # Consider any non-5xx status as accessible (even 404/403 means the site is responding)
                if response.status_code < 500:
                    logger.success(f"Environment {env} is accessible (Status: {response.status_code})")
                    return True
                else:
                    logger.warning(f"Environment responded with status {response.status_code}")
                    
            except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
                logger.error(f"Attempt {attempt} failed: {e}")
            
            # Wait before retry (similar to your homepage load logic)
            if attempt < max_attempts:
                wait_time = 5 * attempt
                logger.info(f"Waiting {wait_time}s before next attempt...")
                time.sleep(wait_time)
        
        logger.error(f"Environment {env} is not accessible after {max_attempts} attempts")
        return False
    
    @classmethod
    def wait_for_environment(cls, environment=None, timeout=60, check_interval=5):
        """Wait for environment to become available"""
        logger = GeoLogger("EnvironmentCheck")
        
        env = environment or cls.TEST_ENV
        start_time = time.time()
        attempt = 1
        
        while time.time() - start_time < timeout:
            if cls.is_environment_accessible(environment, max_attempts=1):
                return True
            
            wait_time = 5 * attempt
            logger.info(f"Waiting for {env} environment... (attempt {attempt}, waiting {wait_time}s)")
            time.sleep(wait_time)
            attempt += 1
        
        logger.error(f"Environment {env} did not become accessible within {timeout} seconds")
        return False

    @classmethod
    def get_browser_options(cls, browser=None):
        browser_config = cls.get_browser_config(browser)
        options = browser_config["options_class"]()

        # Common options for all browsers
        if cls.HEADLESS:
            if hasattr(options, "add_argument"):  # Chrome/Edge
                options.add_argument("--headless")
            elif hasattr(options, "headless"):  # Firefox
                options.headless = True

        if cls.WINDOW_SIZE and hasattr(options, "add_argument"):
            options.add_argument(f"--window-size={cls.WINDOW_SIZE}")

        # Browser-specific options
        if browser == "chrome" or browser == "edge":
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            
            # EDGE-SPECIFIC FIXES:
            if browser == "edge":
                options.add_argument("--ignore-certificate-errors")
                options.add_argument("--ignore-ssl-errors")
                options.add_argument("--disable-web-security")
                options.add_argument("--allow-running-insecure-content")
                options.add_argument("--disable-features=VizDisplayCompositor")
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-plugins")
                options.add_argument("--disable-default-apps")
                options.add_argument("--disable-component-extensions-with-background-pages")
                options.add_argument("--disable-background-timer-throttling")
                options.add_argument("--disable-renderer-backgrounding")
                options.add_argument("--disable-backgrounding-occluded-windows")
                
        elif browser == "firefox":
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference("useAutomationExtension", False)
            # Firefox specific connection fixes
            options.set_preference("network.http.use-cache", False)
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)

        return options